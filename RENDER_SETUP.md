# 🚀 Render.com Setup Guide

## Step 1: Push Code to GitHub
```bash
git add .
git commit -m "Added Render.com configuration"
git push origin main
```

## Step 2: Create Render Account
1. Go to: https://render.com
2. Click **"Get Started"**
3. Sign up with **GitHub** (no credit card needed)

## Step 3: Connect Repository
1. After login, click **"New +"** → **"Cron Job"**
2. Connect your GitHub account (if not already connected)
3. Select repository: **`mindfulyatraa/youtube-automation-bot`**
4. Render will auto-detect `render.yaml` file

## Step 4: Add Environment Variables (Secrets)
Click **"Environment"** tab and add these:

### Required Secrets:
1. **`CLIENT_SECRETS_JSON`**
   - Value: Paste entire content of `client_secrets.json`
   
2. **`TOKEN_JSON`**
   - Value: Paste entire content of `token.json`

### Optional (if YouTube blocks IP):
3. **`YOUTUBE_COOKIES`**
   - Value: Paste content of `cookies.txt`

## Step 5: Deploy
1. Click **"Create Cron Job"**
2. Wait for first build to complete (2-3 minutes)
3. Check logs to verify success

## Step 6: Verify Schedule
- Cron will run automatically at:
  - **8:00 AM IST** (2:30 AM UTC)
  - **8:00 PM IST** (2:30 PM UTC)

## Troubleshooting

### If YouTube blocks download:
1. Generate fresh cookies from browser
2. Add to Render Environment Variables as `YOUTUBE_COOKIES`
3. Redeploy

### Check Logs:
- Go to Render Dashboard → Your Cron Job → "Logs"
- See real-time execution logs

### Manual Trigger:
- Click "Trigger Run" button in Render dashboard to test immediately

## 🎉 Done!
Your automation will run automatically twice daily without any manual intervention!
