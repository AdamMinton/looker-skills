# Looker Embed Events & Interactivity (Bidirectional Communication)

This guide documents how to establish bidirectional communication between your host application and the embedded Looker iframe using the Looker Embed SDK.

---

## 1. Subscribing to Looker Events (`.on()`)

Use the `.on()` helper methods on the Looker Embed Builder to capture events emitted from inside the iframe.

```javascript
LookerEmbedSDK.createDashboardWithId(1)
  .appendTo("#embed-container")

  // 1. Dashboard Loaded
  .on("dashboard:loaded", (event) => {
    console.log("Dashboard Loaded:", event.dashboard);
    // You can inspect available filters, tiles, and dashboard layout
  })

  // 2. Query execution start & end (useful for loading spinners)
  .on("dashboard:run:start", () => {
    showLoadingSpinner(true);
  })
  .on("dashboard:run:complete", (event) => {
    showLoadingSpinner(false);
    console.log(`Query finished. Status: ${event.status}`);
  })

  // 3. Drill Menu Interception
  // Prevents Looker's default drill behavior to trigger host application logic
  .on("drillmenu:click", (event) => {
    console.log("Intercepted Drill Click:", event);

    // Check drill context to render a custom Modal in host app instead
    if (event.label === "View Customer Details") {
      openHostModal(`/customers/${event.context.value}`);

      // Prevent Looker from opening its default popover drill window
      return { preventDefault: true };
    }
  })

  // 4. Explore Runs (tracking exploratory activity)
  .on("explore:run", (event) => {
    trackUserActivity("explore_query_run", {
      model: event.explore.model,
      view: event.explore.view,
    });
  })

  .build()
  .connect();
```

### Critical Event Table:

| Event Name               | Source    | Description                                                          | Payload Attributes                          |
| :----------------------- | :-------- | :------------------------------------------------------------------- | :------------------------------------------ |
| `dashboard:loaded`       | Dashboard | Fired when dashboard configuration is parsed but before queries run. | `dashboard` metadata (filters, tiles).      |
| `dashboard:run:start`    | Dashboard | Fired when the dashboard begins querying.                            | None.                                       |
| `dashboard:run:complete` | Dashboard | Fired when all queries on the dashboard complete.                    | `status`, `errors` (if any).                |
| `drillmenu:click`        | Core      | Fired when a user clicks a drillable value.                          | `label`, `link`, `context` (field & value). |
| `explore:run`            | Explore   | Fired when a query runs inside an embedded Explore.                  | `explore` definition, `query` SQL.          |
| `page:changed`           | Core      | Fired when navigating sub-pages.                                     | `url`.                                      |

---

## 2. Sending Actions to Looker (`connection.send()`)

Once the connection is established, use the connection object to trigger actions inside the iframe.

```javascript
let activeConnection = null;

LookerEmbedSDK.createDashboardWithId(1)
  .appendTo("#embed-container")
  .build()
  .connect()
  .then((connection) => {
    activeConnection = connection;
  });

// 1. Update Dashboard Filters dynamically
function updateFilters(filtersObject) {
  if (!activeConnection) return;

  // Format: { "Filter Name": "value" }
  activeConnection.send("dashboard:filters:update", {
    filters: filtersObject,
  });

  // Note: dashboard:filters:update only sets the inputs; you must trigger dashboard:run to query
  activeConnection.send("dashboard:run");
}

// Example usage:
// updateFilters({ "State": "California, New York", "Date Range": "last 30 days" });

// 2. Modify Layout Options dynamically (e.g., Toggle Title bar)
function toggleDashboardHeader(showTitle) {
  if (!activeConnection) return;

  activeConnection.send("dashboard:options:set", {
    options: {
      layouts: [
        {
          show_title: showTitle,
        },
      ],
    },
  });
}

// 3. Dynamically set Theme
function updateDashboardTheme(themeName) {
  if (!activeConnection) return;

  activeConnection.send("dashboard:options:set", {
    options: {
      theme: themeName,
    },
  });
}
```

---

## 3. Dynamic Multi-Tenant Navigation

When navigating between dashboard views, you must ensure that user attribute restrictions (like `tenant_id` or `department_id`) are preserved and cannot be manipulated by the client.

### Secure Navigation Pattern:

1. **Never pass row-level security variables (like tenant IDs) via frontend filters**. Clients can modify JavaScript execution.
2. Always lock access controls into Looker **User Attributes** on the backend during session acquisition (`acquire_embed_cookieless_session` or SSO URL creation).
3. If navigating between dashboards, rely on the backend-negotiated session tokens to apply those user attributes automatically in the database queries.

```javascript
// Good Pattern: Clean ID swap. Looker handles access filters silently on the backend.
function viewDepartmentSales(dashboardId) {
  // The session token already contains the user's secure department_id user attribute.
  // Looker's LookML uses that attribute automatically.
  connection.loadDashboard(dashboardId);
}

// Bad Pattern: Exposing security filters to client manipulation.
function viewDepartmentSalesVulnerable(dashboardId, departmentId) {
  connection.loadDashboard(dashboardId);
  // VULNERABLE: Client could call this function and pass a different departmentId!
  connection.send("dashboard:filters:update", {
    filters: { "Department ID": departmentId },
  });
  connection.send("dashboard:run");
}
```
