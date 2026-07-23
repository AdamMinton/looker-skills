# API Object Schemas

This document details the structure of the four critical objects passed to `updateAsync(data, element, config, queryResponse, details, done)`.

## 1. Data (`data`)
An array of "Row Objects". Each row represents a single line of the query result.

**Type**: `Array<RowObject>`

### Row Object Structure
Keys are field names (e.g., `users.count`, `orders.created_date`).
*   **Standard Query**: Keys are field names.
*   **Pivoted Query**: Keys are field names, but values are nested by Pivot Key.
*   **Merged Results**: Keys may be aliased (e.g., `q1_users.count`).

```javascript
[
  // Row 1
  {
    "users.count": {
      "value": 42,              // Raw value (Number, Date object)
      "rendered": "42",         // String representation
      "html": "<a>42</a>",      // HTML (if configured)
      "links": [ ... ]          // Drill links
    },
    "orders.status": {
      "value": "complete"
    }
  }
]
```

### Cell Object
| Property | Type | Description |
| :--- | :--- | :--- |
| `value` | `Any` | The raw value. Use this for math, logic, or charts. |
| `rendered` | `String` | The formatted string (e.g., "$1,234.50"). Use for labels. |
| `html` | `String` | (Optional) Sanitized HTML. **Priority** for display if present. |
| `links` | `Array` | Drill menu links. Pass to `LookerCharts.Utils.openDrillMenu`. |

---

## 2. Config (`config`)
A key-value map of the current visualization options (User selections).

**Type**: `Object<String, Any>`

```javascript
{
  "font_size": "small",
  "show_legend": true,
  "custom_color": "#FF0000"
}
```

*   **Defaults**: If a user hasn't set an option, it *might* be missing or use the default defined in your `options` object. Always check for existence.

---

## 3. Query Response (`queryResponse`)
Metadata about the query, fields, and pivots. Critical for generic visualizations that handle any dataset.

**Type**: `Object`

### Fields Structure
Located at `queryResponse.fields`.

```javascript
{
  "dimensions": [ ... ],       // Array of Field Definitions
  "measures": [ ... ],         // Array of Field Definitions
  "pivots": [ ... ],           // Array of Pivot Metadata
  "table_calculations": [ ... ],
  "measure_like": [ ... ]      // (Merged Results) Contains measures from all queries
}
```

### Field Definition
Describes a single dimension or measure.
```javascript
{
  "name": "users.count",
  "label": "Users Count",
  "label_short": "Count",
  "type": "count_distinct",
  "is_numeric": true,
  "value_format": "0.00"
}
```

### Pivots structure
Located at `queryResponse.pivots`. Use this to determine column headers in a pivoted table.
```javascript
[
  {
    "key": "complete",      // The key used in the Row Object
    "label": "Complete",    // Human readable label
    "sort_values": { ... }  // Sort metadata
  }
]
```

---

## 4. Details (`details`)
Contextual information about the current execution environment.

**Type**: `Object`

```javascript
{
  "print": false,            // True if generating a PDF/Screenshot
  "crossfilterEnabled": true // True if Cross-filtering is enabled on the dashboard
}
```

*   **`print`**: Use this to disable animations or interactions (like tooltips) that shouldn't appear in static exports.
