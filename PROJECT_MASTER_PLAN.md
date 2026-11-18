# Creanu Labs: Web Platform & Rust Engine Master Plan

> **Goal:** Transform Creanu Labs (`lettuce-melon`) from a local Python script into a high-performance, browser-executable web application hosted on Cloudflare Workers, capable of generating, analyzing, and downloading realistic synthetic retail datasets in seconds.

---

## 1. System Architecture

```
                       ┌──────────────────────────────────────────────┐
                       │           Cloudflare Edge Network            │
                       │                                              │
                       │  ┌────────────────────────────────────────┐  │
                       │  │ Cloudflare Workers (Static Assets)     │  │
                       │  │ - React Single Page Application        │  │
                       │  │ - Monaco YAML & Form Editor            │  │
                       │  │ - Interactive Diff Dashboard           │  │
                       │  └───────────────────┬────────────────────┘  │
                       │                      │                       │
                       │  ┌───────────────────▼────────────────────┐  │
                       │  │ (Optional Future) Workers API + D1     │  │
                       │  │ - Shared Configs Catalog               │  │
                       │  │ - Upvotes & Community Presets          │  │
                       │  └────────────────────────────────────────┘  │
                       └──────────────────────┬───────────────────────┘
                                              │ User's Browser
                       ┌──────────────────────▼───────────────────────┐
                       │           Client-Side Web Worker             │
                       │                                              │
                       │  ┌────────────────────────────────────────┐  │
                       │  │ Rust Simulation Engine (Wasm)          │  │
                       │  │ - Serde dynamic YAML/JSON parser       │  │
                       │  │ - Vectorized funnel & basket simulator │  │
                       │  │ - Generates 100k+ rows in < 2 seconds  │  │
                       │  └───────────────────┬────────────────────┘  │
                       │                      │ Progress & Datasets   │
                       │  ┌───────────────────▼────────────────────┐  │
                       │  │ In-Browser ZIP & CSV Packaging         │  │
                       │  │ - Instant zero-server-cost download    │  │
                       │  └────────────────────────────────────────┘  │
                       └──────────────────────────────────────────────┘
```

---

## 2. Addressing Your Feedback & Key Decisions

### A. Is Rust Still Configurable?

**Yes, 100%.**
In Rust, we use the `serde` (`serde_yaml` & `serde_json`) crate. The engine does **not** hardcode values. Instead, it defines strongly-typed configuration structs that dynamically parse whatever YAML or JSON string the user writes in the web UI. If a user leaves something out, Rust automatically applies default values.

### B. "I Don't Know Rust — Can You Guide Me?"

**Yes!** We will:

1. Provide a dedicated `RUST_FOR_PYTHONISTAS.md` guide that maps familiar Python concepts (`dict`, `pandas`, `for-in`, `random.choices`) directly to their Rust equivalents (`HashMap`, `Vec`, `iter()`, `rand`).
2. Write clean, modular, heavily commented Rust code where each file mirrors the existing Python modules (`sim/generate_basket.py` $\to$ `engine/src/basket.rs`, etc.).
3. Handle the compilation toolchain so you don't have to wrestle with arcane build flags.

### C. Cloudflare Deployment: Modern Cloudflare Workers

You are completely right: Cloudflare has unified Pages into **Cloudflare Workers** with the static assets feature (`assets` binding in `wrangler.jsonc`).

- **Hosting:** 100% free static site hosting via Cloudflare Workers.
- **Compute:** Zero server bills because the simulation runs client-side inside the user's browser via WebAssembly.
- **Community Configs (D1 Database):** We can add a lightweight Cloudflare D1 SQL database where users can click _"Share My Config"_ and upvote popular community presets.

### D. Realistic Presets Aligned With Your Grocery & Produce Catalog

Your point is spot-on: the product catalog (`config/catalog.yaml`) is built exclusively around **fresh groceries and produce** (vegetables like spinach/kale/lettuce, fruits like berries/citrus/tropical, with prices in Indonesian Rupiah IDR).

Rather than generic retail, the presets must represent **realistic grocery & supermarket shopping dynamics** matching your existing customer tiers (`family_shoppers`, `health_conscious`, `students`, `young_professionals`, `small_business_owners`):

| Preset Scenario                                 | Dynamics & Alignment with Repo                                                                                                                           |
| :---------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Weekend Family Supermarket Rush**          | High weight on `family_shoppers`, Saturday/Sunday traffic spike, large baskets (8–15 items), higher units per item, bulk leafy greens & root vegetables. |
| **2. Healthy Living & Organic Wave**            | High weight on `health_conscious` tier, daily steady visits, high preference for berries, citrus, and leafy greens with low cooldown sensitivity.        |
| **3. Student & Young Professional Quick-Bites** | Dominant `students` and `young_professionals` tiers, weekday evening peaks (7–10 PM), smaller quick baskets (1–4 items), fast checkout.                  |
| **4. Cafe & Restaurant Daily Restock**          | High weight on `small_business_owners`, high weekday order frequency, large bulk quantities, strict cooldown adherence.                                  |
| **5. Holiday Harvest Surge**                    | High December holiday multiplier (`monthly_rate: 1.4`), surge in tropical fruits, stone fruits, and gift/celebration baskets.                            |

