# SETU Government Intelligence Console — patched

Responsive React/Vite interface styled after the supplied government portal reference. This patch adds a **real Supabase email/password sign-in gate**, working text scaling, and a persistent dark theme.

## 1. Configure environment

Copy `.env.example` to `.env.local`, then set:

```dotenv
SETU_BACKEND_TARGET=http://127.0.0.1:8081
VITE_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=YOUR_PUBLIC_PUBLISHABLE_OR_ANON_KEY
VITE_SETU_API_URL=
```

Use the actual FastAPI port for `SETU_BACKEND_TARGET`. The Supabase URL and publishable/anon key are public client configuration; **never** place a service-role key or database password in frontend variables.

## 2. Start

```powershell
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Access control

- The protected dashboard is not rendered until a Supabase Auth session exists.
- The frontend sends the session access token as `Authorization: Bearer ...` to FastAPI.
- The backend remains the authority for role/profile authorization. A valid Supabase login alone does not guarantee a linked, approved SETU profile.
- Signing out clears the active UI session and returns to the sign-in screen.
- The frontend does not store manually pasted access tokens.
- Supabase Auth must have email/password sign-in enabled and staff accounts provisioned. Configure redirect/site URLs in Supabase if your project requires them.

## Accessibility controls

- `A+` increases overall UI scale; `A−` decreases it. Scale is bounded and saved locally.
- `Dark mode` / `Light mode` switches the theme and remembers the choice in local storage.
- Contrast toggle remains available.

## Build

```powershell
npm run build
```

## Notes

The Vite proxy forwards `/health`, `/api`, `/docs`, and `/openapi.json` to FastAPI. The semantic comparison endpoint may be unavailable if disabled in the backend. The graph view does not invent dependency edges that the API does not return.
