# Data Patterns & Recipes

## 1. Handling Pivots

When data is pivoted, the `data` array structure changes. You cannot just look at `fields.measures`.

### The Pattern
1.  **Check for Pivots**: `queryResponse.pivots` (Array).
2.  **Iterate Columns**: You typically want to generate columns for each Pivot + Measure combination.

```javascript
const pivots = queryResponse.pivots || [];
const measures = queryResponse.fields.measures;

// If Pivoted
if (pivots.length > 0) {
    pivots.forEach(pivot => {
        measures.forEach(measure => {
            const fieldKey = measure.name;
            const pivotKey = pivot.key;
            // Access data using the pivot key
            // Note: Pivot keys often look like "Value|FIELD|Value" (e.g., "2026|FIELD|Shipped")
            const cell = row[fieldKey][pivotKey]; 
        });
    });
}
```

**Key Difference**:
*   **Flat**: `row['users.count'].value`
*   **Pivoted**: `row['users.count']['PivotValue_1'].value`

## 2. Handling Drills

Drills are essentially a list of links attached to a cell.

```javascript
/* inside your click handler */
function onCellClick(event, cell) {
  // 1. Check if links exist
  if (!cell.links || cell.links.length === 0) return;

  // 2. Prevent default navigation if using <a> tag
  event.preventDefault();

  // 3. Open Looker Menu
  LookerCharts.Utils.openDrillMenu({
    links: cell.links,
    event: event
  });
}
```

## 3. Handling "No Data"

Always guard against empty results.

```javascript
if (!data || data.length === 0) {
    this.addError({
        title: "No Data",
        message: "The query returned no results."
    });
    return;
}
```

## 4. Coloring

Use Looker's passed color palette if available.

```javascript
const palette = config.custom_color_palette || 
                looker.charts.Utils.getScale("categorical", 10).range();
```

*   **Warning**: `getScale` is not always documented reliable. It's safer to just rely on a `collection` option if you want robust native color support, or expose standard color pickers.

## 5. Merged Results

Merged Results are a common source of bugs because they structure `queryResponse` differently.

*   **Field Aliasing**: Fields often get prefixed (e.g., `q1_order_items.count`, `q2_order_items.count`). **Never hardcode field names** if you want to support merged results. Always inspect `queryResponse.fields.measure_like`.
*   **Missing Dimensions**: Merged results often report empty `dimensions` arrays, moving everything into `measure_like`.
*   **Data Structure**: They typically return a flat array of rows similar to standard queries, but the keys in the row objects match the *aliased* names found in `measure_like`.

```javascript
// Example: Dynamically finding valid numeric fields in a Merged Result
const measures = queryResponse.fields.measure_like;
data.forEach(row => {
    measures.forEach(measure => {
        // measure.name might be "q1_order_items.count"
        // Always derive the key from the response, don't guess it.
        const cell = row[measure.name]; 
        console.log(cell.value); 
    });
});
```
