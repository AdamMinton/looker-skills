# Production Backend Implementation (Express & TypeScript)

This reference contains production-ready Node.js/Express controllers for handling Looker embed authentication, token rotation, and REST API proxying.

---

## 1. Looker SDK Initialization

Ensure you have `@looker/sdk-node` installed. The SDK automatically reads environment variables (e.g., `LOOKERSDK_BASE_URL`, `LOOKERSDK_CLIENT_ID`, `LOOKERSDK_CLIENT_SECRET`) when initialized.

```typescript
import { LookerNodeSDK, NodeSettings } from "@looker/sdk-node";

// Initialize settings from environment
const settings = new NodeSettings('LOOKERSDK');
export const lookerSdk = LookerNodeSDK.init40(settings);

// Verify connection on startup
lookerSdk
  .me()
  .then((user) =>
    console.log(`Connected to Looker as: ${user.value.display_name}`),
  )
  .catch((err) => console.error("Failed to connect to Looker SDK:", err));
```

---

## 2. Cookieless Session Acquisition (`/api/acquire-embed-session`)

This endpoint registers a new cookieless session. The client _must_ pass its public IP, and the server _must_ forward the client's `User-Agent`.

```typescript
import { Request, Response } from "express";
import { lookerSdk } from "./looker-config";

// Server-side cache mapping the active client api_token to the Looker session_reference_token.
// In production, use Redis or a secure database cache instead of an in-memory Map.
export const tokenCache = new Map<string, string>();

export const acquireEmbedSession = async (req: Request, res: Response) => {
  try {
    const { user_ip, external_user_id, user_attributes } = req.body;
    const user_agent = req.headers["user-agent"];

    if (!user_ip || !external_user_id) {
      return res
        .status(400)
        .json({ error: "Missing user_ip or external_user_id" });
    }

    if (!user_agent) {
      return res.status(400).json({ error: "Missing User-Agent header" });
    }

    // Define the session parameters
    const cookielessSessionRequest = {
      external_user_id,
      user_ip,
      user_agent,
      permissions: [
        "access_data",
        "see_user_dashboards",
        "see_lookml_dashboards",
        "see_looks",
        "explore",
      ],
      models: ["marketing_model"], // Replace with your model(s)
      user_attributes: {
        ...user_attributes,
      },
      session_length: 3600, // Session duration in seconds (1 hour)
      force_logout_login: true,
    };

    // Call Looker API to acquire tokens
    const response = await lookerSdk.ok(
      lookerSdk.acquire_embed_cookieless_session(cookielessSessionRequest, {
        headers: { "User-Agent": req.headers["user-agent"] || "" },
      }),
    );

    // Cache the long-lived session_reference_token server-side under the api_token key
    if (response.api_token && response.session_reference_token) {
      tokenCache.set(response.api_token, response.session_reference_token);
    }

    // CRITICAL: Strip the session_reference_token before sending to client
    const { session_reference_token, ...clientResponse } = response;

    return res.status(200).json(clientResponse);
  } catch (error: any) {
    console.error("Error acquiring cookieless session:", error);
    return res
      .status(500)
      .json({ error: error.message || "Internal Server Error" });
  }
};
```

---

## 3. Token Rotation Endpoint (`/api/generate-embed-tokens`)

The frontend Embed SDK will trigger a callback when the `navigation_token` or `api_token` is near expiration. The backend must exchange the client's current `api_token` for the cached `session_reference_token` and fetch fresh tokens.

```typescript
import { Request, Response } from "express";
import { lookerSdk } from "./looker-config";
import { tokenCache } from "./acquire-embed-session";

export const generateEmbedTokens = async (req: Request, res: Response) => {
  try {
    // Extract the client's current api_token from Authorization header
    const current_api_token = req.headers["authorization"]?.split(" ")[1];

    if (!current_api_token) {
      return res.status(400).json({ error: "Missing api_token for session lookup" });
    }

    // Retrieve the cached session_reference_token
    const session_reference_token = tokenCache.get(current_api_token);

    if (!session_reference_token) {
      return res.status(401).json({ error: "Session expired or invalid" });
    }

    // Exchange reference token for fresh navigation and API tokens
    const response = await lookerSdk.ok(
      lookerSdk.generate_tokens_for_cookieless_session(
        { session_reference_token },
        { headers: { "User-Agent": req.headers["user-agent"] || "" } },
      ),
    );

    // Update the cache with the new api_token
    tokenCache.delete(current_api_token);
    if (response.api_token) {
      tokenCache.set(response.api_token, session_reference_token);
    }

    // Response contains new api_token and navigation_token
    return res.status(200).json(response);
  } catch (error: any) {
    console.error("Error rotating tokens:", error);
    return res
      .status(500)
      .json({ error: error.message || "Internal Server Error" });
  }
};
```

---

