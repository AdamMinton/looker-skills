---
name: looker-embed-portal
description: >-
  Guide for building secure, production-grade external analytics portals using Looker Embedded Analytics. Covers architecture options (Signed SSO, Cookieless JWT, Embed as Me), React/Vite integration, event handling, and security best practices.
---

# Looker Embed Portal Skill

This skill guides you through building secure, production-grade external-facing analytics portals using Looker Embedded Analytics. It covers the core embedding architectures, backend and frontend implementation patterns, React/Vite integration, event interactivity, and critical security considerations.

---

## 1. Architecture Options Overview

Looker offers several ways to embed dashboards, looks, and explores into external applications. Choosing the right method depends on your authentication model, need for third-party cookies, and API access requirements.

| Method                                 | User Provisioning         | 3P Cookies Required? | REST API CORS Access?     | Best For                                                                   |
| :------------------------------------- | :------------------------ | :------------------- | :------------------------ | :------------------------------------------------------------------------- |
| **Option 1: Signed SSO (Native HMAC)** | On-the-fly (just-in-time) | Yes                  | No                        | Simple embeds, legacy setups, environments where 3P cookies are allowed.   |
| **Option 2: Signed SSO (SDK)**         | On-the-fly (just-in-time) | Yes                  | No                        | Similar to Option 1, but easier implementation using Looker SDK.           |
| **Option 3: Embed as Me (CORS API)**   | Ahead-of-time (AOT)       | No                   | Yes (Direct from browser) | High interactivity, heavy use of Looker REST API from frontend.            |
| **Option 4: Cookieless JWT**           | Server-managed session    | No                   | Yes (via Backend Proxy)   | Modern web apps, strict privacy settings (Safari/Chrome block 3P cookies). |

For a detailed breakdown of each option, see [Architecture Options Reference](./references/architecture-options.md).

---

## 2. The Third-Party Cookie Problem

Modern browsers (Safari, Firefox, and increasingly Chrome) block third-party cookies by default. Traditional Looker embedding (Signed SSO) relies on cookies set by the Looker instance inside the iframe. If Looker is hosted on a different domain than your parent application (e.g., `analytics.company.com` embedding `company.looker.com`), the browser will block these cookies, resulting in login loops or blank iframes.

### Solutions:

1. **Custom Domain (CNAME)**: Map your Looker instance to a subdomain of your main application (e.g., `looker.company.com` embedded in `app.company.com`). This makes Looker cookies "first-party".
2. **Cookieless JWT (Option 4)**: The recommended modern solution. It replaces cookie-based sessions with token-based authentication managed via postMessage and a backend proxy.

---

## 3. Workflow Guide for Developers

When implementing a Looker embed portal, follow these steps:

### Step 1: Define Architecture & Tradeoffs

Before writing any code or generating scaffolding templates, you **MUST** engage the user in a tradeoff review. Present these key architectural decisions to the user (preferably using a structured multiple-choice list or conversational checklist) to align on the project requirements:

1. **Embedding Option (SSO vs. Cookieless JWT)**:
   * *Signed SSO*: Simplest implementation. Highly compatible with existing apps, but **requires third-party cookies** to be enabled in the browser (will fail on Safari ITP and modern Chrome setups unless using a mapped CNAME custom subdomain).
   * *Cookieless JWT*: Modern, token-based session model. **Does not require third-party cookies**, but requires the host backend to implement session acquisition and token rotation endpoints.

2. **Iframe Lifecycle (Iframe Recreation vs. Preloaded Reuse)**:
   * *Recreation*: Tearing down and recreating the `<iframe>` element on every dashboard transition. Simple to code but causes visible page flickers and slower load times (1–3 seconds per transition).
   * *Preload & Hot-swap*: Mounting a single preloaded iframe context on startup and using `connection.loadDashboard(id)` or `connection.loadUrl(path)` to instantly navigate. Eliminates reload lag but requires React context/global state management.

