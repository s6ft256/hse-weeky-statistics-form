# Render Deployment Checklist

## ✅ Pre-Deployment (Completed)

- [x] Updated `render.yaml` with service configuration
- [x] Created `Procfile` with Gunicorn command
- [x] Added `gunicorn==21.2.0` to `requirements.txt`
- [x] Updated `final_solution.py` to use PORT environment variable
- [x] Verified `.gitignore` includes `.env` file
- [x] Created deployment documentation

## 📋 Deployment Steps

### 1. Push to GitHub

```powershell
# Check status
git status

# Add all changes
git add .

# Commit
git commit -m "Prepare for Render deployment - add production config"

# Push to GitHub
git push origin main
```

### 2. Sign Up / Login to Render

- Visit: https://render.com
- Sign up with GitHub (recommended) or email
- Authorize Render to access your GitHub repositories

### 3. Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Select repository: `s6ft256/hse-weeky-statistics-form`
3. Configure:

   ```yaml
   Name: hse-statistics-dashboard
   Region: Oregon (or closest to you)
   Branch: main
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn final_solution:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```

### 4. Add Environment Variables

Add these in the **Environment** section:

```
PYTHON_VERSION = 3.11.0
AIRTABLE_TOKEN = <your_token_from_.env_file>
AIRTABLE_BASE_ID = <your_base_id_from_.env_file>
```

⚠️ **Mark AIRTABLE_TOKEN as "secret"** (click the lock icon)

### 5. Deploy & Monitor

- Click **"Create Web Service"**
- Watch logs for:
  - `Installing dependencies...`
  - `[+] Airtable client initialized`
  - `Booting worker with pid: ...`
  - `Listening at: http://0.0.0.0:10000`

### 6. Test Your App

Once deployed, your app will be at:
```
https://hse-statistics-dashboard.onrender.com
```

Test these pages:
- [ ] Dashboard (/)
- [ ] Any table view
- [ ] Theme toggle (light/dark)
- [ ] Add record modal
- [ ] Inline editing

## 🔍 Verification Checklist

After deployment:

- [ ] App loads without errors
- [ ] Tables are listed on dashboard
- [ ] Can view records in any table
- [ ] Theme toggle works
- [ ] Can add new records
- [ ] Inline editing works
- [ ] All toolbar buttons respond
- [ ] Modals open and close properly

## 🐛 Troubleshooting

### App Won't Start

Check logs for these errors:

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'gunicorn'` | Verify gunicorn is in requirements.txt |
| `Airtable init error` | Check environment variables are set |
| `No such file or directory: 'final_solution.py'` | Check file name matches exactly |

### Environment Variable Issues

```bash
# In Render logs, you should see:
[+] Airtable client initialized

# If you see errors, verify:
# 1. AIRTABLE_TOKEN is set correctly
# 2. AIRTABLE_BASE_ID is set correctly
# 3. Token has proper permissions in Airtable
```

### Performance Issues

Free tier limitations:
- Sleeps after 15 min inactivity
- 512 MB RAM
- Shared CPU

**Solutions:**
- Upgrade to Starter ($7/month) for always-on
- Reduce workers in Procfile if memory issues
- Add caching layer (Redis) for better performance

## 🔄 Updates & Redeployment

Every time you push to GitHub `main` branch:
1. Render automatically detects changes
2. Rebuilds your app
3. Redeploys (takes 2-3 minutes)

**Manual deploy:**
- Go to your service in Render
- Click **"Manual Deploy"**
- Select **"Deploy latest commit"**

## 📊 Monitoring

### View Logs
- Dashboard → Your Service → **Logs** tab
- Real-time streaming
- Search/filter capabilities

### Metrics (Paid plans)
- CPU usage
- Memory usage
- Response times
- Error rates

## 🌐 Custom Domain (Optional)

To use your own domain:

1. **In Render:**
   - Settings → Custom Domain
   - Add: `hse.trojanconstruction.group`

2. **In Your DNS Provider:**
   - Add CNAME record:
     ```
     hse.trojanconstruction.group → hse-statistics-dashboard.onrender.com
     ```

3. **SSL Certificate:**
   - Render provides free auto-renewing SSL
   - Automatically enabled for custom domains

## 💰 Cost Breakdown

### Free Tier (Current)
- Cost: **$0/month**
- Pros: Good for testing
- Cons: Sleeps after 15 min, slower startup

### Starter Plan (Recommended)
- Cost: **$7/month**
- Pros: Always on, faster, more reliable
- Cons: Paid

### Professional Plan
- Cost: **$25/month**
- Pros: More resources, autoscaling, priority support
- Cons: More expensive

## 🎯 Next Steps

1. [ ] Complete deployment to Render
2. [ ] Test all functionality
3. [ ] Share URL with team
4. [ ] Consider upgrading to paid plan
5. [ ] Set up custom domain (optional)
6. [ ] Configure monitoring/alerts

## 📞 Support Resources

- **Render Docs:** https://render.com/docs/deploy-flask
- **Render Status:** https://status.render.com
- **Community:** https://community.render.com
- **Support:** support@render.com (paid plans get priority)

---

**Ready to deploy! Follow the steps above. 🚀**

Estimated deployment time: **5-10 minutes**
