# Frontend

Minimal Next.js portal for the AI inference platform.

## Features

- Email/password signup and login through the FastAPI gateway.
- Use-case and model selection from the FastAPI gateway.
- Generic JSON model input and streamed response output.

## Run locally

1. Copy `.env.example` to `.env.local`.
2. Make sure FastAPI allows `http://localhost:3000` through CORS.
3. Run `npm install`, then `npm run dev`.
4. Open `http://localhost:3000` and create an account.

## Vercel variables

- `NEXT_PUBLIC_API_BASE_URL` — the public HTTPS URL of FastAPI

Add the Vercel origin to the API gateway CORS origins. If Vercel and the API use
unrelated domains, configure the API auth cookie with `Secure=true` and
`SameSite=none`. Prefer custom domains such as `app.example.com` and
`api.example.com` so both deployments are on the same site.
