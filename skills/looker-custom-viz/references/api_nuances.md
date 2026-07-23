# Looker Viz API Nuances ("The Textbook")

## 1. Lifecycle Methods

The Visualization API is a state machine. You must handle transitions cleanly.

### `create(element, config)`
*   **Run Once**: Called only when the visualization is first initialized.
*   **Goal**: Create DOM containers, SVG roots, or Canvas elements.
*   **Access**: `this.chart = ...` (Store references on `this`).
*   **Do Not**: Render data here. Data is not guaranteed to be available.

### `updateAsync(data, element, config, queryResponse, details, done)`
*   **Run Many Times**: Called on every data change, resize, or option change.
*   **The "Async" Lie**: It is named `Async`, but Looker expects you to behave synchronously unless you explicitly delay calling `done()`.
*   **Critical Params**:
    *   `data`: Array of row objects.
    *   `queryResponse`: Metadata (fields, pivots).
    *   `done`: **MUST BE CALLED** or the visualization will hang in PDF generation.
*   **Error Clearing**: Always call `this.clearErrors()` at the very start.

## 2. Rendering Data

### The `data` Object
It is an array of rows. Each row is a dictionary of `field_name` -> `cell`.

```json
[
  {
    "users.count": {
      "value": 42,
      "rendered": "42",
      "html": "<a href='...'>42</a>"
    }
  }
]
```

### `value` vs `rendered` vs `html`
*   `value`: Raw data (Number, Date object). Use for **logic/math**.
*   `rendered`: String representation (e.g., "$42.00"). Use for **labels**.
*   `html`: Sanitize HTML from Looker. **Prioritize this** if you want links and formatting to work.
*   **Helper**: `LookerCharts.Utils.htmlForCell(cell)` automatically handles the fallback logic.

## 3. Options (Configuration)

Define options in `this.options` or register them dynamically.

```javascript
options: {
  font_size: {
    type: "string",
    label: "Font Size",
    values: [
      {"Small": "small"},
      {"Large": "large"}
    ],
    display: "select",
    default: "large"
  }
}
```

*   **Access**: `config.font_size` in `updateAsync`.
*   **Registering**: `this.trigger('registerOptions', options)` allows you to change options dynamically based on data.

## 4. Common Pitfalls

### The "PDF Timeout"
If your viz looks great in the browser but fails in scheduled emails:
1.  **Likely Cause**: You forgot to call `done()`.
2.  **Likely Cause**: You have an animation that never finishes.
3.  **Fix**: Ensure `done()` is called *after* the animation completes/settles.

### "It works locally but not in Looker"
*   **Likely Cause**: CSS collision. Looker has global CSS.
*   **Fix**: Use specific class names or Shadow DOM (if careful).
*   **Likely Cause**: `LookerCharts` global missing.
*   **Fix**: Check `if (window.LookerCharts) ...`

### "My drill links don't work"
*   **Requirement**: You must handle the click event.
*   **Code**:
    ```javascript
    LookerCharts.Utils.openDrillMenu({
      links: cell.links,
      event: domEvent // The click event (needed for positioning)
    });
    ```
