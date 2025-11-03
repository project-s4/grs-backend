# Deployment Notes for Render

## Critical: Update Start Command

The Render service is currently configured with `./run.sh` as the start command, which uses a hardcoded port and won't work on Render.

**You MUST update the start command in the Render dashboard:**

1. Go to: https://dashboard.render.com/web/srv-d44ged4hg0os73cgdg10
2. Navigate to **Settings** → **Start Command**
3. Change from: `./run.sh`
4. Change to: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Alternatively, delete the start command field entirely and let Render use the `Procfile` automatically.

## Fixed Issues

1. ✅ Updated `pydantic` to 2.8.2 (has pre-built wheels, avoids Rust compilation)
2. ✅ Updated `SQLAlchemy` to 2.0.36 (compatible with Python 3.13)
3. ✅ Created `Procfile` with correct port binding
4. ✅ Created `render.yaml` for Blueprint deployments
5. ✅ Created `runtime.txt` for Python version specification

## Environment Variables Required

Set these in Render dashboard:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Application secret key
- `JWT_SECRET` - JWT token secret
- `GEMINI_API_KEY` - Gemini AI API key
- `SUPABASE_URL` - Supabase project URL (if using)
- `SUPABASE_ANON_KEY` - Supabase anonymous key (if using)

## After Deployment

1. Run database migrations via Render Shell:
   ```bash
   alembic upgrade head
   ```

2. Verify the service is running:
   - Health check: `https://grs-backend-l961.onrender.com/health`
   - API docs: `https://grs-backend-l961.onrender.com/docs`

## GitHub Actions Workflow

A GitHub Actions workflow has been set up to automatically trigger Render deployments on push to main.

**Workflow file:** `.github/workflows/deploy.yml`

**Deploy Hook:**
- URL: `https://api.render.com/deploy/srv-d44ged4hg0os73cgdg10?key=DDr_ziuaamw`
- **Note:** For better security, add `RENDER_DEPLOY_HOOK_KEY` as a GitHub secret in your repository settings (Settings → Secrets and variables → Actions)

The workflow will automatically trigger Render deployments when you push to the main branch.

