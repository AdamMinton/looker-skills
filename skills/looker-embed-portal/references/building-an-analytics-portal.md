# Tutorial: Building a Looker Analytics Portal from Scratch

This step-by-step guide walks you through setting up, coding, and running a secure, production-grade Looker Embedded Analytics portal using **React (Vite)** on the frontend and **Node.js (Express)** on the backend.

---

## 1. Project Directory Structure

Create a root directory for your project and divide it into `backend/` and `frontend/` services:

```
my-embed-portal/
├── backend/
│   ├── src/
│   │   ├── server.ts                  # Express App entry point
│   │   ├── looker-config.ts           # Looker SDK Initialization
│   │   └── controllers/
│   │       └── auth.ts                # Session Acquisition & Token Rotation
│   ├── package.json
│   └── tsconfig.json
└── frontend/
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx                    # Main App View
    │   ├── hooks/
    │   │   └── useLookerEmbed.ts      # Cookieless JWT Hook
    │   └── components/
    │       └── LookerEmbedDashboard.tsx # Iframe mounting component
    ├── package.json
    ├── vite.config.ts                 # Proxy configuration (avoid CORS)
    └── index.html
```

---

## 2. Step-by-Step Backend Setup

### Step 2.1: Initialize & Install Backend Dependencies
In `backend/`, initialize the node project and install the Looker Node SDK and Express:
```bash
cd backend
npm init -y
npm install express cors dotenv @looker/sdk-node
npm install --save-dev typescript ts-node-dev @types/express @types/cors @types/node
```

### Step 2.2: Configure Looker Credentials
Create a `.env` file in the root of the `backend/` directory:
```env
LOOKERSDK_BASE_URL=https://yourcompany.looker.com
LOOKERSDK_CLIENT_ID=your_client_id
LOOKERSDK_CLIENT_SECRET=your_client_secret
PORT=5000
```

### Step 2.3: Instantiate the Looker Node SDK
In `backend/src/looker-config.ts`, initialize the SDK:
```typescript
import { LookerNodeSDK } from "@looker/sdk-node";
export const lookerSdk = LookerNodeSDK.init40();
```

### Step 2.4: Implement Endpoints
Implement the Express controllers:
1. **Acquire Session (`/api/acquire-embed-session`)**: Hits the Looker API, receives the cookieless tokens, caches the long-lived `session_reference_token` (SRT) in a secure server-side cache (Map or Redis), and returns only the short-lived tokens to the client.
2. **Token Rotation (`/api/generate-embed-tokens`)**: Receives the client's current `api_token` via the `Authorization` header, looks up the cached SRT, requests fresh tokens from Looker, and updates the server-side cache mapping.

*(For full code, refer to [Backend Implementation](./backend-implementation.md)).*

---

## 3. Step-by-Step Frontend Setup

### Step 3.1: Initialize & Install Frontend Dependencies
In `frontend/`, scaffold a React + TypeScript app using Vite:
```bash
cd ../frontend
npm create vite@latest . -- --template react-ts
npm install @looker/embed-sdk
```

### Step 3.2: Configure Vite Proxy (Avoid CORS)
To avoid CORS issues during session acquisition, configure Vite to proxy requests starting with `/api` to the backend Express server running on port `5000`:
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  }
});
```

### Step 3.3: Implement the Cookieless Hook
Create `frontend/src/hooks/useLookerEmbed.ts` to manage the SDK initialization. The hook must:
* Query the user's public IP address (using `api.ipify.org`).
* Maintain the active `api_token` in memory and attach it as a Bearer token in the `Authorization` header during rotation calls.
* Use a **Promise-based guard** (`sdkInitPromise`) to prevent double-initialization bugs during React StrictMode mount cycles.

*(For full code, refer to [React & Vite Patterns](./react-vite-patterns.md#useLookerEmbed)).*

### Step 3.4: Implement the Dashboard Component
Create `frontend/src/components/LookerEmbedDashboard.tsx` to handle the iframe rendering:
* Use `getEmbedSDK().createDashboardWithId(id)` to mount the Looker frame.
* **Resizing**: Listen to the `page:properties:changed` event inside the iframe and dynamically adjust the height of the outer container wrapper.
* **Async Cleanup**: Implement checking the `active` flag after the connection promise resolves. If the component was unmounted during the connection handshake, clear `innerHTML` to prevent zombie/duplicate iframes.

*(For full code, refer to [React & Vite Patterns](./react-vite-patterns.md#LookerEmbedDashboard)).*

---

## 4. Configuring Looker Admin Settings

Before running the application, you must authorize your local portal origin inside your Looker instance:

1. Log into Looker as an **Administrator**.
2. Navigate to **Admin > Embed**.
3. In the **Embedded Domain Allowlist**, add your frontend's local development origin:
   ```
   http://localhost:3000
   ```
4. Click **Update** to save.

---

## 5. Running the Application

1. **Start the Backend**:
   ```bash
   cd backend
   npm run dev    # runs ts-node-dev watcher
   ```
2. **Start the Frontend**:
   ```bash
   cd ../frontend
   npm run dev    # runs Vite dev server on port 3000
   ```
3. Open **[http://localhost:3000](http://localhost:3000)** in your browser. The page will initialize a cookieless session and render the embedded dashboard.
