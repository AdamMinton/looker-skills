# Local Harness Guide

The **Harness** is your local simulation of Looker. It allows you to develop 10x faster by removing the "Upload -> Reload -> Click" loop.

## Architecture

The harness consists of three parts:
1.  **`builder.html`**: The UI shell (sidebar, canvas, buttons).
2.  **`mocks.js`**: The simulated Looker API (`looker.plugins.visualizations.add`, `trigger`).
3.  **`data_scenarios.js`**: The mock data library.

## How to Use

### 1. Define a Scenario

In `harness/data_scenarios.js`, add a new key for your test case.

**Structure:**
```javascript
window.scenarios = {
  my_new_scenario: {
    config: {
      font_size: "large", // Default options
      my_custom_option: "blue"
    },
    data: [
       // Row 1
      {
        "users.count": { value: 100, rendered: "100" },
        "users.created_date": { value: "2023-01-01", rendered: "2023-01-01" }
      }
    ],
    queryResponse: {
      fields: {
        dimensions: [
          { name: "users.created_date", label: "Created Date", type: "date" }
        ],
        measures: [
          { name: "users.count", label: "Count", type: "count_distinct" }
        ]
      }
    }
  }
};
```

### 2. Mocking API Calls

If your visualization calls `looker.charts.Utils.textForCell(cell)`, you **must** ensure it is mocked in `harness/mocks.js`.

**Example Mock:**
```javascript
window.LookerCharts = {
  Utils: {
    textForCell: (cell) => cell.rendered || String(cell.value),
    htmlForCell: (cell) => cell.html || cell.rendered || String(cell.value),
    openDrillMenu: (options) => {
        console.log("DRILL MENU OPENED", options);
    }
  }
};
```

### 3. Debugging

*   **Console is King**: `console.log` is visible in the harness.
*   **"Run" Button**: The harness does NOT auto-reload code changes (unless you use HMR, which is complex). You typically need to reload the browser page after a `yarn build` or `webpack` recompile.
*   **Editor Persistence**: Changes made in the harness UI (changing options) *do* persist until you reload the page.

## Best Practices

1.  **Create "Edge Case" Scenarios**:
    *   `empty_data`: `data: []`
    *   `null_values`: `data: [{ "field": { value: null } }]`
    *   `huge_data`: `data: [...1000 rows...]`
2.  **Verify Error Handling**:
    *   Load the `empty_data` scenario.
    *   Verify your viz calls `addError()` and the harness logs it to the console.