> [!IMPORTANT]
> **Mandatory Security Rule for Cookieless JWT**:
> The `session_reference_token` (SRT) returned during Looker cookieless session acquisition acts as a master refresh credential. To prevent session hijacking, your backend proxy **MUST** cache the SRT in a secure server-side store (e.g., Redis) and **never** return it to the client browser. During rotation, the client must authenticate via its active `api_token` or first-party session cookie.

### Interactive Prerequisites Verification
Before proceeding, you **MUST** verify the following prerequisites by asking the user directly:
1. **Target Instance Details**: Ask for their Looker host domain name (e.g., `company.looker.com`) and the ID of a test dashboard they wish to embed.
2. **API Credentials**: Confirm they have API client ID and client secret credentials configured (e.g., in a `looker.ini` file in the workspace or environment variables).
3. **Domain Allowlist Authorization**: Remind the user that they **must** log into Looker as an Admin and add the local development domain (typically `http://localhost:3000`) to **Admin > Embed > Embedded Domain Allowlist**. Prompt them to confirm when this is completed before starting the development server.

Discuss and align on these preferences and prerequisites with the user before writing any code.

---

### Step 2: Implement Backend Authentication

- Set up an API-only Service Account with appropriate permissions.
- Implement the authentication endpoints (e.g., `/api/acquire-embed-session` for Cookieless, `/api/sso-url` for Signed SSO).
- Refer to [Backend Implementation](./references/backend-implementation.md) for Node.js/Express templates.

### Step 3: Implement Frontend Embedding

- Install the Looker Embed SDK (`@looker/embed-sdk`).
- Implement UMD-safe loading and initialization.
- Configure cookieless callback handlers if using Option 4.
- Refer to [Frontend Implementation](./references/frontend-implementation.md) for vanilla JS patterns.

### Step 4: Integrate with React/Vite (Optional)

- Wrap the embed container in a React component.
- Manage lifecycle, loading states, and error boundaries.
- Implement iframe preloading and connection reuse for sub-second navigation.
- Refer to [React & Vite Patterns](./references/react-vite-patterns.md).

### Step 5: Add Interactivity

- Listen to iframe events (loaded, run start/complete, drills).
- Send actions to the iframe (update filters, trigger runs, change layout).
- Refer to [Embed Events & Interactivity](./references/embed-events-and-interactivity.md).

---

## 4. References & Scaffolding

- **Step-by-Step Setup Guide**: [building-an-analytics-portal.md](./references/building-an-analytics-portal.md)
- **Architecture Options**: [architecture-options.md](./references/architecture-options.md)
- **Backend Implementation**: [backend-implementation.md](./references/backend-implementation.md)
- **Frontend Implementation**: [frontend-implementation.md](./references/frontend-implementation.md)
- **React/Vite Patterns**: [react-vite-patterns.md](./references/react-vite-patterns.md)
- **Events & Interactivity**: [embed-events-and-interactivity.md](./references/embed-events-and-interactivity.md)
- **Security & Gotchas**: [security-and-gotchas.md](./references/security-and-gotchas.md)
- **Conversational Analytics**: [conversational-analytics.md](./references/conversational-analytics.md)
- **Embed Types Primer**: [embed-types-primer.md](./references/embed-types-primer.md)
- **API Access Patterns**: [api-access-patterns.md](./references/api-access-patterns.md)

---


## 5. Official Google Cloud References

For further details, consult the official Looker documentation:

- **Cookieless Embedding**: [Google Cloud Cookieless Embed Documentation](https://cloud.google.com/looker/docs/cookieless-embed)
- **Signed SSO Embedding**: [Google Cloud Signed Embedding Documentation](https://cloud.google.com/looker/docs/signed-embedding)
- **Embed SDK Introduction**: [Google Cloud Embed SDK Introduction](https://cloud.google.com/looker/docs/embed-sdk-intro)
- **Embedded JavaScript Events**: [Google Cloud Embedded JavaScript Events Reference](https://cloud.google.com/looker/docs/embedded-javascript-events)
- **Embedding Conversational Analytics**: [Google Cloud Embedding Conversational Analytics Reference](https://cloud.google.com/looker/docs/conversational-analytics-looker-embedding)
