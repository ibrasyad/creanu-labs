use chrono::NaiveDate;
use rand::Rng;
use std::collections::HashMap;

use crate::config::{FullSimulationConfig, TierConfig};
use crate::models::UserRecord;
use crate::utils::{apply_noise, get_day_of_week, get_month_name, sample_poisson, weighted_choice};

/// Fallback demographic distributions
fn default_cities() -> HashMap<String, f64> {
    let mut map = HashMap::new();
    map.insert("Jakarta".to_string(), 0.50);
    map.insert("Surabaya".to_string(), 0.20);
    map.insert("Bandung".to_string(), 0.15);
    map.insert("Medan".to_string(), 0.10);
    map.insert("Semarang".to_string(), 0.05);
    map
}

fn default_genders() -> HashMap<String, f64> {
    let mut map = HashMap::new();
    map.insert("Female".to_string(), 0.60);
    map.insert("Male".to_string(), 0.40);
    map
}

fn default_channels() -> HashMap<String, f64> {
    let mut map = HashMap::new();
    map.insert("Organic Search".to_string(), 0.35);
    map.insert("Social Media".to_string(), 0.30);
    map.insert("Referral".to_string(), 0.20);
    map.insert("Direct".to_string(), 0.15);
    map
}

/// Generate a single user record
pub fn generate_user_record<R: Rng>(
    tier_name: &str,
    tier_cfg: &TierConfig,
    user_index: usize,
    registered_date: &str,
    rng: &mut R,
) -> UserRecord {
    let default_city = default_cities();
    let city_weights = tier_cfg.city.as_ref().unwrap_or(&default_city);
    let city = weighted_choice(city_weights, rng).unwrap_or(&"Jakarta".to_string()).clone();

    let default_gender = default_genders();
    let gender_weights = tier_cfg.gender.as_ref().unwrap_or(&default_gender);
    let gender = weighted_choice(gender_weights, rng).unwrap_or(&"Female".to_string()).clone();

    let default_channel = default_channels();
    let channel_weights = tier_cfg.acquisition_channel.as_ref().unwrap_or(&default_channel);
    let channel = weighted_choice(channel_weights, rng).unwrap_or(&"Organic Search".to_string()).clone();

    UserRecord {
        tier: tier_name.to_string(),
        user_id: format!("usr-{:06}", user_index),
        city,
        gender,
        acquisition_channel: channel,
        registered_date: registered_date.to_string(),
        last_active_date: registered_date.to_string(),
    }
}

/// Generate initial base users for simulation start
pub fn generate_base_users<R: Rng>(config: &FullSimulationConfig, start_date: &str, rng: &mut R) -> Vec<UserRecord> {
    let mut users = Vec::new();
    let mut user_counter = 1;

    for (tier_name, tier_cfg) in &config.tiers {
        for _ in 0..tier_cfg.base_user {
            users.push(generate_user_record(tier_name, tier_cfg, user_counter, start_date, rng));
            user_counter += 1;
        }
    }
    users
}

/// Roll daily new user arrivals for a tier
pub fn roll_new_users_for_tier<R: Rng>(
    tier_cfg: &TierConfig,
    date: NaiveDate,
    rng: &mut R,
) -> usize {
    let weekday = get_day_of_week(date);
    let is_weekend = weekday == "saturday" || weekday == "sunday";
    let base_chance = if is_weekend && tier_cfg.daily_new_user_chance_weekend > 0.0 {
        tier_cfg.daily_new_user_chance_weekend
    } else {
        tier_cfg.daily_new_user_chance
    };

    let retries = tier_cfg.daily_retry.max(1);
    let mut new_users = 0;

    for _ in 0..retries {
        let draw: f64 = rng.gen();
        if draw < base_chance {
            new_users += 1;
        }
    }

    new_users
}
