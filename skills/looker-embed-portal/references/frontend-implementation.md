# Frontend Implementation (Vanilla JavaScript & Embed SDK)

This reference documents the vanilla HTML/JavaScript patterns for initializing the Looker Embed SDK, handling cookieless token lifecycles, preloading iframes, and routing API calls.

---

## 1. UMD Safe Resolution

When importing the Looker Embed SDK via a script tag or in certain bundling environments, resolve the SDK object safely:

```javascript
// Safe resolution helper for UMD/CDN packaging
const { getEmbedSDK } = window.LookerEmbedSDK || {};

if (!getEmbedSDK) {
  console.error("Looker Embed SDK failed to load from window context.");
}
```

---

## 2. Cookieless Initialization Callback Pattern

Cookieless embedding requires you to initialize the SDK with two callback functions: one to acquire the initial session, and one to refresh expired tokens. You must also fetch the client's public IP address before initialization.

```javascript
async function initLookerCookieless(
  lookerHost,
  externalUserId,
  userAttributes = {},
) {
  // 1. Fetch public IP (mandatory for User-IP binding in Looker)
  let publicIp = "";
  try {
    const ipResponse = await fetch("https://api.ipify.org?format=json");
    const ipData = await ipResponse.json();
    publicIp = ipData.ip;
  } catch (ipError) {
    console.error(
      "Failed to fetch public IP. Cookieless session may fail.",
      ipError,
    );
    return;
  }

  let activeApiToken = "";

  // 2. Define the Acquire Session Callback
  const acquireSessionCallback = async () => {
    const response = await fetch("/api/acquire-embed-session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_ip: publicIp,
        external_user_id: externalUserId,
        user_attributes: userAttributes,
      }),
    });
    if (!response.ok) throw new Error("Failed to acquire Looker session");
    const data = await response.json();
    
    // Store active api_token for rotation lookup
    activeApiToken = data.api_token;
    window.lookerApiToken = data.api_token;
    return data;
  };

  // 3. Define the Token Rotation Callback
  const generateTokensCallback = async () => {
    const response = await fetch("/api/generate-embed-tokens", {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${activeApiToken}` // Pass current api_token to authenticate
      }
    });
    if (!response.ok) throw new Error("Failed to rotate Looker tokens");
    const data = await response.json();

    // Cache the API token in frontend state if you plan to proxy API requests
    activeApiToken = data.api_token;
    window.lookerApiToken = data.api_token;

    return data; // Returns new api_token and navigation_token
  };

  // 4. Initialize the Cookieless SDK
  try {
    await getEmbedSDK().initCookieless(
      lookerHost,
      acquireSessionCallback,
      generateTokensCallback,
    );
    console.log("Looker Cookieless SDK initialized successfully.");
  } catch (err) {
    console.error("Looker SDK Cookieless initialization failed:", err);
  }
}
```

---

## 3. Unified Iframe Preload and Load Pattern

To achieve sub-second navigation between different Looker dashboards or views, avoid destroying and recreating the iframe. Instead, preload the Looker embedding assets once, and then use the SDK connection's dynamic load methods.

### Step 1: Preload Looker Assets on App Startup

Mount the Looker preload endpoint in a hidden container:

```javascript
let globalLookerConnection = null;

function preloadLookerFrame(lookerHost, containerElementId) {
  const container = document.getElementById(containerElementId);

  // Clear container to prevent duplicate mountings
  if (container) {
    container.textContent = "";
  }

  getEmbedSDK().preload()
    .appendTo(container)
    .withClassName("looker-preload-frame")
    // We style this frame to be 0x0 or hidden, but NOT display:none (which stops loading)
    .build()
    .connect()
    .then((connection) => {
      globalLookerConnection = connection;
      console.log("Looker iframe preloaded and connection established.");
    })
    .catch((error) => console.error("Preload connection failed:", error));
}
```

### Step 2: Dynamically Hot-Swap Embed Content

Use the active connection to load new dashboards, looks, or explores instantly:

```javascript
// Navigate to a new dashboard
function navigateToDashboard(dashboardId) {
  if (!globalLookerConnection) {
    console.warn("Looker connection not ready yet.");
    return;
  }

  // connection.loadDashboard() updates the existing iframe source
  globalLookerConnection
    .loadDashboard(dashboardId)
    .then(() => console.log(`Loaded dashboard: ${dashboardId}`))
    .catch((err) => console.error("Failed to load dashboard:", err));
}

// Navigate to an Explore interface
function navigateToExplore(modelName, exploreName) {
  if (!globalLookerConnection) return;

  globalLookerConnection
    .loadExplore(`${modelName}/${exploreName}`)
    .then(() => console.log(`Loaded explore: ${exploreName}`))
    .catch((err) => console.error("Failed to load explore:", err));
}

// Navigate to Conversational Analytics (Explore Chat)
function navigateToChat(conversationId) {
  if (!globalLookerConnection) return;

  const chatUrl = `/embed/conversations/${conversationId}`;
  globalLookerConnection
    .loadUrl(chatUrl)
    .then(() =>
      console.log(`Loaded conversational analytics chat: ${conversationId}`),
    )
    .catch((err) => console.error("Failed to load chat:", err));
}
```

---

## 4. REST API Routing Logic (CORS vs Backend Proxy)

If your frontend needs to fetch data from the Looker REST API, choose the routing method based on your authentication model:

### For Option 3 (Embed as Me - Direct Browser CORS)

Since the client has a user-scoped access token and Looker has CORS enabled, call the Looker API directly:

```javascript
async function callLookerApiDirect(apiPath, method = "GET", body = null) {
  const lookerHost = "company.looker.com"; // Your Looker instance host
  const userToken = window.lookerApiToken; // Acquired during Option 3 auth

  const options = {
    method,
    headers: {
      Authorization: `Bearer ${userToken}`,
      "Content-Type": "application/json",
    },
  };
  if (body) options.body = JSON.stringify(body);

  const response = await fetch(
    `https://${lookerHost}/api/4.0/${apiPath}`,
    options,
  );
  return await response.json();
}
```

### For Option 4 (Cookieless JWT - Routed via Backend Proxy)

To avoid CORS issues and protect tokens, route the request through your application's backend proxy:

```javascript
async function callLookerApiProxy(apiPath, method = "GET", body = null) {
  const options = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      path: apiPath,
      method,
      body,
    }),
  };

  const response = await fetch("/api/looker-proxy", options);
  return await response.json();
}
```
