# React (Vite) Embedding Patterns

This reference provides production-grade TypeScript patterns for integrating the Looker Embed SDK inside React 18+ applications built with Vite.

---

## 1. Custom React Hook: `useLookerEmbed`

This hook handles the initialization of the Looker SDK (supporting cookieless mode) and manages token generation callbacks within the React lifecycle.

### Key Lifecycle Patterns Demonstrated:

1. **React StrictMode Double-Initialization Guard**:
   In React StrictMode (specifically in development), components mount, unmount, and remount immediately. This causes `useEffect` hooks to fire twice. Since the Looker Embed SDK can only be initialized once per application lifecycle, calling `getEmbedSDK().initCookieless()` twice will throw a fatal error.
   We prevent this by declaring a module-scoped flag `let sdkInitialized = false;` outside the component/hook definition.
2. **Client IP Lookup Pattern**:
   Cookieless embedding binds tokens to the client's IP address for enhanced security (preventing session hijacking). The frontend must resolve the browser's public IP address (e.g., using a public service like `api.ipify.org`) and send it to the backend `acquire-embed-session` endpoint. The hook includes a resilient fallback structure if the public IP lookup fails (e.g., due to ad-blockers or corporate VPN proxy policies).

```typescript
// Module-scoped promise and token reference to track initialization and rotation safely
let sdkInitPromise: Promise<void> | null = null;
let activeApiToken = "";

interface UseLookerEmbedProps {
  lookerHost: string;
  externalUserId: string;
  userAttributes?: Record<string, any>;
}

export const useLookerEmbed = ({
  lookerHost,
  externalUserId,
  userAttributes = {},
}: UseLookerEmbedProps) => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Client IP lookup callback pattern
  const fetchPublicIp = useCallback(async (): Promise<string | null> => {
    try {
      const res = await fetch("https://api.ipify.org?format=json");
      if (!res.ok) return null;
      const data = await res.json();
      return data.ip || null;
    } catch (err) {
      console.warn("Public IP lookup failed, falling back to server-resolved IP.", err);
      return null;
    }
  }, []);

  useEffect(() => {
    let active = true;

    const init = async () => {
      try {
        const publicIp = await fetchPublicIp();
        if (!active) return;

        // Define session acquisition callback
        const acquireSession = async () => {
          const res = await fetch("/api/acquire-embed-session", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              user_ip: publicIp, // Bind session to resolved client IP
              external_user_id: externalUserId,
              user_attributes: userAttributes,
            }),
          });
          if (!res.ok) throw new Error("Session acquisition failed");
          const data = await res.json();
          
          // Store the active api_token for rotation lookup
          activeApiToken = data.api_token;
          return data;
        };

        // Define token rotation callback
        const generateTokens = async () => {
          const res = await fetch("/api/generate-embed-tokens", {
            method: "POST",
            headers: { 
              "Content-Type": "application/json",
              "Authorization": `Bearer ${activeApiToken}` // Pass active api_token to authenticate request
            }
          });
          if (!res.ok) throw new Error("Token rotation failed");
          const data = await res.json();
          
          // Update the active api_token
          activeApiToken = data.api_token;
          return data;
        };

        // Initialize SDK safely, caching the promise to guard against double-mounts
        if (!sdkInitPromise) {
          sdkInitPromise = getEmbedSDK().initCookieless(
            lookerHost,
            acquireSession,
            generateTokens,
          );
        }
        await sdkInitPromise;

        if (active) {
          setIsInitialized(true);
        }
      } catch (err: any) {
        // Revert promise on failure so initialization can be retried
        sdkInitPromise = null;
        if (active) {
          setError(err.message || "Failed to initialize Looker Cookieless SDK");
        }
      }
    };

    init();

    return () => {
      active = false;
    };
  }, [lookerHost, externalUserId, userAttributes, fetchPublicIp]);

  return { isInitialized, error };
};
```

---

## 2. Reusable Component: `LookerEmbedDashboard`

This component embeds a Looker dashboard into a DOM node using a `ref`. It safely handles cleanup, preventing duplicate iframes during React StrictMode double-renders.

