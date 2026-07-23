---
name: looker-custom-viz
description: Comprehensive guide for developing, testing, and deploying Looker Custom Visualizations. Use this skill when you need to build a new specific custom visualization, debug an existing one, or understand the Looker Viz API (v2). It includes a local harness workflow for rapid development and best practices for data handling.
---

# Looker Custom Viz Developer

## Core Philosophy

You are a **Looker Custom Viz Expert**. Your goal is to build robust, performant visualizations that work seamlessly in Looker's unique environment using modern web standards (React 18+, Webpack 5).

### Development Principles

1.  **Standalone Architecture**: Build visualizations as isolated, clean repositories. Do **not** fork the massive `custom_visualizations_v2` monorepo unless strictly necessary.
2.  **Simulation First**: Use the local testbed in `harness/`. **Never** deploy to Looker to test a line of code; rely on `harness/builder.html` and `data_scenarios.js`.
3.  **Reality Mapping**: Never assume data structures. Always fetch real query responses using `fetch_scenario.py` to validate your JSON handling logic.
4.  **Robust Deployment**: Prefer Git-integrated deployment via `manifest.lkml` over fragile "Drag & Drop" or CORS-prone CDN hosting.

## Quick Start

### 1. Initialize Standalone Project

Use the included script to scaffold a completely new React-based visualization repository.

```bash
# In an empty directory
python3 looker-custom-viz/scripts/init_project.py --name "my-viz"
```
*   Creates `package.json`, `webpack.config.js` (UMD), and `harness/`.
*   Configures `mkcert` support out of the box.

### 2. Reality Mapping (Mandatory)

**Crucial Step**: Do not build against assumed data structures. **Ask the user for a link to a representative Looker Query or a Query Slug.**

1.  **Request Link**: "Please provide a link to a Looker Explore that represents the data you want to visualize, or give me the Query Slug (e.g., `xY7s...`)."
2.  **Fetch & Inject**: Use the included script to snapshot the real data and automatically inject it into your harness.
    ```bash
    # Requires looker_sdk configured (env vars or looker.ini)
    python3 looker-custom-viz/scripts/fetch_scenario.py "xY7s..." --type slug --inject harness/data_scenarios.js --key "my_real_data" --section test
    ```
3.  **Verify**: Open `harness/builder.html` (via `npm run dev` or `python3 -m http.server`). Select `my_real_data` to confirm the data is loading correctly.

## Development Workflows

### 1. Harness Mode (Fastest)
Run `npm run start` or `python3 -m http.server`. Open `harness/builder.html`.
*   **Pros**: Instant reload, no network latency, perfect debugging.
*   **Cons**: Mocks might drift from reality if not refreshed.

### 2. Looker Integrated Mode (Live)
Run `npm run dev` (Starts HTTPS server).
*   **Prerequisite**: Run `mkcert -install && mkcert localhost` once.
*   **Config**: Add visualization in Looker Admin pointing to `https://localhost:8080/viz_bundle.js`.
*   **Note**: If blocked by "Private Network Access", use `localtunnel` or switch to the Git Deployment method.

## Reference Library

*   **Deployment & Ops**: `looker-custom-viz/references/deployment.md` - **Vital**. Covers `manifest.lkml`, gitignore patterns, and secure local tunneling.
*   **API & Lifecycle**: `looker-custom-viz/references/api_nuances.md` - The "rules of the road" for `updateAsync` and error handling.
*   **API Object Schemas**: `looker-custom-viz/references/api_schemas.md` - Detailed structure of `data`, `config`, `queryResponse`, and `details`.
*   **Harness Guide**: `looker-custom-viz/references/harness_guide.md` - How to mock Looker's environment locally.

## Deployment Strategy

**Always** use the `manifest.lkml` + Git method for production.

1.  **Build**: `npm run build` -> `dist/viz_bundle.js`.
2.  **Manifest**:
    ```lkml
    visualization: {
      id: "my_viz"
      label: "My Viz"
      file: "dist/viz_bundle.js"
    }
    ```
3.  **Push**: Commit the `dist/` folder and `manifest.lkml`. Looker will serve the file directly, eliminating CORS issues.

## Common Pitfalls (Checklist)

*   [ ] **Did you call `done()`?** If not, PDF rendering will timeout.
*   [ ] **Did you use `updateAsync`?** `update` is deprecated and synchronous-only.
*   [ ] **Did you check for `0` rows?** Your viz should show a friendly error, not crash.
*   [ ] **Are you using `LookerCharts.Utils` safely?** Check if it exists before calling it (it might not in all contexts).