### E. Summary Dashboard with Baseline Diff

The web dashboard will show **two sets of numbers**:

1. **Current Simulation Metrics:** Total GMV, Orders, Conversion Rate, Average Order Value (AOV), Active Users.
2. **Baseline Difference ($\Delta$):**
   - e.g., `Revenue: $148,200 (+24.2% vs Default)`
   - `Funnel Conversion: 3.8% (-0.4% vs Default)`
   - A visual diff indicator showing exactly which parameters in their YAML deviate from defaults.

### F. Client-Side Packaging & Real-time Progress Bar

- The Web Worker will emit progress events (e.g., `Day 12 of 30 (40%)`) so the UI renders a responsive progress bar with cancel capability.
- Datasets are formatted into CSV streams in-memory and bundled into a `.zip` file using `JSZip` or native browser streams, downloading instantly.

---

## 3. Project Management & Linear Tracker

**Linear Project:** [Creanu Labs - Web Platform & Rust Engine](https://linear.app/ibnulab/project/creanu-labs-web-platform-and-rust-engine-9aeb91c0bfc3) (`P-IBN-1`)

| Issue ID                                          | Milestone / Task                                                    | Priority | Status  |
| :------------------------------------------------ | :------------------------------------------------------------------ | :------- | :------ |
| [IBN-5](https://linear.app/ibnulab/issue/IBN-5)   | **Engine:** Port simulation core to Rust & Wasm                     | Urgent   | Done    |
| [IBN-6](https://linear.app/ibnulab/issue/IBN-6)   | **Docs:** Write `RUST_FOR_PYTHONISTAS.md` learning guide            | High     | Done    |
| [IBN-7](https://linear.app/ibnulab/issue/IBN-7)   | **Frontend:** Scaffold React/Vite app with Tailwind & Monaco Editor | High     | Done    |
| [IBN-8](https://linear.app/ibnulab/issue/IBN-8)   | **Frontend:** Build Retail & Grocery Scenario Presets               | Medium   | Done    |
| [IBN-9](https://linear.app/ibnulab/issue/IBN-9)   | **Analytics:** Implement KPI Summary & Baseline Diff Dashboard      | Medium   | Done    |
| [IBN-10](https://linear.app/ibnulab/issue/IBN-10) | **Export:** Build in-browser multi-CSV ZIP packaging                | Medium   | Done    |
| [IBN-12](https://linear.app/ibnulab/issue/IBN-12) | **UI:** Fix Raw YAML editor blank bug & add paired numeric inputs   | Urgent   | Done    |
| [IBN-13](https://linear.app/ibnulab/issue/IBN-13) | **Design:** Redesign UI aesthetic away from generic AI look         | High     | Done    |
| [IBN-14](https://linear.app/ibnulab/issue/IBN-14) | **UX:** Separate Config Studio and Dashboard into dedicated views   | High     | Done    |
| [IBN-15](https://linear.app/ibnulab/issue/IBN-15) | **Config:** Add comprehensive engine controls for all parameters    | High     | Done    |
| [IBN-16](https://linear.app/ibnulab/issue/IBN-16) | **Design:** Adopt Swiss aesthetic with Light & Dark mode toggle     | High     | Done    |
| [IBN-17](https://linear.app/ibnulab/issue/IBN-17) | **Presets:** Fix Holiday Harvest duplicate YAML key error           | Urgent   | Done    |
| [IBN-18](https://linear.app/ibnulab/issue/IBN-18) | **Analytics:** 90-day steady-state baseline generation              | High     | Done    |
| [IBN-19](https://linear.app/ibnulab/issue/IBN-19) | **Charts:** Add Daily, Weekly, Monthly, Yearly aggregation toggles  | Medium   | Done    |
| [IBN-20](https://linear.app/ibnulab/issue/IBN-20) | **Export:** Ensure complete non-truncated dataset download          | Medium   | Done    |
| [IBN-21](https://linear.app/ibnulab/issue/IBN-21) | **Config:** Comprehensive engine parameters audit & full integration| Low      | Done    |

---

## 4. Technology Stack Summary

- **Simulation Engine:** Rust (`rand`, `serde`, `serde_yaml`, `wasm-bindgen`).
- **Web Frontend:** React 19 / Vite / Tailwind CSS / TypeScript.
- **Code Editor:** Monaco Editor (`@monaco-editor/react`).
- **Charts & Visualization:** Recharts or Chart.js (lightweight, zero latency).
- **Client Compression:** `JSZip` / FileSaver API.
- **Hosting & Edge Deployment:** Cloudflare Workers (Static Assets).
- **Optional Database:** Cloudflare D1 (Serverless SQLite).
