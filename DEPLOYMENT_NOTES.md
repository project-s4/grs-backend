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

**IMPORTANT:** Supabase's direct connection (`db.*.supabase.co`) uses IPv6-only hostnames that Render cannot connect to. You **MUST** use Supabase's Connection Pooler (Supavisor) instead.

#### ✅ Solution: Use Supabase Connection Pooler

1. Go to: https://supabase.com/dashboard/project/hwlngdpexkgbtrzatfox
2. Click the **"Connect"** button at the top of the page
3. Look for **"Session pooler"** or **"Connection pooler"** connection string
4. For serverless/auto-scaling deployments (like Render), use the pooler connection string
5. Copy the **ENTIRE** connection string
6. Replace `[YOUR-PASSWORD]` with your actual database password
7. Update `DATABASE_URL` in Render with that connection string

**The connection string format should be:**

```
postgresql://postgres.hwlngdpexkgbtrzatfox:[PASSWORD]@aws-1-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require
```

**OR for transaction mode (port 6543):**

```
postgresql://postgres.hwlngdpexkgbtrzatfox:[PASSWORD]@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require
```

**Note:** If you don't see the "Connect" button, try:

- https://supabase.com/dashboard/project/hwlngdpexkgbtrzatfox/settings/database
- Look for "Connection string" or "Connection pooler" section in the database settings

**Key points:**

- ✅ Username must be `postgres.[PROJECT_REF]` (not just `postgres`)
- ✅ Hostname is `aws-1-ap-south-1.pooler.supabase.com` (not `db.*.supabase.co`)
- ✅ Port is `6543` for transaction mode (or `5432` for session mode)
- ✅ Protocol should be `postgresql://` (not `postgres://`)

**Code automatically handles:**

- ✅ Detects pooler URLs and uses `NullPool` to avoid double pooling
- ✅ Validates username format and provides helpful error messages
- ✅ Adds SSL requirements and connection timeouts
- ✅ URL-encodes credentials to handle special characters in passwords
- ✅ Disables prepared statements for transaction mode (port 6543) as required

## Solution: Set Up Render PgBouncer

Since Supabase's direct connection uses IPv6-only hostnames that Render cannot connect to, we'll use Render's PgBouncer to act as a connection pooler between your app and Supabase.

### Step 1: Create PgBouncer Private Service

1. Go to: https://dashboard.render.com
2. Click **New +** → **Private Service**
3. Configure the service:
   - **Name**: `grs-pgbouncer` (or any name you prefer)
   - **Environment**: **Docker**
   - **Docker Image**: `rendeross/pgbouncer:latest`
   - **Start Command**: Leave empty (Docker image handles this)

### Step 2: Configure PgBouncer Environment Variables

Set these environment variables for the PgBouncer service:

- **`DATABASE_URL`**: `postgresql://postgres:d5atb1Xe4QTUIB6z@db.hwlngdpexkgbtrzatfox.supabase.co:5432/postgres?sslmode=require`
  - This is the direct Supabase connection string (IPv6). PgBouncer will connect to it.
- **`POOL_MODE`**: `transaction`
  - Use transaction mode for serverless-friendly pooling
- **`SERVER_RESET_QUERY`**: `DISCARD ALL`
  - Required for transaction mode to properly reset connections
- **`MAX_CLIENT_CONN`**: `500`
  - Maximum number of client connections PgBouncer can handle
- **`DEFAULT_POOL_SIZE`**: `50`
  - Default pool size for database connections

### Step 3: Get PgBouncer Internal Hostname

After PgBouncer deploys:

1. Go to the PgBouncer service page
2. Find the **Internal Hostname** (e.g., `grs-pgbouncer-1234.onrender.com`)
3. Note the port (usually `5432`)

### Step 4: Update Web Service DATABASE_URL

Update your web service (`grs-backend`) environment variable:

1. Go to: https://dashboard.render.com/web/srv-d44ged4hg0os73cgdg10
2. Navigate to **Environment** → **Environment Variables**
3. Update **`DATABASE_URL`** to:
   ```
   postgresql://postgres:d5atb1Xe4QTUIB6z@[PGBOUNCER_INTERNAL_HOSTNAME]:5432/postgres?sslmode=require
   ```
   Replace `[PGBOUNCER_INTERNAL_HOSTNAME]` with the internal hostname from Step 3.

### Step 5: (Optional) Set Up Direct Connection for Migrations

If you need to run database migrations (which may require features not supported by transaction mode pooler):

1. Add a new environment variable **`MIGRATE_DATABASE_URL`** to your web service:

   ```
   postgresql://postgres:d5atb1Xe4QTUIB6z@db.hwlngdpexkgbtrzatfox.supabase.co:5432/postgres?sslmode=require
   ```

   This is the direct Supabase connection (bypasses PgBouncer).

2. Update your migration scripts to use `MIGRATE_DATABASE_URL` when available.

### How It Works

```
┌─────────────┐      IPv4      ┌──────────────┐      IPv6      ┌─────────────┐
│   Web App   │ ──────────────> │  PgBouncer   │ ──────────────> │  Supabase   │
│  (Render)   │                 │   (Render)   │                 │  Database   │
└─────────────┘                 └──────────────┘                 └─────────────┘
```

- Your web app connects to PgBouncer via IPv4 (works on Render)
- PgBouncer connects to Supabase via IPv6 (PgBouncer can handle this)
- PgBouncer pools connections, preventing connection limit issues

### Troubleshooting Database Connection Errors

#### Error: "Tenant or user not found"

This means your `DATABASE_URL` credentials are incorrect. Common causes:

1. **Wrong username format** - Pooler requires `postgres.[PROJECT_REF]`, not just `postgres`

   - ❌ Wrong: `postgresql://postgres:password@...`
   - ✅ Correct: `postgresql://postgres.hwlngdpexkgbtrzatfox:password@...`

2. **Wrong password** - Get the correct password from Supabase Dashboard → Settings → Database

3. **Wrong hostname** - Must use pooler hostname, not direct connection

   - ❌ Wrong: `db.hwlngdpexkgbtrzatfox.supabase.co`
   - ✅ Correct: `aws-1-ap-south-1.pooler.supabase.com`

4. **Connection pooling conflict** - Code automatically uses `NullPool` for pooler connections (fixed in code)

#### Error: "Network is unreachable"

This means you're using the direct connection URL (`db.*.supabase.co`) which only resolves to IPv6.
**Solution:** Use the pooler URL from Supabase Dashboard (see above).

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