## 4. Secure REST API Proxy (`/api/looker-proxy`)

When using Cookieless JWT, the frontend cannot call the Looker REST API directly due to CORS restrictions. The backend must act as a proxy. To preserve Looker user-session limits, we impersonate the user, execute the request, and immediately log out.

```typescript
import { Request, Response } from "express";
import { LookerNodeSDK } from "@looker/sdk-node";
import { lookerSdk } from "./looker-config";

export const lookerApiProxy = async (req: Request, res: Response) => {
  const { path, method, body, query } = req.body;
  const embedUserId = req.session?.lookerUserId; // Assuming you store Looker User ID in session

  if (!embedUserId) {
    return res
      .status(401)
      .json({ error: "Unauthorized: No active Looker session" });
  }

  // 1. Create a user-scoped SDK instance by login impersonation
  let userSdk: any;
  try {
    const token = await lookerSdk.ok(lookerSdk.login_user(embedUserId));

    // Initialize a new SDK client using the acquired user token
    userSdk = LookerNodeSDK.init40({
      baseUrl: process.env.LOOKERSDK_BASE_URL,
      headers: { Authorization: `Bearer ${token.access_token}` },
    } as any);
  } catch (authError) {
    console.error("Failed to impersonate user:", authError);
    return res.status(500).json({ error: "Authentication proxy failure" });
  }

  // 2. Execute the requested API call using the impersonated client
  try {
    let apiResponse;
    if (method === "GET") {
      apiResponse = await userSdk.ok(userSdk.get(path, query));
    } else if (method === "POST") {
      apiResponse = await userSdk.ok(userSdk.post(path, body));
    } else {
      return res.status(405).json({ error: "Method not supported by proxy" });
    }

    return res.status(200).json(apiResponse);
  } catch (apiError: any) {
    console.error(`Proxy API Error (${method} ${path}):`, apiError);
    return res
      .status(apiError.statusCode || 500)
      .json({ error: apiError.message });
  } finally {
    // 3. CRITICAL: Always logout the impersonated session immediately to free up Looker resources
    try {
      await userSdk.logout();
    } catch (logoutError) {
      console.warn("Failed to logout proxy session:", logoutError);
    }
  }
};
```

---

## 5. Signed SSO URL Generator Endpoints

If you choose to use Signed SSO, here are backend endpoints implementing both manual HMAC signing (Option 1) and Looker SDK signing (Option 2).

### Option A: Manual HMAC signing (Option 1)

```typescript
import crypto from "crypto";
import { Request, Response } from "express";

export const getSsoUrlNative = (req: Request, res: Response) => {
  const lookerHost =
    process.env.LOOKERSDK_BASE_URL?.replace("https://", "") || "";
  const secret = process.env.LOOKER_EMBED_SECRET || "";

  const { external_user_id, target_url } = req.body;
  const path = `/login/embed/${encodeURIComponent(target_url)}`;

  const nonce = crypto.randomBytes(16).toString("hex");
  const time = Math.floor(Date.now() / 1000).toString();
  const sessionLength = "3600";
  const permissions = JSON.stringify(["access_data", "see_user_dashboards"]);
  const models = JSON.stringify(["marketing_model"]);
  const groupIds = JSON.stringify([]);
  const userAttributes = JSON.stringify({ company: "Acme Co" });
  const forceLogoutLogin = "true";

  // Construct string to sign in exact newline order
  const stringToSign = [
    lookerHost,
    path,
    nonce,
    time,
    sessionLength,
    external_user_id,
    permissions,
    models,
    groupIds,
    "", // external_group_id (empty)
    userAttributes,
    forceLogoutLogin,
  ].join("\n");

  const signature = crypto
    .createHmac("sha1", secret)
    .update(stringToSign)
    .digest("hex");

  const queryParams = new URLSearchParams({
    nonce,
    time,
    session_length: sessionLength,
    external_user_id,
    permissions,
    models,
    group_ids: groupIds,
    user_attributes: userAttributes,
    force_logout_login: forceLogoutLogin,
    signature,
  });

  const finalUrl = `https://${lookerHost}${path}?${queryParams.toString()}`;
  res.status(200).json({ url: finalUrl });
};
```

### Option B: Looker SDK signing (Option 2)

```typescript
import { Request, Response } from "express";
import { lookerSdk } from "./looker-config";

export const getSsoUrlApi = async (req: Request, res: Response) => {
  try {
    const { external_user_id, target_url } = req.body;

    const ssoUrlResponse = await lookerSdk.ok(
      lookerSdk.create_sso_embed_url({
        target_url,
        external_user_id,
        permissions: ["access_data", "see_user_dashboards"],
        models: ["marketing_model"],
        user_attributes: { company: "Acme Co" },
        force_logout_login: true,
        session_length: 3600,
      }),
    );

    res.status(200).json({ url: ssoUrlResponse.url });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
};
```
