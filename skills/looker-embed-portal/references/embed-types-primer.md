# Looker Embed Types and URLs Primer

Looker supports embedding several types of content into external portals. This primer catalogs the available embed types, their iframe URL structures, the corresponding Looker Embed SDK methods, and links to official documentation.

---

## 1. Embedded Dashboards

Embedded Dashboards are the most common embed type, allowing you to embed multi-tile interactive dashboards with native filters and scheduling options.

- **Looker URL Structure**:
  ```
  /embed/dashboards/<dashboard_id>
  ```
  *(Note: Older instances may use `/embed/dashboards-next/<dashboard_id>`, but `/embed/dashboards/` is standard).*
- **Embed SDK Helper**:
  ```typescript
  import { getEmbedSDK } from "@looker/embed-sdk";

  getEmbedSDK().createDashboardWithId(dashboardId)
    .appendTo(containerRef)
    .build()
    .connect();
  ```
- **Official Documentation**: [Google Cloud Dashboards Embedding](https://cloud.google.com/looker/docs/embed-sdk)

---

## 2. Embedded Explores

Embedded Explores allow you to embed self-service query builders. This enables users to select dimensions and measures, run queries, and build their own visualizations.

- **Looker URL Structure**:
  ```
  /embed/explore/<model_name>/<explore_name>
  ```
- **Embed SDK Helper**:
  ```typescript
  import { getEmbedSDK } from "@looker/embed-sdk";

  getEmbedSDK().createExploreWithId(`${modelName}/${exploreName}`)
    .appendTo(containerRef)
    .build()
    .connect();
  ```
- **Official Documentation**: [Google Cloud Explores Embedding](https://cloud.google.com/looker/docs/embed-sdk)

---

## 3. Embedded Looks

Embedded Looks allow you to embed a single, saved Looker visualization and its underlying data table.

- **Looker URL Structure**:
  ```
  /embed/looks/<look_id>
  ```
- **Embed SDK Helper**:
  ```typescript
  import { getEmbedSDK } from "@looker/embed-sdk";

  getEmbedSDK().createLookWithId(lookId)
    .appendTo(containerRef)
    .build()
    .connect();
  ```
- **Official Documentation**: [Google Cloud Looks Embedding](https://cloud.google.com/looker/docs/embed-sdk)

---

## 4. Embedded Conversational Analytics

Embedded Conversational Analytics allows you to embed Looker's AI-powered natural language exploration interface (Conversations Hub or individual chat threads) where users can ask questions in plain English to generate query outputs.

- **Looker URL Structure**:
  - **Conversations Hub**: `/embed/conversations`
  - **Specific Thread**: `/embed/conversations/<conversation_id>`
- **Embed SDK Helper**:
  *(Note: There is no direct SDK helper method for conversations yet. You must initialize it using the generic URL method or by loading it via the active connection).*
  ```typescript
  import { getEmbedSDK } from "@looker/embed-sdk";

  // Option A: Initial Mount
  getEmbedSDK().createDashboardWithUrl(`https://<looker-domain>/embed/conversations`)
    .appendTo(containerRef)
    .build()
    .connect();

  // Option B: Hot-swap navigate on active connection
  connection.loadUrl(`/embed/conversations/${conversationId}`);
  ```
- **Official Documentation**: [Google Cloud Conversational Analytics Embedding](https://cloud.google.com/looker/docs/conversational-analytics-looker-embedding)

---

## 5. Common URL Parameters

All iframe URLs support standard parameters that can be appended to customize the embedding experience:

| Parameter | Type | Role |
| :--- | :--- | :--- |
| `theme` | String | Applies a specific CSS theme (e.g. `?theme=dark`). |
| `embed_domain` | String | Mandatory for postMessage security. Set to the parent application's host origin. |
| `sdk` | String | Set to `3` to enable modern Embed SDK messaging. |
| `ca_chat` | Boolean | Pass `false` on Dashboards to hide the Conversational Analytics floating chat button. |
| `f[field_name]` | String | Inject values into filters (e.g. `?f[users.state]=California`). |
