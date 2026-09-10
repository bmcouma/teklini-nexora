# Teklini Nexora — Frontend

React + TypeScript + Tailwind CSS operations dashboard for Teklini Nexora, built with Vite.

## Development

```bash
npm install
npm run dev
```

The dev server proxies `/api/*` to `http://localhost:8000` (see `vite.config.ts`), so the backend
must be running separately. See the repository root [SETUP.md](../SETUP.md) for full instructions.

## Build

```bash
npm run build
```

Outputs a production build to `dist/`, served by nginx in the Docker image
(`frontend/Dockerfile`, `frontend/nginx.conf`).

## Structure

```
src/
  components/   Shared UI: app shell, status/severity/risk badges
  pages/        Dashboard, New Incident, Investigation View
  lib/          API client
  types/        TypeScript types mirroring the backend's Pydantic models
```
