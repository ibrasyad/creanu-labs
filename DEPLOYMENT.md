# Deployment Guide: Creanu Labs on Cloudflare Workers

Creanu Labs runs entirely client-side using in-browser WebAssembly and React. Cloudflare Workers serves the pre-compiled static assets with ultra-low latency across Cloudflare's global edge network at **zero server compute cost**.

---

## 1. Local Development

To run the application locally on your machine:

```powershell
cd web
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser. You can immediately edit configs in Visual Form or Monaco YAML mode, run simulations, view conversion funnels, and download CSV/ZIP packages!

---

## 2. Deploy via Wrangler CLI (1-Click Local Deploy)

If you have a Cloudflare account:

1. **Log in to Cloudflare from your terminal:**
   ```powershell
   cd web
   npx wrangler login
   ```
2. **Deploy directly to your Cloudflare Workers edge:**
   ```powershell
   npm run build
   npx wrangler deploy
   ```

Wrangler will upload `web/dist` and give you a public URL (e.g., `https://creanu-labs-simulator.<your-subdomain>.workers.dev`).

---

## 3. Automated CI/CD via GitHub Actions

The repository includes a ready-to-run GitHub Actions workflow at [deploy-cloudflare.yml](file:///d:/Windsurf/lettuce-melon/.github/workflows/deploy-cloudflare.yml).

To enable automatic deployment on every `git push`:

1. In your GitHub repository, go to **Settings > Secrets and variables > Actions**.
2. Add two repository secrets:
   - `CLOUDFLARE_API_TOKEN`: Your Cloudflare API token with **Edit Cloudflare Workers** permissions (created at [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens)).
   - `CLOUDFLARE_ACCOUNT_ID`: Your Cloudflare Account ID (found on your Workers dashboard sidebar).
3. Now, whenever you push changes to `main`, GitHub Actions will automatically build the React app and deploy it to Cloudflare!

---

## 4. Configuration Schema (`wrangler.jsonc`)

The Cloudflare configuration is located at [web/wrangler.jsonc](file:///d:/Windsurf/lettuce-melon/web/wrangler.jsonc):

```jsonc
{
  "$schema": "node_modules/wrangler/config-schema.json",
  "name": "creanu-labs-simulator",
  "compatibility_date": "2024-11-01",
  "assets": {
    "directory": "./dist",
    "binding": "ASSETS"
  }
}
```

This uses Cloudflare's **Static Assets on Workers** feature, combining lightning-fast asset delivery with the ability to add Cloudflare D1 database bindings in the future without changing infrastructure.
