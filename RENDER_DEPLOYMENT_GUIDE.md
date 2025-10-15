# Deploying to Render - Complete Guide

## Prerequisites

- ✅ GitHub account with your repository pushed
- ✅ Render account (free tier available at https://render.com)
- ✅ Your Airtable Personal Access Token
- ✅ Your Airtable Base ID

## Files Prepared for Render

✅ **render.yaml** - Render configuration (Infrastructure as Code)
✅ **Procfile** - Process configuration for Gunicorn
✅ **requirements.txt** - Python dependencies (including gunicorn)
✅ **final_solution.py** - Production-ready Flask app

## Step-by-Step Deployment

### 1. Push Your Code to GitHub

```powershell
# Make sure all changes are committed
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Create a New Web Service on Render

1. Go to https://render.com and sign in
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository:
   - If first time: Click "Configure account" to authorize Render
   - Select your repository: `s6ft256/hse-weeky-statistics-form`

### 3. Configure the Web Service

Fill in these settings:

**Basic Settings:**
- **Name:** `hse-statistics-dashboard` (or any name you prefer)
- **Region:** Choose closest to your users (e.g., Oregon USA, Frankfurt EU)
- **Branch:** `main`
- **Runtime:** `Python 3`

**Build & Deploy:**
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn final_solution:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

**Plan:**
- Select **Free** (or paid plan if you need more resources)

### 4. Add Environment Variables

In the **Environment Variables** section, add these:

| Key | Value | Notes |
|-----|-------|-------|
| `PYTHON_VERSION` | `3.11.0` | Specify Python version |
| `AIRTABLE_TOKEN` | `<your_token_from_.env>` | Your token from .env |
| `AIRTABLE_BASE_ID` | `<your_base_id_from_.env>` | Your base ID from .env |

⚠️ **IMPORTANT:** Click the 🔒 icon next to each secret value to mark it as "secret" (hidden in logs)

### 5. Deploy

1. Click **"Create Web Service"** at the bottom
2. Render will:
   - Clone your repository
   - Install dependencies from requirements.txt
   - Start your app with gunicorn
   - Provide you with a URL like: `https://hse-statistics-dashboard.onrender.com`

### 6. Monitor Deployment

Watch the deployment logs in real-time:
- Look for `[+] Airtable client initialized`
- Look for successful Gunicorn startup
- First deploy takes 2-5 minutes

## Your App URL

After deployment, your app will be available at:
```
https://hse-statistics-dashboard.onrender.com
```
(Replace with your actual Render URL)

## Alternative: Using render.yaml (Blueprint)

If you prefer Infrastructure as Code:

1. In Render dashboard, click **"New +"** → **"Blueprint"**
2. Connect your repository
3. Render will automatically detect `render.yaml` and use those settings
4. You'll still need to add environment variables in the dashboard

## Testing Your Deployment

Once deployed, test these URLs:

1. **Dashboard:** `https://your-app.onrender.com/`
2. **Table View:** `https://your-app.onrender.com/table/2.MAIN%20REGISTER`
3. **Theme Toggle:** Click the theme button - should work instantly
4. **Add Record:** Click "+ Add" - modal should open and work

## Troubleshooting

### Issue: App Won't Start

**Check logs for:**
- `ModuleNotFoundError` → Missing dependency in requirements.txt
- `Airtable init error` → Environment variables not set correctly
- `Port already in use` → Should not happen on Render (they manage ports)

**Solutions:**
1. Verify all environment variables are set
2. Check that gunicorn is in requirements.txt
3. Ensure AIRTABLE_TOKEN has proper permissions

### Issue: SSL Errors with Airtable

The app already handles this with:
```python
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
```

### Issue: Theme Not Persisting

This is browser-side (localStorage) and should work fine. If issues:
- Clear browser cache
- Check browser console for errors
- Verify JavaScript is enabled

### Issue: Free Tier Sleeping

Render free tier:
- Sleeps after 15 minutes of inactivity
- Takes ~30 seconds to wake up on first request
- **Solution:** Upgrade to paid tier ($7/month) for always-on service

## Performance Optimization

### Production Settings

Current setup uses:
- **2 workers** - Good for free tier
- **120s timeout** - Handles slow Airtable API calls

For paid tier, you can increase in Procfile:
```
web: gunicorn final_solution:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120
```

### Database Caching (Future Enhancement)

Consider adding Redis for caching Airtable data:
- Reduces API calls
- Faster page loads
- Lower Airtable rate limits

## Security Checklist

✅ Environment variables stored securely on Render (not in code)
✅ `.env` file in `.gitignore` (never committed)
✅ HTTPS enabled by default on Render
✅ Secrets marked as "secret" in Render dashboard

## Monitoring & Maintenance

### View Logs
- Go to your service in Render dashboard
- Click **"Logs"** tab
- Real-time streaming logs

### Redeploy
- Push changes to GitHub
- Render auto-deploys on every push to `main`
- Or click **"Manual Deploy"** → **"Deploy latest commit"**

### Custom Domain (Optional)

To use your own domain:
1. In Render dashboard → **"Settings"** → **"Custom Domain"**
2. Add your domain (e.g., `hse.trojanconstruction.group`)
3. Update DNS records as instructed
4. Render provides free SSL certificate

## Costs

**Free Tier:**
- 750 hours/month (enough for one always-running service)
- App sleeps after 15 min inactivity
- 100 GB bandwidth/month
- ✅ Perfect for testing/development

**Paid Starter ($7/month):**
- Always on (no sleeping)
- More CPU/memory
- Priority support
- ✅ Recommended for production

## Next Steps After Deployment

1. ✅ Test all features on production URL
2. ✅ Share URL with team
3. ✅ Set up custom domain (if needed)
4. ✅ Configure monitoring/alerting
5. ✅ Plan for backups (Airtable handles data, but screenshot/export reports periodically)

## Support

- **Render Docs:** https://render.com/docs
- **Render Community:** https://community.render.com
- **This Project Issues:** Create GitHub issue in your repo

---

## Quick Reference Commands

```powershell
# Test locally before deploying
python final_solution.py

# Commit and push changes
git add .
git commit -m "Update deployment config"
git push origin main

# Render will auto-deploy after push
```

**Your deployment is ready! 🚀**
