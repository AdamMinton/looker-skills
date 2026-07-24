---
name: looker-custom-viz
description: Comprehensive guide for developing, testing, and deploying Looker Custom Visualizations. Use this skill when you need to build a new specific custom visualization, debug an existing one, or understand the Looker Viz API (v2). It includes a local harness workflow for rapid development and best practices for data handling.
---

# Looker Custom Viz Developer

## Core Philosophy

You are a **Looker Custom Viz Expert**. Your goal is to build robust, performant visualizations that work seamlessly in Looker's unique environment using modern web standards (React 18+, Webpack 5).

### 💡 Looker CLI Recommendation
It is highly recommended to fulfill Looker-side interactions (such as session management, project configurations, manifest definitions, and asset uploads) using the Looker CLI (`looker-cli`) to simplify deployment and testing.

### Development Principles

1.  **Native Fidelity & Typography**: Look and feel exactly like native Looker tiles. Because sandboxed custom visualization iframes do not inherit styles, you must explicitly declare Google's native fonts (resolved dynamically at runtime from the parent origin) and use Looker's exact theme colors and empty states.
2.  **Compile-Safe Deployment**: Never upload untested raw code to a project. Always run offline syntax checks (`node -c path/to/viz.js`) or bundler builds (`npm run build`) before pushing files to prevent breaking Looker dashboards.
3.  **Asset Minification**: Always compress production assets using `terser` to keep files lightweight and minimize dashboard loading latency.
4.  **Simulation & Reality Mapping**: Use the local testbed (`harness/builder.html`) to isolate and test rendering code with mock scenarios, and fetch real query response shapes to validate the data transformation layer before deploying.

## Onboarding Transparency & Alignment
When starting a new custom visualization project, the developer agent **MUST NOT** make modifications to the Looker instance (such as creating projects, connections, or model sets) automatically. Instead, you must:
1.  **Document and Present the exact `looker-cli` commands** needed for these adjustments to the user.
2.  Allow the user to review the commands and execute them manually, or request explicit confirmation before running any instance-modifying command on their behalf.
3.  For reference on `looker-cli` setup and commands, refer to [references/deployment_guide.md](file://./references/deployment_guide.md).

## Quick Start

### 1. Setting Up Your Local Workspace

All Looker-side operations (creating projects, managing development sessions, and uploading visualization files) **must be fulfilled exclusively using the Looker CLI (`looker-cli`)**. 

To set up a local workspace for coding and testing:
1.  **Create a project directory** on your local machine.
2.  **Copy the harness assets**: Copy the `assets/harness/` directory (containing `builder.html`, `mocks.js`, `data_scenarios.js`, and `server.py`) from this skill into your local project directory.
3.  **Create your visualization script**: Create your main JavaScript file (e.g., `demo_viz.js`) in the same folder.

### 2. Reality Mapping (Mandatory)

**Crucial Step**: Do not build against assumed data structures. **Ask the user for a link to a representative Looker Query or a Query Slug.**

1.  **Request Link**: "Please provide a link to a Looker Explore that represents the data you want to visualize, or give me the Query Slug (e.g., `xY7s...`)."
2.  **Start Proxy Server**: Run the harness API proxy server locally:
    ```bash
    python3 skills/looker-custom-viz/assets/harness/server.py --port 45873
    ```
3.  **Import Dynamically**: Open `http://localhost:45873/skills/looker-custom-viz/assets/harness/builder.html` in your browser. Click **+ Import**, paste the Explore URL or Query Slug, check **Save permanently**, and click **Import** to load it instantly.

## Development Workflows

1.  **Harness Mode (Fastest, Offline)**:
    *   Run the proxy server locally:
        ```bash
        python3 skills/looker-custom-viz/assets/harness/server.py --port 45873
        ```
    *   Open `http://localhost:45873/skills/looker-custom-viz/assets/harness/builder.html` in your browser.
    *   *Details & Edge Cases*: Refer to [references/deployment_guide.md: Section 1 (Harness Testing)](file://./references/deployment_guide.md#L7-L32).
2.  **Looker Deployment & Live Mode**:
    *   Manage active testing or production deploys using Looker CLI or Git Manifest project integrations.
    *   *Details*: Refer to [references/deployment_guide.md: Section 3 (Deployment Strategies)](file://./references/deployment_guide.md#L52-L87).

## Reference Library

*   **API & Features Guide**: [references/api_guide.md](file://./references/api_guide.md) - Lifecycle methods, parameters, cell HTML formatting, and native drill coordinates.
*   **Data Patterns & Recipes**: [references/data_patterns.md](file://./references/data_patterns.md) - Code patterns for handling pivoted data structures, programmatic drill actions, mock scenarios, coloring fallbacks, and query shape/field count validations.
*   **Harness & Deployment Guide**: [references/deployment_guide.md](file://./references/deployment_guide.md) - Local offline testing, mock scenarios, Looker CLI dev mode, and manifest settings.
*   **Marketplace Requirements**: [references/marketplace_requirements.md](file://./references/marketplace_requirements.md) - Official Looker quality guidelines including code organization, security audits, dependency schemas, and styling consistency checklist.
*   **Styling & Layout Guide**: [references/styling_guide.md](file://./references/styling_guide.md) - ResizeObserver dynamic resizing, padding conventions, dynamic font resolution, and native Looker empty states.
*   **Data Visualization Guide**: [references/visualization_guide.md](file://./references/visualization_guide.md) - Best practices for chart presentation, chart choice rules, axes, coloring, and Looker config parameters.

---

## Pre-Flight & Marketplace Checklist

Before deploying your custom visualization to production, verify you have completed these quality checks:

*   [ ] **Call `done()`**: Ensure `done()` is called at the end of `updateAsync` (see [api_guide.md](file://./references/api_guide.md#L15-L24)).
*   [ ] **Query Shape Validation**: Verify measures and dimensions count using `this.addError` (see [data_patterns.md](file://./references/data_patterns.md#L141-L178)).
*   [ ] **Looker Cell Formatting**: Render display values using `LookerCharts.Utils.htmlForCell` (see [api_guide.md](file://./references/api_guide.md#L67-L80)).
*   [ ] **Drill Menus**: Trigger drill menus by passing the native DOM event (see [api_guide.md](file://./references/api_guide.md#L81-L99)).
*   [ ] **Dynamic Font Resolution**: Load `Google Sans` using referrer origin interpolation (see [styling_guide.md](file://./references/styling_guide.md#L45-L77)).
*   [ ] **Fluid Sizing (ResizeObserver)**: Bind container sizing to `ResizeObserver` (see [styling_guide.md](file://./references/styling_guide.md#L5-L39)).
*   [ ] **Tighter Margin Spacing**: Follow standard margin spacing conventions (55px left, 40px bottom, 2px padding) (see [styling_guide.md](file://./references/styling_guide.md#L41-L43)).
*   [ ] **CSP Inline Script Compliance**: Do not use inline HTML handlers; bind programmatically (see [api_guide.md](file://./references/api_guide.md#L101-L119)).
*   [ ] **Exact ID Matching**: Verify `manifest.lkml` ID matches the JS registration ID (see [deployment_guide.md](file://./references/deployment_guide.md#L88-L96)).
*   [ ] **First-Time Prod Deploy**: Project must be pushed to production once to index the custom viz dropdown (see [deployment_guide.md](file://./references/deployment_guide.md#L97-L99)).
*   [ ] **Code Minification**: Verify syntax with `node -c` and minify files using `terser` (see [deployment_guide.md](file://./references/deployment_guide.md#L34-L49)).
