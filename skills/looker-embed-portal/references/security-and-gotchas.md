# Security Guidelines & Troubleshooting Gotchas

This document compiles critical security rules, session management constraints, and browser compatibility issues encountered when building Looker embed portals.

---

## 1. Client IP & User Agent Binding

In Cookieless JWT embedding, Looker requires that the client's `User-Agent` and public `user_ip` match _exactly_ between the session acquisition call (backend) and the iframe load request (browser).

### Common Failure Scenarios:

- **403 Forbidden / Session Attach Failure**: If the client's IP changes (e.g., switching from Wi-Fi to cellular) during the session, Looker blocks token rotation.
- **Behind Reverse Proxies (Cloudflare/LB)**: If your backend server resolves `req.ip` directly, it might capture the Load Balancer's IP instead of the client's.
  - _Fix_: Configure your express server to trust proxies (`app.set('trust proxy', true)`) or have the client fetch its public IP from an external API (like `api.ipify.org`) and send it in the request payload.

---

## 2. Session Reference Token Lifetimes

Understanding the lifetimes of different tokens is crucial for writing robust token-rotation logic.

| Token Type                  | Lifetime (TTL)    | Role                                                                                        |
| :-------------------------- | :---------------- | :------------------------------------------------------------------------------------------ |
| **Authentication Token**    | **30 Seconds**    | Single-use token to initialize the iframe connection. Expired immediately upon consumption. |
| **Navigation Token**        | **10 Minutes**    | Authorizes iframe page changes (navigation). Must be rotated before expiration.             |
| **API Token**               | **10 Minutes**    | Authorizes Looker REST API calls. Must be rotated before expiration.                        |
| **Session Reference Token** | **1 to 24 Hours** | Long-lived token held by the host backend. Used to request fresh Nav/API tokens.            |

### Failure Gotcha:

If the user keeps the tab open but idle, and your frontend ceases calling the rotation endpoint, the `navigation_token` will expire. When the user returns and clicks a button, the iframe will crash or show a login screen.
_Recommendation_: Always run an background interval timer in the frontend to proactively rotate tokens every **8 minutes** if the window is active.

---

## 3. Iframe Sandboxing & Storage Limitations

Modern browser security models enforce strict boundaries on iframes.

### LocalStorage & SessionStorage Restrictions:

If Looker is hosted on a different domain than the host application, the iframe runs in a third-party context.

- Safari (ITP) and Chrome (3P Cookie Phase-out) block write access to `localStorage` and `sessionStorage` inside third-party iframes.
- Looker features that rely on browser storage for persistence (like preserving open folders in the LookML IDE embed or caching local query states) may fail or reset upon iframe remounting.
- _Solution_: Use **Scoped User Attributes** in Looker to persist state in Looker's database rather than the client's local browser storage.

---

## 4. Multi-Tenant User Mapping & Tab Sprawling

A critical vulnerability in embedded portals is session pollution across browser tabs.

> [!WARNING]
> **The Tab Sprawling Anti-Pattern**
> Do not allow a user to log into different accounts (or different tenants) in two separate tabs of the same browser instance if you are using cookie-based authentication.

### Why it Fails:

Browser cookies are shared across all tabs for a given domain. If a user opens **Tab A** authenticated as `user_1` and then opens **Tab B** authenticated as `user_2`, the cookie for `user_2` overrides the cookie for `user_1`. When the user returns to **Tab A** and runs a query, they will see data belonging to `user_2` (session hijacking).

### Safe Architecture Rules:

1. **Prefer Cookieless JWT (Option 4)**: Since it does not rely on shared browser cookies, token states are isolated to the specific iframe context of each tab.
2. **Explicit Tab Isolation**: If using Signed SSO, append a unique session identifier or tab ID to your page routing, and verify that the active user session on the backend matches the specific request.
3. **One-to-One Mapping**: Maintain a clean, immutable mapping between your host application's user ID and Looker's `external_user_id`. Never allow a host user to dynamically swap their Looker user ID context without a full page refresh and session cleanup.

---

## 5. Session Reference Token Caching Security

The `session_reference_token` returned during Looker cookieless session acquisition is a highly sensitive credential. Because it is long-lived (typically between 1 and 24 hours), exposing it directly to the client browser poses a significant security risk (e.g., credential theft via XSS or browser extension sniffing).

### The Risk
If an attacker obtains the `session_reference_token`, they can bypass your host application's authentication entirely and directly request fresh navigation and API tokens from Looker, gaining unauthorized access to the embedded analytics environment.

### Mitigation: Server-Side Caching
To protect this token, implement a server-side caching pattern in your backend proxy:
1. **Intercept on Acquisition**: When your backend calls Looker to acquire the embed session, it receives the `session_reference_token` alongside the shorter-lived navigation and API tokens.
2. **Cache Server-Side**: Store the `session_reference_token` in a secure server-side session, database, or fast key-value cache (like Redis), keyed by the user's active host-application session ID.
3. **Strip from Client Response**: Strip the `session_reference_token` from the response payload before sending it back to the client browser. The client only receives the short-lived tokens (e.g., navigation token, API token) needed to boot the iframe.
4. **Proxy Token Rotation**: When the client needs to rotate tokens, it calls your backend's token-rotation endpoint using its standard host application session cookie/token. Your backend looks up the cached `session_reference_token` and calls Looker's token-rotation API on the client's behalf.

---

## 6. Folder Access and External Group Namespaces

When embedding Looker's self-service features (like the Folder or Explore interfaces) for external users, they will not see any Shared Folders by default, even if they have the correct roles and models assigned.

### The Access Gap
Unlike standard users, embed users do not inherit default folder viewing rights. Instead, access control relies on **external group mapping namespaces**.

### Resolution Steps
1. **Declare External Groups**: During SSO auth URL generation or cookieless session acquisition, specify external group IDs (e.g. `external_group_id` or `group_ids` list parameter).
2. **Map Groups in Looker Folder UI**: Log into the Looker Admin panel as an Administrator, navigate to the target folders (e.g. Shared folders), select **Manage Access**, and map the external group names directly to folder permissions (e.g., View vs. Edit).
3. **Verify Namespace Match**: The group names used in the Looker folder UI must exactly match the group IDs passed from the backend authentication payload. If they do not match, the shared folders will remain completely invisible to the embed users.
