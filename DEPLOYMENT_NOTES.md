# Deployment Notes for Render

## Critical: Update Build and Start Commands

The Render service needs to be updated with the correct commands:

### 1. Update Build Command (to force Python 3.12)

1. Go to: https://dashboard.render.com/web/srv-d44ged4hg0os73cgdg10
2. Navigate to **Settings** → **Build Command**
3. Change from: `pip install -r requirements.txt`
4. Change to: `bash build.sh`
   
   OR explicitly use Python 3.12:
   ```
   python3.12 -m pip install --upgrade pip && python3.12 -m pip install -r requirements.txt
   ```

### 2. Update Start Command

1. Go to: https://dashboard.render.com/web/srv-d44ged4hg0os73cgdg10
2. Navigate to **Settings** → **Start Command**
3. Change from: `./run.sh`
4. Change to: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Alternatively, delete the start command field entirely and let Render use the `Procfile` automatically.

## Fixed Issues

1. ✅ Updated `pydantic` to 2.8.2 (has pre-built wheels, avoids Rust compilation)
2. ✅ Updated `SQLAlchemy` to 2.0.36 (compatible with Python 3.13)
3. ✅ Updated `psycopg2-binary` to 2.9.10 (works with Python 3.12, may need Python 3.12)
4. ✅ Created `Procfile` with correct port binding
5. ✅ Created `render.yaml` for Blueprint deployments
6. ✅ Created `runtime.txt` for Python version specification (Python 3.12.10)
7. ✅ Created `build.sh` script to force Python 3.12 usage
8. ✅ Created `.python-version` file for pyenv support

## Python Version Note

If you encounter `undefined symbol: _PyInterpreterState_Get` errors with psycopg2, it means Render is using Python 3.13 but the package doesn't have wheels for it. 

**Solution:** Ensure Python 3.12 is used:
1. Go to Render Dashboard → Settings → Environment
2. Verify that `runtime.txt` is being respected (should show Python 3.12.10)
3. If not, you may need to manually set the Python version in the service settings

## Environment Variables Required

Set these in Render dashboard:
- `DATABASE_URL` - PostgreSQL connection string (Supabase format: `postgresql://postgres:PASSWORD@db.PROJECT_ID.supabase.co:5432/postgres?sslmode=require`)
- `SECRET_KEY` - Application secret key
- `JWT_SECRET` - JWT token secret
- `GEMINI_API_KEY` - Gemini AI API key
- `SUPABASE_URL` - Supabase project URL (if using)
- `SUPABASE_ANON_KEY` - Supabase anonymous key (if using)

### Database Connection Note

If you encounter "Network is unreachable" errors with Supabase, it may be due to IPv6 connectivity issues on Render. The code has been updated to:
- Add connection timeouts
- Prefer IPv4 connections
- Use connection pooling

**IMPORTANT:** If your `DATABASE_URL` hostname resolves only to IPv6 (which Render cannot connect to), you need to use Supabase's connection pooler or IPv4-enabled endpoint. 

**Solution:** In your Supabase dashboard:
1. Go to Settings → Database
2. Use the "Connection Pooler" connection string instead of the "Direct Connection" 
3. The pooler connection string should use an IPv4-enabled hostname

Alternatively, you can use Supabase's Transporter or set up IPv4 networking in Supabase.

If issues persist, verify your `DATABASE_URL` is correctly set in Render dashboard environment variables and that it uses an IPv4-compatible endpoint.

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

