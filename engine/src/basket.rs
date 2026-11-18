use chrono::NaiveDate;
use rand::Rng;
use rand_distr::{Distribution, LogNormal};
use std::collections::{HashMap, HashSet};

use crate::config::{CatalogConfig, FullSimulationConfig, TierConfig};
use crate::models::TransactionItemRecord;
use crate::utils::{sample_poisson, sample_triangular, weighted_choice};

pub type PurchaseHistory = HashMap<(String, String, String), NaiveDate>; // (user_id, category, subcategory) -> date

/// Product candidate chosen from catalog
struct Candidate {
    category: String,
    subcategory: String,
    product_name: String,
    base_price: f64,
}

/// Check if item is available based on subcategory cooldown
fn is_available(
    history: &PurchaseHistory,
    user_id: &str,
    category: &str,
    subcategory: &str,
    cooldown_days: u32,
    current_date: NaiveDate,
) -> bool {
    let key = (user_id.to_string(), category.to_string(), subcategory.to_string());
    if let Some(&last_purchase) = history.get(&key) {
        let elapsed = (current_date - last_purchase).num_days();
        elapsed >= cooldown_days as i64
    } else {
        true
    }
}

/// Pick a single valid product candidate honoring cooldowns and duplicate rules
fn pick_candidate<R: Rng>(
    catalog: &CatalogConfig,
    tier_cfg: &TierConfig,
    user_id: &str,
    current_date: NaiveDate,
    history: &PurchaseHistory,
    picked_subcategories: &HashSet<String>,
    rng: &mut R,
) -> Option<Candidate> {
    let categories = &tier_cfg.category_weight;
    if categories.is_empty() {
        return None;
    }

    // Try up to 100 times matching Python _candidate()
    for _ in 0..100 {
        let category = match weighted_choice(categories, rng) {
            Some(c) => c,
            None => continue,
        };
        let subcategories = match catalog.get(category) {
            Some(subs) => subs,
            None => continue,
        };
        if subcategories.is_empty() {
            continue;
        }

        // Subcategory choice
        let subcategory_name = if let Some(sub_weights) = tier_cfg.subcategory_weight.as_ref().and_then(|w| w.get(category)) {
            weighted_choice(sub_weights, rng).cloned()
        } else {
            let names: Vec<&String> = subcategories.keys().collect();
            names.get(rng.gen_range(0..names.len())).map(|&s| s.clone())
        };

        let subcategory_name = match subcategory_name {
            Some(s) => s,
            None => continue,
        };

        // Check duplicate rule for this subcategory
        let allow_duplicates = tier_cfg
            .subcategory_allow_duplicates
            .as_ref()
            .and_then(|m| m.get(&subcategory_name))
            .copied()
            .unwrap_or(true);

        if !allow_duplicates && picked_subcategories.contains(&subcategory_name) {
            continue;
        }

        let subcat_cfg = match subcategories.get(&subcategory_name) {
            Some(cfg) => cfg,
            None => continue,
        };

        if subcat_cfg.product.is_empty() {
            continue;
        }

        // Weighted product choice within subcategory
        let product_weights: HashMap<String, f64> = subcat_cfg
            .product
            .iter()
            .map(|(name, p)| (name.clone(), p.weight))
            .collect();

        let product_name = match weighted_choice(&product_weights, rng) {
            Some(p) => p.clone(),
            None => continue,
        };

        let prod_cfg = match subcat_cfg.product.get(&product_name) {
            Some(p) => p,
            None => continue,
        };

        let effective_cooldown = prod_cfg.cooldown.unwrap_or(subcat_cfg.cooldown);

        if is_available(history, user_id, category, &subcategory_name, effective_cooldown, current_date) {
            return Some(Candidate {
                category: category.clone(),
                subcategory: subcategory_name,
                product_name,
                base_price: prod_cfg.base_price,
            });
        }
    }
    None
}

/// Generate a complete basket of items for a paid transaction
pub fn generate_basket<R: Rng>(
    config: &FullSimulationConfig,
    tier_name: &str,
    tier_cfg: &TierConfig,
    user_id: &str,
    current_date: NaiveDate,
    activity_datetime: &str,
    trx_id: &str,
    history: &mut PurchaseHistory,
    rng: &mut R,
) -> Vec<TransactionItemRecord> {
    let basket_cfg = tier_cfg.basket.as_ref().unwrap_or(&config.simulation.basket);
    let min_items = basket_cfg.min_items as f64;
    let max_items = basket_cfg.max_items as f64;
    let mode = (min_items + max_items) / 2.0;

    let target_items = sample_triangular(min_items, max_items, mode, rng).round() as usize;
    let target_items = target_items.max(1);

    let mut items = Vec::new();
    let mut picked_subcategories = HashSet::new();

    let base_lambda = tier_cfg
        .quantity_model
        .as_ref()
        .map(|q| q.base_lambda)
        .unwrap_or(config.simulation.quantity_model.base_lambda);

    let cv = config.simulation.price_variation.std_pct.max(0.0);
    let sigma = (1.0 + cv * cv).ln().sqrt();

    for _ in 0..target_items {
        let candidate = match pick_candidate(
            &config.catalog,
            tier_cfg,
            user_id,
            current_date,
            history,
            &picked_subcategories,
            rng,
        ) {
            Some(c) => c,
            None => break,
        };

        // Quantity calculation
        let bias = tier_cfg
            .quantity_bias
            .as_ref()
            .and_then(|b| b.get(&candidate.category))
            .copied()
            .unwrap_or(1.0);

        let quantity = sample_poisson(base_lambda * bias, rng).max(1);

        // Price variation
        let unit_price = if sigma > 0.0 {
            let lognormal = LogNormal::new(-0.5 * sigma * sigma, sigma).unwrap_or(LogNormal::new(0.0, 0.01).unwrap());
            let multiplier = lognormal.sample(rng);
            // Round to nearest 100 rupiah (matching Python round(..., -2))
            let raw_price = candidate.base_price * multiplier;
            ((raw_price / 100.0).round() * 100.0).max(100.0)
        } else {
            candidate.base_price
        };

        let total_price = unit_price * (quantity as f64);

        items.push(TransactionItemRecord {
            trx_id: trx_id.to_string(),
            user_id: user_id.to_string(),
            tier: tier_name.to_string(),
            date: activity_datetime.to_string(),
            product: candidate.product_name,
            quantity,
            unit_price,
            total_price,
        });

        // Update purchase history for cooldown
        let hist_key = (user_id.to_string(), candidate.category, candidate.subcategory.clone());
        history.insert(hist_key, current_date);
        picked_subcategories.insert(candidate.subcategory);
    }

    items
}
