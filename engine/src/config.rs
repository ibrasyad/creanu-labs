use serde::{Deserialize, Serialize};
use std::collections::HashMap;

// ============================================================================
// NOISE & DISTRIBUTIONS
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NoiseConfig {
    #[serde(default = "default_noise_dist")]
    pub distribution: String,
    #[serde(default = "default_one_f64")]
    pub multiplier: f64,
}

fn default_noise_dist() -> String {
    "lognormal".to_string()
}
fn default_one_f64() -> f64 {
    1.0
}

// ============================================================================
// CATALOG CONFIG
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProductConfig {
    pub base_price: f64,
    #[serde(default = "default_one_f64")]
    pub weight: f64,
    pub cooldown: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubcategoryConfig {
    #[serde(default = "default_cooldown")]
    pub cooldown: u32,
    pub product: HashMap<String, ProductConfig>,
}

fn default_cooldown() -> u32 {
    1
}

pub type CatalogConfig = HashMap<String, HashMap<String, SubcategoryConfig>>;

// ============================================================================
// DATE CONFIG
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransactionVolumeConfig {
    #[serde(default)]
    pub monthly_rate: HashMap<String, f64>,
    #[serde(default)]
    pub monthly_rate_noise: Option<NoiseConfig>,
    #[serde(default)]
    pub weekday_base: HashMap<String, f64>,
    #[serde(default)]
    pub weekday_rate_noise: Option<NoiseConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DateConfig {
    pub start_date: String,
    pub end_date: String,
    pub transaction_volume: TransactionVolumeConfig,
}

// ============================================================================
// FUNNEL CONFIG
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DurationConfig {
    #[serde(default = "default_min_duration")]
    pub min_duration: u64,
    #[serde(default = "default_max_duration")]
    pub max_duration: u64,
    #[serde(default = "default_avg_duration")]
    pub avg_duration: u64,
}

fn default_min_duration() -> u64 { 5 }
fn default_max_duration() -> u64 { 60 }
fn default_avg_duration() -> u64 { 10 }

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct FunnelStepConfig {
    #[serde(default)]
    pub conversion_rate: f64,
    #[serde(default)]
    pub duration: Option<DurationConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FunnelConfig {
    #[serde(default = "default_funnel_order")]
    pub funnel_order: Vec<String>,
    #[serde(default)]
    pub landing_page: FunnelStepConfig,
    #[serde(default)]
    pub product_view: FunnelStepConfig,
    #[serde(default)]
    pub add_to_cart: FunnelStepConfig,
    #[serde(default)]
    pub checkout: FunnelStepConfig,
    #[serde(default)]
    pub paid: FunnelStepConfig,
}

fn default_funnel_order() -> Vec<String> {
    vec![
        "landing_page".to_string(),
        "product_view".to_string(),
        "add_to_cart".to_string(),
        "checkout".to_string(),
        "paid".to_string(),
    ]
}

// ============================================================================
// SIMULATION & GLOBAL DEFAULTS
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VisitDecayRule {
    pub days: i64,
    pub multiplier: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BasketConfig {
    #[serde(default = "default_min_items")]
    pub min_items: u32,
    #[serde(default = "default_max_items")]
    pub max_items: u32,
}

fn default_min_items() -> u32 { 1 }
fn default_max_items() -> u32 { 10 }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PriceVariationConfig {
    #[serde(default = "default_price_std_pct")]
    pub std_pct: f64,
}

fn default_price_std_pct() -> f64 { 0.05 }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuantityModelConfig {
    #[serde(default = "default_base_lambda")]
    pub base_lambda: f64,
}

fn default_base_lambda() -> f64 { 1.5 }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SimulationSettings {
    #[serde(default = "default_seed")]
    pub random_seed: u64,
    #[serde(default)]
    pub visit_decay: Vec<VisitDecayRule>,
    #[serde(default = "default_reactivation")]
    pub reactivation_probability: f64,
    #[serde(default)]
    pub visit_chance: HashMap<String, f64>,
    pub basket: BasketConfig,
    pub price_variation: PriceVariationConfig,
    pub quantity_model: QuantityModelConfig,
    #[serde(default)]
    pub subcategory_allow_duplicates: HashMap<String, bool>,
}

fn default_seed() -> u64 { 20260101 }
fn default_reactivation() -> f64 { 0.002 }

// ============================================================================
// TIER CONFIG
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HourPeakRange {
    pub min: u32,
    pub max: u32,
    pub avg: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HourPeakConfig {
    pub weight: f64,
    pub hour: HourPeakRange,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TierConfig {
    #[serde(default = "default_profile")]
    pub profile: String,
    pub description: Option<String>,
    #[serde(default)]
    pub visit_chance: HashMap<String, f64>,
    #[serde(default)]
    pub monthly_visit_chance_multiplier: HashMap<String, f64>,
    #[serde(default)]
    pub landing_page: Option<FunnelStepConfig>,
    #[serde(default)]
    pub product_view: Option<FunnelStepConfig>,
    #[serde(default)]
    pub add_to_cart: Option<FunnelStepConfig>,
    #[serde(default)]
    pub checkout: Option<FunnelStepConfig>,
    #[serde(default)]
    pub paid: Option<FunnelStepConfig>,
    #[serde(default)]
    pub funnel_noise: Option<NoiseConfig>,
    #[serde(default)]
    pub visit_hour_peak: HashMap<String, HourPeakConfig>,
    #[serde(default = "default_base_user")]
    pub base_user: usize,
    #[serde(default = "default_retry")]
    pub daily_retry: u32,
    #[serde(default)]
    pub daily_new_user_chance: f64,
    #[serde(default)]
    pub daily_new_user_chance_weekend: f64,
    #[serde(default)]
    pub basket: Option<BasketConfig>,
    #[serde(default)]
    pub category_weight: HashMap<String, f64>,
    #[serde(default)]
    pub subcategory_weight: Option<HashMap<String, HashMap<String, f64>>>,
    #[serde(default)]
    pub subcategory_allow_duplicates: Option<HashMap<String, bool>>,
    #[serde(default)]
    pub quantity_model: Option<QuantityModelConfig>,
    #[serde(default)]
    pub quantity_bias: Option<HashMap<String, f64>>,
    #[serde(default)]
    pub city: Option<HashMap<String, f64>>,
    #[serde(default)]
    pub gender: Option<HashMap<String, f64>>,
    #[serde(default)]
    pub acquisition_channel: Option<HashMap<String, f64>>,
}

fn default_profile() -> String { "balanced".to_string() }
fn default_base_user() -> usize { 10 }
fn default_retry() -> u32 { 3 }

// ============================================================================
// GROWTH & EVENT CONFIGS
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct GrowthMultipliers {
    #[serde(default = "default_one_f64")]
    pub new_user: f64,
    #[serde(default = "default_one_f64")]
    pub visit: f64,
    #[serde(default = "default_one_f64")]
    pub conversion: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct GrowthConfig {
    #[serde(default)]
    pub base: Option<HashMap<String, GrowthMultipliers>>,
    #[serde(default)]
    pub yearly: Option<HashMap<String, HashMap<String, GrowthMultipliers>>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CampaignConfig {
    pub name: String,
    pub description: Option<String>,
    pub year: u32,
    pub start_month: Option<u32>,
    pub end_month: Option<u32>,
    #[serde(default)]
    pub overall: Option<GrowthMultipliers>,
    #[serde(default)]
    pub tiers: Option<HashMap<String, GrowthMultipliers>>,
    #[serde(default)]
    pub profiles: Option<HashMap<String, GrowthMultipliers>>,
}

pub type EventConfig = HashMap<String, CampaignConfig>;

// ============================================================================
// FULL SIMULATION CONFIG (Root Object)
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FullSimulationConfig {
    pub simulation: SimulationSettings,
    pub date: DateConfig,
    pub catalog: CatalogConfig,
    pub funnel: FunnelConfig,
    pub tiers: HashMap<String, TierConfig>,
    #[serde(default)]
    pub growth: Option<GrowthConfig>,
    #[serde(default)]
    pub event: Option<EventConfig>,
}

impl FullSimulationConfig {
    /// Parse from YAML string
    pub fn from_yaml(yaml_str: &str) -> Result<Self, serde_yaml::Error> {
        serde_yaml::from_str(yaml_str)
    }

    /// Parse from JSON string
    pub fn from_json(json_str: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(json_str)
    }

    /// Serialize to YAML string
    pub fn to_yaml(&self) -> Result<String, serde_yaml::Error> {
        serde_yaml::to_string(self)
    }

    /// Serialize to JSON string
    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string_pretty(self)
    }
}
