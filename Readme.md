

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


## Deploy on Render

Option A: Native Python Service (recommended)
1) Push this repo to GitHub
2) In Render, create a new Web Service from repo
3) It will auto-detect `render.yaml` and configure:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4) Set env vars: `GEMINI_API_KEY` (required), and if using Supabase: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_BUCKET`
5) Deploy. Health check on `/health`.

Option B: Docker (if you prefer custom image)
- Add a Dockerfile and use Render Docker service. `.dockerignore` is included.
