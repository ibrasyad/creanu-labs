use chrono::{Duration, NaiveDate};
use rand_chacha::ChaCha8Rng;
use rand_core::SeedableRng;
use std::collections::HashMap;

use crate::basket::{generate_basket, PurchaseHistory};
use crate::config::FullSimulationConfig;
use crate::funnel::{get_visit_decay_multiplier, rolls_landing_page, simulate_user_journey};
use crate::models::{
    CatalogItemRecord, DailyMetric, FunnelEventRecord, SimulationOutput, SimulationSummary,
    TransactionItemRecord, TransactionRecord, UserRecord,
};
use crate::user::{generate_base_users, generate_user_record, roll_new_users_for_tier};
use crate::utils::{get_day_of_week, seed_for_date};

pub type ProgressCallback = Box<dyn Fn(usize, usize, &str)>;

/// Extract catalog flat records for export
pub fn export_catalog_records(config: &FullSimulationConfig) -> Vec<CatalogItemRecord> {
    let mut records = Vec::new();
    for (cat_name, subcats) in &config.catalog {
        for (subcat_name, subcat) in subcats {
            for (prod_name, prod) in &subcat.product {
                records.push(CatalogItemRecord {
                    category: cat_name.clone(),
                    subcategory: subcat_name.clone(),
                    product: prod_name.clone(),
                    base_price: prod.base_price,
                });
            }
        }
    }
    records
}

