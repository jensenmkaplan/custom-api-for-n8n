

## Deploy on Vercel

1) Install Vercel CLI and login:
```bash
npm i -g vercel
vercel login
```

2) Set env vars in Vercel (Dashboard or CLI):
- `GEMINI_API_KEY`
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_BUCKET` (if using Supabase)
- Optional: `DEFAULT_GEMINI_MODEL`, `DEFAULT_EMBEDDING_MODEL`

3) Deploy:
```bash
vercel --prod
```

- The app is exposed via `api/index.py` using Vercel Python runtime.
- CORS is enabled; restrict origins in `app/main.py` for production.
