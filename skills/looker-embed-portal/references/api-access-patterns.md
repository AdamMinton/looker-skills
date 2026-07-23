# Looker REST API Access Patterns in Portals

Embedded analytics portals often need to query Looker's REST API to render custom visualizations, populate dropdown filters dynamically, or build headless analytics features. This primer explains the three primary patterns for routing API requests from an external portal, security implications, and session management.

---

## 1. Direct Client CORS (Embed as Me)

Under this pattern, the client browser authenticates directly with Looker using a user-scoped access token and executes requests directly from the client.

### Architecture Flow:
1. **SSO Sudo Login**: The host backend calls Looker's admin API `/api/4.0/users/login/{user_id}` (or using `sdk.login_user()`) to generate a temporary user access token.
2. **Deliver Token**: The host backend returns this user token to the client browser.
3. **CORS Request**: The client browser calls Looker's API endpoints directly (e.g. `https://your-looker-domain:19999/api/4.0/...`) using the token in the `Authorization: Bearer <token>` header.

### Key Considerations:
- **CORS Config**: You *must* add your host application's origin (e.g., `https://app.company.com`) to the Looker instance's CORS allowlist.
- **Exposure**: Since the access token is exposed to the browser, it must be short-lived.

### Official Documentation:
- [Looker API CORS Access Guide](https://cloud.google.com/looker/docs/api-cors)

---

## 2. Routed Backend Proxy (Cookieless JWT)

Under this pattern, the client browser never contacts the Looker API directly. Instead, it sends standard API requests to your application's backend server, which proxies them to Looker using the client's cookieless API token (`api_token`).

### Architecture Flow:
1. **Token Retrieval**: The client obtains a short-lived `api_token` (and `navigation_token`) during cookieless session initialization.
2. **API Request**: The client browser sends requests to your backend (e.g. `/api/looker-proxy`) and attaches the `api_token` in headers or payload.
3. **Proxy Execution**: Your backend extracts the `api_token`, executes the request to Looker's `/api/4.0/...` endpoint, and forwards the results back to the client.

### Key Considerations:
- **CORS Independent**: Looker's CORS settings do not need to be modified since the requests originate from your backend server.
- **Token Protection**: Highly secure, as the long-lived `session_reference_token` remains safely cached on your backend.

---

## 3. Sudo User Impersonation (Headless REST)

If the client browser does not hold any Looker API tokens (e.g. a headless portal using a Signed SSO model or background tasks running offline), the backend server can impersonate the user on-demand to fetch data.

### Architecture Flow:
1. **User Lookup**: The backend looks up the Looker user ID corresponding to the host user (using `sdk.user_for_credential("embed", external_user_id)`).
2. **Sudo SDK Client**: The backend initializes a Looker SDK client and calls `login_user(embed_user_id)` to log in as that user, inheriting all their Row-Level Security (RLS) and permissions.
3. **Query & Logout**: The backend executes the queries, retrieves the data, and **immediately calls `logout()`** to destroy the temporary user session.

### Key Considerations:
- > [!IMPORTANT]
  > **Clean Lifecycle Hook**: You must always call `logout()` (or wrap the SDK in a context manager) immediately after the API call completes. Failing to do so will leak active sessions, causing Looker to hit its concurrent embed user limits, which will block new users from logging in.

- [Looker API Sudo Impersonation Reference](https://developers.looker.com/api/explorer/4.0/methods/ApiAuth/login_user)
- [Looker API SDK Reference](https://cloud.google.com/looker/docs/api-sdk-support-policy)
