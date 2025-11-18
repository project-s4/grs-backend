# Fix Database Password in Render

## Problem
The backend is failing to connect to Supabase database with error:
```
password authentication failed for user "postgres"
```

## Solution: Update DATABASE_URL in Render

### Step 1: Get Your Database Password

1. Go to Supabase Dashboard: https://supabase.com/dashboard/project/hwlngdpexkgbtrzatfox/settings/database
2. Scroll down to "Connection string"
3. Click on "Connection pooling" tab
4. Select "Session mode"
5. Copy the connection string - it should look like:
   ```
   postgres://postgres.hwlngdpexkgbtrzatfox:[YOUR_PASSWORD]@aws-1-ap-south-1.pooler.supabase.com:5432/postgres
   ```

**IMPORTANT:** Replace `[YOUR_PASSWORD]` with your actual database password. If you don't know your password:
- Scroll to "Database password" section in Supabase Dashboard
- Click "Reset database password" if needed
- Copy the new password

### Step 2: Update DATABASE_URL in Render

1. Go to Render Dashboard: https://dashboard.render.com/web/srv-d44ged4hg0os73cgdg10
2. Click on "Environment" in the left sidebar
3. Find the `DATABASE_URL` environment variable
4. Update it with the full connection string from Step 1
5. Make sure to:
   - Use `postgresql://` or `postgres://` protocol
   - Include `postgres.hwlngdpexkgbtrzatfox` as username (NOT just `postgres`)
   - Include your actual password
   - Use pooler URL: `aws-1-ap-south-1.pooler.supabase.com:5432`
   - Add `?sslmode=require` at the end

**Correct format:**
```
postgresql://postgres.hwlngdpexkgbtrzatfox:[YOUR_ACTUAL_PASSWORD]@aws-1-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require
```

### Step 3: Save and Deploy

1. Click "Save Changes" in Render
2. Render will automatically redeploy your service
3. Wait 2-3 minutes for deployment to complete
4. Test the registration form again

### Step 4: Verify Connection

After deployment, check the Render logs:
1. Go to: https://dashboard.render.com/web/srv-d44ged4hg0os73cgdg10
2. Click "Logs" tab
3. Look for: "✅ Final DATABASE_URL username: postgres.hwlngdpexkgbtrzatfox"
4. No more "password authentication failed" errors

## Common Mistakes

❌ **Wrong username format:**
- `postgres` → Should be `postgres.hwlngdpexkgbtrzatfox` for pooler
- `postgres@hwlngdpexkgbtrzatfox` → Wrong format

❌ **Wrong password:**
- Using OAuth client secret instead of database password
- Using old/expired password
- Missing special characters in password

❌ **Wrong URL format:**
- Using direct connection URL instead of pooler URL
- Missing `?sslmode=require` at the end
- Using `postgres://` without proper encoding for special chars

✅ **Correct format:**
```
postgresql://postgres.hwlngdpexkgbtrzatfox:[PASSWORD]@aws-1-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require
```

## After Fixing

Once the DATABASE_URL is correct:
1. Registration form will work
2. Users can create profiles after OAuth
3. Users will be redirected to their dashboard after registration

