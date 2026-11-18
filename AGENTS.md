# Project instructions

These instructions apply to AI coding assistants working in this repository.

## Project context

Creanu Labs generates synthetic retail and grocery simulation data. The repository currently contains:

- A Python simulation and data-generation workflow (`generate.py`, `sim/`).
- A Rust simulation engine (`engine/`), also intended for WebAssembly use.
- A React, TypeScript, and Vite web app (`web/`).
- YAML simulation settings and presets (`config/`).

The project is migrating and evolving; do not assume the Rust engine has replaced every Python workflow or that plans in documentation describe fully implemented behavior. Check the current code and its callers before choosing where to make a change.

## Working principles

- Preserve existing behavior and output formats unless the request explicitly calls for a change.
- Keep Python, Rust, the web app, and YAML configuration consistent where they implement or expose the same behavior. First confirm which paths are active; do not make unrelated layers change just for symmetry.
- Treat reproducibility as a core property. Preserve seeded behavior and idempotency where they already exist. Do not claim Python and Rust produce identical random sequences unless that is explicitly implemented and tested.
- Treat configuration and generated data schemas as user-facing contracts. When changing them, update the directly dependent parsers, types, presets, exports, and documentation as needed.
- Prefer small, focused changes that follow the surrounding code's patterns. Avoid new dependencies and abstractions unless they solve a demonstrated need.
- Measure performance before making performance claims; do not trade correctness or reproducibility for an unverified optimization.
- Keep explanations beginner-friendly, especially for Rust concepts, without adding comments that merely restate the code.

## Safety and scope

- Do not overwrite or delete generated files in `output/` unless the user asks for that operation. In particular, `initial_run()` in `generate.py` intentionally replaces simulation output files.
- Do not change unrelated user work or generated/configuration data as part of a code task.
- Surface invalid input and operational failures clearly; avoid silently swallowing errors or returning success-shaped fallbacks.
- Do not add credentials, private data, or machine-specific settings to the repository.

## Validation

- Run the smallest relevant existing check for the files changed, and report what was run and any limitations.
- For Rust engine changes, use `cargo test --manifest-path engine/Cargo.toml` when applicable.
- For web app changes, run `npm run build` from `web/` when applicable.
- For Python or YAML changes, inspect the existing entry points and validation conventions first; do not assume a test runner exists.
- Do not run a full data-generation workflow just to validate code if it could replace files in `output/`.
