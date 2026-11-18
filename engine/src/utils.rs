use chrono::{Datelike, NaiveDate};
use rand::Rng;
use rand_distr::{Distribution, LogNormal, Normal, Poisson};
use sha2::{Digest, Sha256};
use std::collections::HashMap;

use crate::config::NoiseConfig;

/// Generate deterministic seed for a specific date, identical to Python implementation:
/// int.from_bytes(hashlib.sha256(f"{seed}:{date_str}").digest()[:8], "big") % (2**32)
pub fn seed_for_date(base_seed: u64, date_str: &str) -> u64 {
    let payload = format!("{}:{}", base_seed, date_str);
    let mut hasher = Sha256::new();
    hasher.update(payload.as_bytes());
    let hash = hasher.finalize();
    let mut bytes = [0u8; 8];
    bytes.copy_from_slice(&hash[0..8]);
    u64::from_be_bytes(bytes) % (1u64 << 32)
}

/// Choose an item from a weighted map: key -> weight
pub fn weighted_choice<'a, R: Rng>(weights: &'a HashMap<String, f64>, rng: &mut R) -> Option<&'a String> {
    if weights.is_empty() {
        return None;
    }
    let total_weight: f64 = weights.values().filter(|&&w| w > 0.0).sum();
    if total_weight <= 0.0 {
        return weights.keys().next();
    }
    let mut draw = rng.gen_range(0.0..total_weight);
    for (key, &weight) in weights {
        if weight <= 0.0 {
            continue;
        }
        if draw < weight {
            return Some(key);
        }
        draw -= weight;
    }
    weights.keys().last()
}

/// Apply a mean-one noise multiplier matching Python apply_noise()
pub fn apply_noise<R: Rng>(base_value: f64, noise_cfg: Option<&NoiseConfig>, rng: &mut R) -> f64 {
    let cfg = match noise_cfg {
        Some(c) => c,
        None => return base_value,
    };
    let cv = (cfg.multiplier - 1.0).max(0.0);
    if cv <= 0.0 {
        return base_value;
    }
    let factor = match cfg.distribution.as_str() {
        "uniform" => rng.gen_range((1.0 - cv).max(0.0)..(1.0 + cv)),
        "normal" => {
            let normal = Normal::new(1.0, cv).unwrap_or(Normal::new(1.0, 0.01).unwrap());
            normal.sample(rng).max(0.0)
        }
        _ => {
            // lognormal default (matches python)
            let sigma = (1.0 + cv * cv).ln().sqrt();
            let mean = -0.5 * sigma * sigma;
            let lognormal = LogNormal::new(mean, sigma).unwrap_or(LogNormal::new(0.0, 0.01).unwrap());
            lognormal.sample(rng)
        }
    };
    base_value * factor
}

/// Draw a Poisson random variable
pub fn sample_poisson<R: Rng>(lambda: f64, rng: &mut R) -> u32 {
    if lambda <= 0.0 {
        return 0;
    }
    match Poisson::new(lambda) {
        Ok(poi) => poi.sample(rng) as u32,
        Err(_) => lambda.round() as u32,
    }
}

/// Draw a Triangular random variable
pub fn sample_triangular<R: Rng>(min: f64, max: f64, mode: f64, rng: &mut R) -> f64 {
    if min >= max {
        return min;
    }
    let f = (mode - min) / (max - min);
    let u: f64 = rng.gen();
    if u <= f {
        min + (u * (max - min) * (mode - min)).sqrt()
    } else {
        max - ((1.0 - u) * (max - min) * (max - mode)).sqrt()
    }
}

/// Return lowercase weekday string (e.g. "monday", "saturday")
pub fn get_day_of_week(date: NaiveDate) -> String {
    date.format("%A").to_string().to_lowercase()
}

/// Return lowercase month name (e.g. "january", "december")
pub fn get_month_name(date: NaiveDate) -> String {
    date.format("%B").to_string().to_lowercase()
}
