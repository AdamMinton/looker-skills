# Looker Custom Viz Deployment Guide

## 1. Production Deployment (Git Integration)

This is the most **robust** method for deploying custom visualizations. It avoids all CORS and HTTPS complexity by having Looker serve the files directly.

### Prerequisites
*   A Git repository connected to your Looker Project.
*   Your built visualization file (e.g., `dist/bundle.js`).

### Step A: Configure `.gitignore`
Ensure your `dist/` folder is **NOT** ignored. You want to verify this file into Git.

**.gitignore**:
```gitignore
node_modules
# dist/ is intentionally included
# dist/ 
```

### Step B: Create `manifest.lkml`
In the root of your project, create a list of your visualizations.

**manifest.lkml**:
```lkml
project_name: "my-custom-viz-project"

visualization: {
  id: "my_custom_viz_id"
  label: "My Friendly Label"
  file: "dist/bundle.js"
}
```

### Step C: Deploy
1.  Run `npm run build` to generate the latest bundle.
2.  Commit `dist/bundle.js` and `manifest.lkml`.
3.  Push to Git.
4.  In Looker, pull the changes. The visualization is now available project-wide.

---

## 2. Local Development (Live Reload)

For rapid iteration without committing every change, use a local server.

### Option A: Direct HTTPS (Recommended)
Looker requires HTTPS. Modern browsers also require "Public Network Access" headers.

1.  **Generate Certs**: Use `mkcert` (included in `init_project.py` setup).
    ```bash
    mkcert -install
    mkcert localhost
    ```
2.  **Start Server**:
    ```bash
    npm run dev
    ```
3.  **Configure Looker**:
    *   Go to **Admin > Visualizations > Add New**.
    *   **Main**: `https://localhost:8080/viz_bundle.js`
    *   **Ignore SSL Errors**: You might need to open the URL in a separate tab and click "Proceed" once.

### Option B: Local Tunnel (Bypass Firewalls)
If you are behind a strict corporate firewall that blocks `localhost` access from Looker.

1.  Start your dev server: `npm run dev`
2.  Start a tunnel:
    ```bash
    npx localtunnel --port 8080 --local-https --allow-invalid-cert
    ```
3.  Use the public URL (e.g., `https://funny-cat-99.loca.lt/viz_bundle.js`) in Looker.

---

## 3. Harness Development (Simulation)
**Best Practice**: Do 99% of your development here.

1.  Open `harness/builder.html` in Chrome.
2.  Load realistic data scenarios (see `fetch_scenario.py`).
3.  Modify code and refresh. No headers, no SSL, no Uploads required.
