pub mod basket;
pub mod config;
pub mod funnel;
pub mod models;
pub mod simulation;
pub mod user;
pub mod utils;

use wasm_bindgen::prelude::*;

use crate::config::FullSimulationConfig;
use crate::models::SimulationOutput;

/// Validate a configuration string (either YAML or JSON).
/// Returns parsed config summary or an error string.
#[wasm_bindgen]
pub fn validate_config_wasm(config_str: &str) -> Result<JsValue, JsValue> {
    let config = parse_config(config_str).map_err(|e| JsValue::from_str(&e))?;
    serde_wasm_bindgen::to_value(&config).map_err(|e| JsValue::from_str(&e.to_string()))
}

/// Helper to parse config from either YAML or JSON
fn parse_config(raw: &str) -> Result<FullSimulationConfig, String> {
    let trimmed = raw.trim();
    if trimmed.starts_with('{') {
        FullSimulationConfig::from_json(trimmed).map_err(|e| format!("JSON parse error: {}", e))
    } else {
        FullSimulationConfig::from_yaml(trimmed).map_err(|e| format!("YAML parse error: {}", e))
    }
}

/// Execute simulation directly inside the browser using WebAssembly.
/// Emits progress via progress_js(day, total_days, date_str).
#[wasm_bindgen]
pub fn run_simulation_wasm(
    config_str: &str,
    start_date: Option<String>,
    end_date: Option<String>,
    seed: Option<f64>,
    progress_js: Option<js_sys::Function>,
) -> Result<JsValue, JsValue> {
    let config = parse_config(config_str).map_err(|e| JsValue::from_str(&e))?;

    let seed_u64 = seed.map(|s| s as u64);

    let callback = progress_js.map(|cb| {
        let cb_box: simulation::ProgressCallback = Box::new(move |day, total, date| {
            let this = JsValue::NULL;
            let arg_day = JsValue::from_f64(day as f64);
            let arg_total = JsValue::from_f64(total as f64);
            let arg_date = JsValue::from_str(date);
            let _ = cb.call3(&this, &arg_day, &arg_total, &arg_date);
        });
        cb_box
    });

    let output: SimulationOutput = simulation::run_simulation(
        &config,
        start_date.as_deref(),
        end_date.as_deref(),
        seed_u64,
        callback.as_ref(),
    )
    .map_err(|e| JsValue::from_str(&e))?;

    serde_wasm_bindgen::to_value(&output).map_err(|e| JsValue::from_str(&e.to_string()))
}

/// Convert specific dataset in memory to CSV string format
#[wasm_bindgen]
pub fn export_table_csv(dataset_name: &str, output_js: JsValue) -> Result<String, JsValue> {
    let output: SimulationOutput = serde_wasm_bindgen::from_value(output_js)
        .map_err(|e| JsValue::from_str(&format!("Invalid simulation output: {}", e)))?;

    let mut csv = String::new();

    match dataset_name {
        "users" => {
            csv.push_str("tier,user_id,city,gender,acquisition_channel,registered_date,last_active_date\n");
            for u in output.users {
                csv.push_str(&format!(
                    "{},{},{},{},{},{},{}\n",
                    u.tier, u.user_id, u.city, u.gender, u.acquisition_channel, u.registered_date, u.last_active_date
                ));
            }
        }
        "transactions" => {
            csv.push_str("session_id,user_id,trx_id,date,tier,total_price\n");
            for t in output.transactions {
                csv.push_str(&format!(
                    "{},{},{},{},{},{:.2}\n",
                    t.session_id, t.user_id, t.trx_id, t.date, t.tier, t.total_price
                ));
            }
        }
        "transaction_items" => {
            csv.push_str("trx_id,user_id,tier,date,product,quantity,unit_price,total_price\n");
            for it in output.transaction_items {
                csv.push_str(&format!(
                    "{},{},{},{},{},{},{:.2},{:.2}\n",
                    it.trx_id, it.user_id, it.tier, it.date, it.product, it.quantity, it.unit_price, it.total_price
                ));
            }
        }
        "funnel" => {
            csv.push_str("session_id,tier,user_id,activity,activity_datetime\n");
            for f in output.funnel {
                csv.push_str(&format!(
                    "{},{},{},{},{}\n",
                    f.session_id, f.tier, f.user_id, f.activity, f.activity_datetime
                ));
            }
        }
        "catalog" => {
            csv.push_str("category,subcategory,product,base_price\n");
            for c in output.catalog {
                csv.push_str(&format!(
                    "{},{},{},{:.2}\n",
                    c.category, c.subcategory, c.product, c.base_price
                ));
            }
        }
        _ => return Err(JsValue::from_str(&format!("Unknown dataset: {}", dataset_name))),
    }

    Ok(csv)
}
