# Rust for Pythonistas: Creanu Labs Guide

Welcome to Rust! If you come from Python, Rust might look intimidating with its type signatures and compiler checks. But here is the secret: **Rust and Python share many high-level ideas**. Once you understand how Python idioms translate into Rust, you will find Rust code readable, elegant, and blazingly fast.

This guide walks you through the concepts used in the `engine/` folder and shows you how every piece connects back to your familiar `sim/` Python modules.

---

## 1. The Rosetta Stone: Python vs. Rust

### 1.1 Dictionaries vs. Structs (`serde`)
In Python, configurations and data rows are loose dictionaries:
```python
# Python
user = {
    "user_id": "usr-000001",
    "tier": "family_shoppers",
    "city": "Jakarta",
    "registered_date": "2023-01-01"
}
```
In Rust, we give data a fixed shape using a `struct`. With the `#[derive(Serialize, Deserialize)]` attribute, the `serde` library can automatically read/write this to YAML or JSON:
```rust
// Rust (engine/src/models.rs)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserRecord {
    pub user_id: String,
    pub tier: String,
    pub city: String,
    pub registered_date: String,
}
```
**Why this is better:** If you misspell a field in Python (e.g. `user["regitered_date"]`), it crashes at runtime. In Rust, the compiler catches the typo immediately before the code even runs!

---

### 1.2 List Comprehensions vs. Iterators
In Python:
```python
# Python
active_names = [u["user_id"] for u in users if u["tier"] == "family_shoppers"]
```
In Rust:
```rust
// Rust
let active_names: Vec<String> = users
    .iter()
    .filter(|u| u.tier == "family_shoppers")
    .map(|u| u.user_id.clone())
    .collect();
```
- `.iter()`: Creates a stream of items (like a generator in Python).
- `.filter(...)`: Equivalent to the `if` clause.
- `.map(...)`: Equivalent to the expression evaluated in the comprehension.
- `.collect()`: Gathers the results back into a `Vec` (Rust's list).

---

### 1.3 `None` vs. `Option<T>`
Python uses `None` everywhere. Rust has no `None` or `NULL` pointers. Instead, if a value might be missing, it is wrapped in an `Option`:
- `Some(value)`: The value exists.
- `None`: The value is missing.

```rust
// A product may or may not have a custom cooldown override:
pub struct ProductConfig {
    pub base_price: f64,
    pub cooldown: Option<u32>, // Can be Some(3) or None
}

// In Python: cooldown = prod.get("cooldown", default_cooldown)
// In Rust:
let cooldown = prod.cooldown.unwrap_or(default_cooldown);
```

---

### 1.4 `try/except` vs. `Result<T, E>`
Python uses exceptions. Rust returns a `Result`:
- `Ok(data)`: The operation succeeded.
- `Err(error)`: The operation failed.

```rust
// In Python:
// try:
//     config = yaml.safe_load(raw_text)
// except yaml.YAMLError as e:
//     ...

// In Rust:
match FullSimulationConfig::from_yaml(raw_text) {
    Ok(config) => println!("Config loaded successfully!"),
    Err(e) => eprintln!("Invalid YAML: {}", e),
}
```

---

### 1.5 Random Sampling: `numpy` / `random` vs. `rand`
In Python:
```python
# Python
import random
import numpy as np

draw = random.random()                         # Float between 0.0 and 1.0
qty = int(np.random.poisson(lam=2.5))          # Poisson draw
pick = random.choices(items, weights=w)[0]    # Weighted choice
```
In Rust:
```rust
// Rust (engine/src/utils.rs)
use rand::Rng;

let draw: f64 = rng.gen();                     // Float between 0.0 and 1.0
let qty = sample_poisson(2.5, &mut rng);       // Poisson draw
let pick = weighted_choice(&weights, &mut rng);// Weighted choice
```

---

## 2. What Does Borrowing (`&` and `&mut`) Mean?

In Python, everything is passed by reference behind the scenes, and the Garbage Collector cleans it up.
In Rust, there is no Garbage Collector. Instead, Rust uses **Ownership**:
- `let user = ...` owns the user data.
- `&user`: **Read-only borrow**. "You can inspect the user data, but you cannot change it."
- `&mut user`: **Mutable borrow**. "You are allowed to modify the user data."

That's why functions in `engine/src/basket.rs` take:
```rust
history: &mut PurchaseHistory // Because the basket needs to record new purchases into history!
```

---

## 3. Codebase Mapping: Python vs. Rust

Here is where every part of your simulation lives in Rust:

| Feature | Python Module | Rust Module |
| :--- | :--- | :--- |
| **Catalog, Tiers, Dates Configs** | `sim/config.py` | `engine/src/config.rs` |
| **User & Lifecycle Generation** | `sim/generate_user.py` | `engine/src/user.rs` |
| **Basket, Pricing & Cooldowns** | `sim/generate_basket.py` | `engine/src/basket.rs` |
| **Conversion Funnel & Peak Hours**| `sim/generate_funnel.py` | `engine/src/funnel.rs` |
| **Simulation Loop & Day Iteration**| `generate.py` | `engine/src/simulation.rs` |
| **Random Utilities & Seeding** | `sim/utils.py` | `engine/src/utils.rs` |
| **WebAssembly Browser Bridge** | *(New for Web)* | `engine/src/lib.rs` |

---

## 4. How WebAssembly (Wasm) Works

WebAssembly is binary code that runs in modern browsers at near-native speed.

```
┌─────────────────────────────────┐
│     Rust Code (engine/src)      │
└────────────────┬────────────────┘
                 │ wasm-pack build --target web
                 ▼
┌─────────────────────────────────┐
│  lettuce_melon_engine.wasm      │ (Compiled binary file)
│  lettuce_melon_engine.js        │ (JavaScript helper glue)
└────────────────┬────────────────┘
                 │ In React Web Worker
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ import init, { run_simulation_wasm } from './engine_wasm'; │
│ await init();                                               │
│ const results = run_simulation_wasm(yamlText, ...);         │
└─────────────────────────────────────────────────────────────┘
```

The user never needs to download or install Python, Rust, or any C++ runtime. The browser runs the Wasm module seamlessly on any computer, tablet, or phone!

---

## 5. How to Install Rust & Build on Windows

When you are ready to test compiling on your machine:

1. **Install Rust (one-time setup):**
   - Download and run the official Windows installer from: [https://rustup.rs](https://rustup.rs)
   - Follow standard default prompts (Option 1).
2. **Install `wasm-pack` (the WebAssembly packager):**
   ```powershell
   cargo install wasm-pack
   ```
3. **Build the Engine for Web:**
   ```powershell
   cd d:\Windsurf\lettuce-melon\engine
   wasm-pack build --target web --out-dir ../web/src/wasm
   ```

This generates the ready-to-import WebAssembly module in the web application folder!