/// Execute the entire simulation across the date range
pub fn run_simulation(
    config: &FullSimulationConfig,
    override_start: Option<&str>,
    override_end: Option<&str>,
    override_seed: Option<u64>,
    progress_callback: Option<&ProgressCallback>,
) -> Result<SimulationOutput, String> {
    let start_str = override_start.unwrap_or(&config.date.start_date);
    let end_str = override_end.unwrap_or(&config.date.end_date);
    let base_seed = override_seed.unwrap_or(config.simulation.random_seed);

    let start_date = NaiveDate::parse_from_str(start_str, "%Y-%m-%d")
        .map_err(|e| format!("Invalid start date '{}': {}", start_str, e))?;
    let end_date = NaiveDate::parse_from_str(end_str, "%Y-%m-%d")
        .map_err(|e| format!("Invalid end date '{}': {}", end_str, e))?;

    if end_date < start_date {
        return Err("End date must be on or after start date".to_string());
    }

    let total_days = (end_date - start_date).num_days() as usize + 1;

    // 1. Initialize base users
    let mut init_rng = ChaCha8Rng::seed_from_u64(base_seed);
    let mut users: Vec<UserRecord> = generate_base_users(config, start_str, &mut init_rng);
    let mut purchase_history: PurchaseHistory = HashMap::new();

    let mut all_funnel: Vec<FunnelEventRecord> = Vec::new();
    let mut all_transactions: Vec<TransactionRecord> = Vec::new();
    let mut all_items: Vec<TransactionItemRecord> = Vec::new();
    let mut daily_metrics: Vec<DailyMetric> = Vec::new();

    let mut user_counter = users.len() + 1;
    let mut current_date = start_date;
    let mut day_index = 0;

    let mut total_revenue = 0.0;
    let mut total_items_sold: u64 = 0;
    let mut category_revenue: HashMap<String, f64> = HashMap::new();
    let mut product_units: HashMap<String, (u64, f64)> = HashMap::new();
    let mut funnel_step_counts: HashMap<String, usize> = HashMap::new();

    // 2. Iterate day by day
    while current_date <= end_date {
        let date_str = current_date.format("%Y-%m-%d").to_string();
        let day_seed = seed_for_date(base_seed, &date_str);
        let mut rng = ChaCha8Rng::seed_from_u64(day_seed);

        // A. Acquire new users for today
        let mut daily_new_users = 0;
        for (tier_name, tier_cfg) in &config.tiers {
            let new_count = roll_new_users_for_tier(tier_cfg, current_date, &mut rng);
            for _ in 0..new_count {
                let new_user = generate_user_record(tier_name, tier_cfg, user_counter, &date_str, &mut rng);
                users.push(new_user);
                user_counter += 1;
                daily_new_users += 1;
            }
        }

        // B. Simulate user visits & funnel
        let mut active_today_users = Vec::new();
        let mut session_counter = 1;
        let date_prefix = current_date.format("%Y%m%d").to_string();

        let mut day_transactions = 0;
        let mut day_revenue = 0.0;
        let mut day_items = 0u32;
        let mut day_visitors = 0usize;

        // Iterate through all current users
        for user_idx in 0..users.len() {
            let user = &users[user_idx];
            let tier_cfg = match config.tiers.get(&user.tier) {
                Some(cfg) => cfg,
                None => continue,
            };

            // Calculate recency decay
            let last_active = NaiveDate::parse_from_str(&user.last_active_date, "%Y-%m-%d")
                .unwrap_or(current_date);
            let days_elapsed = (current_date - last_active).num_days();
            let decay = get_visit_decay_multiplier(days_elapsed, &config.simulation.visit_decay);

            if rolls_landing_page(config, tier_cfg, current_date, decay, &mut rng) {
                let session_id = format!("{}-{:08}", date_prefix, session_counter);
                session_counter += 1;
                day_visitors += 1;
                active_today_users.push(user_idx);

                let (journey_events, paid, paid_dt) = simulate_user_journey(
                    config,
                    &user.tier,
                    tier_cfg,
                    &user.user_id,
                    &session_id,
                    current_date,
                    &mut rng,
                );

                for ev in &journey_events {
                    *funnel_step_counts.entry(ev.activity.clone()).or_insert(0) += 1;
                }
                all_funnel.extend(journey_events);

                // If transaction paid: generate basket
                if paid {
                    if let Some(ref paid_time_str) = paid_dt {
                        let trx_id = format!("trx-{}", session_id);
                        let basket = generate_basket(
                            config,
                            &user.tier,
                            tier_cfg,
                            &user.user_id,
                            current_date,
                            paid_time_str,
                            &trx_id,
                            &mut purchase_history,
                            &mut rng,
                        );

                        if !basket.empty_or_zero() {
                            let trx_total: f64 = basket.iter().map(|it| it.total_price).sum();
                            let items_count: u32 = basket.iter().map(|it| it.quantity).sum();

                            day_transactions += 1;
                            day_revenue += trx_total;
                            day_items += items_count;

                            for item in &basket {
                                // Track product stats
                                let entry = product_units.entry(item.product.clone()).or_insert((0, 0.0));
                                entry.0 += item.quantity as u64;
                                entry.1 += item.total_price;

                                // Track category stats
                                *category_revenue.entry(item.tier.clone()).or_insert(0.0) += item.total_price;
                            }

                            all_transactions.push(TransactionRecord {
                                session_id: session_id.clone(),
                                user_id: user.user_id.clone(),
                                trx_id,
                                date: paid_time_str.clone(),
                                tier: user.tier.clone(),
                                total_price: trx_total,
                            });

                            all_items.extend(basket);
                        }
                    }
                }
            }
        }

        // C. Update last_active_date for all active visitors
        for idx in active_today_users {
            users[idx].last_active_date = date_str.clone();
        }

        total_revenue += day_revenue;
        total_items_sold += day_items as u64;

        let day_conversion = if day_visitors > 0 {
            (day_transactions as f64) / (day_visitors as f64)
        } else {
            0.0
        };

        daily_metrics.push(DailyMetric {
            date: date_str.clone(),
            weekday: get_day_of_week(current_date),
            active_visitors: day_visitors,
            transactions: day_transactions,
            gross_revenue: day_revenue,
            items_sold: day_items,
            conversion_rate: day_conversion,
            new_users_acquired: daily_new_users,
        });

        day_index += 1;
        if let Some(cb) = progress_callback {
            cb(day_index, total_days, &date_str);
        }

        current_date = current_date + Duration::days(1);
    }

    // 3. Compile top products
    let mut top_products: Vec<(String, u64, f64)> = product_units
        .into_iter()
        .map(|(prod, (qty, rev))| (prod, qty, rev))
        .collect();
    top_products.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap_or(std::cmp::Ordering::Equal));
    top_products.truncate(10);

    let total_transactions = all_transactions.len();
    let average_order_value = if total_transactions > 0 {
        total_revenue / (total_transactions as f64)
    } else {
        0.0
    };

    let total_sessions = *funnel_step_counts.get("landing_page").unwrap_or(&0);
    let overall_conversion_rate = if total_sessions > 0 {
        (total_transactions as f64) / (total_sessions as f64)
    } else {
        0.0
    };

    let summary = SimulationSummary {
        total_users: users.len(),
        new_users: users.len().saturating_sub(config.tiers.values().map(|t| t.base_user).sum()),
        total_sessions,
        total_transactions,
        total_items_sold,
        total_revenue,
        average_order_value,
        overall_conversion_rate,
        daily_metrics,
        funnel_breakdown: funnel_step_counts,
        category_revenue,
        top_products,
    };

    Ok(SimulationOutput {
        users,
        funnel: all_funnel,
        transactions: all_transactions,
        transaction_items: all_items,
        catalog: export_catalog_records(config),
        summary,
    })
}

trait EmptyOrZero {
    fn empty_or_zero(&self) -> bool;
}

impl EmptyOrZero for Vec<TransactionItemRecord> {
    fn empty_or_zero(&self) -> bool {
        self.is_empty() || self.iter().all(|it| it.quantity == 0)
    }
}