```tsx
import React, { useEffect, useRef, useState } from "react";
import { getEmbedSDK } from "@looker/embed-sdk";

interface LookerEmbedDashboardProps {
  dashboardId: number | string;
  isSdkInitialized: boolean;
  onConnectionCreated?: (connection: any) => void;
}

export const LookerEmbedDashboard: React.FC<LookerEmbedDashboardProps> = ({
  dashboardId,
  isSdkInitialized,
  onConnectionCreated,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [height, setHeight] = useState("700px"); // Default fallback height

  useEffect(() => {
    if (!isSdkInitialized || !containerRef.current) return;

    let active = true;
    let embedConnection: any = null;

    // Clear container using textContent (safer than innerHTML, prevents XSS)
    containerRef.current.textContent = "";

    const buildEmbed = async () => {
      try {
        setLoading(true);
        setError(null);

        // Use getEmbedSDK() instead of the deprecated static class
        const builder = getEmbedSDK().createDashboardWithId(dashboardId)
          .appendTo(containerRef.current!)
          // Note: withClassName only accepts a SINGLE token class name. Space-separated classes will crash.
          .withClassName("looker-embed-iframe")
          // Add event listeners
          .on("dashboard:loaded", () => {
            if (active) setLoading(false);
          })
          .on("page:properties:changed", (event: any) => {
            if (active && event.height) {
              setHeight(`${event.height}px`); // Automatically resize outer height
            }
          })
          .on("dashboard:run:complete", () => {
            console.log("Dashboard query run complete.");
          });

        const embed = builder.build();
        if (!active) return;

        embedConnection = await embed.connect();

        if (!active) {
          if (containerRef.current) containerRef.current.textContent = "";
          return;
        }

        if (onConnectionCreated) {
          onConnectionCreated(embedConnection);
        }
      } catch (err: any) {
        if (active) {
          setError(err.message || "Failed to connect Looker embed");
          setLoading(false);
        }
      }
    };

    buildEmbed();

    // Cleanup: destroy iframe connection when component unmounts
    return () => {
      active = false;
      if (containerRef.current) {
        containerRef.current.textContent = "";
      }
    };
  }, [dashboardId, isSdkInitialized, onConnectionCreated]);

  return (
    <div style={{ position: "relative", width: "100%", height: height }}>
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 bg-opacity-75">
          <p>Loading Dashboard...</p>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 text-red-700 p-4">
          <p>Error: {error}</p>
        </div>
      )}
      <div ref={containerRef} style={{ width: "100%", height: "100%" }} />
    </div>
  );
};
```

---

## 3. Preloaded Connection Context Pattern

To avoid reload delays when navigating between different dashboards, preload the Looker connection in a global context and "hot-swap" views.

### Context Definition (`LookerEmbedContext.tsx`)

```tsx
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
} from "react";
import { useLookerEmbed } from "./useLookerEmbed";
import { getEmbedSDK } from "@looker/embed-sdk";

interface LookerContextType {
  connection: any | null;
  isInitialized: boolean;
  error: string | null;
}

const LookerContext = createContext<LookerContextType>({
  connection: null,
  isInitialized: false,
  error: null,
});

export const LookerEmbedProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { isInitialized, error } = useLookerEmbed({
    lookerHost: import.meta.env.VITE_LOOKER_HOST,
    externalUserId: "user_react_demo",
  });

  const [connection, setConnection] = useState<any | null>(null);
  const preloadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isInitialized || !preloadRef.current) return;

    getEmbedSDK().preload()
      .appendTo(preloadRef.current)
      .withClassName("looker-preload")
      .build()
      .connect()
      .then((conn: any) => {
        setConnection(conn);
        console.log("Global preloaded connection established.");
      })
      .catch((err: any) => console.error("Preload failed:", err));

    return () => {
      if (preloadRef.current) preloadRef.current.textContent = "";
    };
  }, [isInitialized]);

  return (
    <LookerContext.Provider value={{ connection, isInitialized, error }}>
      {children}
      {/* Hidden container for the preloaded iframe asset */}
      <div
        ref={preloadRef}
        style={{ width: 0, height: 0, opacity: 0, position: "absolute" }}
      />
    </LookerContext.Provider>
  );
};

export const useLookerContext = () => useContext(LookerContext);
```

### Navigating Component (`PortalView.tsx`)

```tsx
import React from "react";
import { useLookerContext } from "./LookerEmbedContext";

export const PortalView: React.FC = () => {
  const { connection, isInitialized } = useLookerContext();

  const handleNavigate = (dashboardId: string) => {
    if (connection) {
      connection
        .loadDashboard(dashboardId)
        .then(() => console.log(`Navigated to dashboard: ${dashboardId}`))
        .catch((err: any) => console.error(err));
    }
  };

  if (!isInitialized) return <p>Initializing Looker...</p>;

  return (
    <div>
      <div className="sidebar">
        <button onClick={() => handleNavigate("1")}>Marketing Stats</button>
        <button onClick={() => handleNavigate("2")}>Sales Overview</button>
      </div>
      <div className="content">
        {/* The active preloaded iframe is mounted and controlled globally */}
        <p>Select a dashboard to view report.</p>
      </div>
    </div>
  );
};
```

---

## 4. Gotchas & Troubleshooting

### Space-Separated Class Names Crash
The Looker Embed SDK's `.withClassName()` builder method delegates directly to the browser's native `Element.classList.add()` API.
Passing a string containing spaces (e.g. `.withClassName("w-full h-full")`) to specify multiple classes will cause a runtime crash:
`DOMException: Failed to execute 'add' on 'DOMTokenList': The token provided contains HTML space characters, which are not valid in tokens.`

**Solution**:
Always pass a single, unique class token to `.withClassName()`. If you need to apply multiple layout or styling overrides, define them in your global CSS stylesheet targeting that single token:
```css
/* index.css */
.looker-embed-iframe {
  width: 100% !important;
  height: 100% !important;
}
```
And apply it as a single token in the React component:
```typescript
getEmbedSDK().createDashboardWithId(id)
  .appendTo(containerRef.current)
  .withClassName("looker-embed-iframe")
```
