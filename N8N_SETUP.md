# 🚀 N8n Self-Hosted Setup on Render

## Step 1: Create New Render Service

1. Go to: https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. **Don't connect GitHub** - we'll use Blueprint instead

## Step 2: Use Blueprint

1. Select **"Blueprint"** option
2. Repository: `mindfulyatraa/youtube-automation-bot`
3. Branch: `main`
4. Blueprint file: `n8n-render.yaml`

## Step 3: Set Environment Variables

In Render dashboard, add these:

### Required:
1. **`N8N_BASIC_AUTH_USER`**
   - Your n8n username (choose any)
   - Example: `admin`

2. **`N8N_BASIC_AUTH_PASSWORD`**
   - Your n8n password (choose strong password)
   - Example: `YourStrongPassword123`

### Optional (for YouTube automation):
3. **`CLIENT_SECRETS_JSON`**
   - Same as before (YouTube API credentials)

4. **`TOKEN_JSON`**
   - Same as before (YouTube OAuth token)

5. **`YOUTUBE_COOKIES`**
   - Same cookies you generated earlier

## Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait 5-10 minutes for deployment
3. You'll get a URL like: `https://n8n-automation.onrender.com`

## Step 5: Access N8n

1. Open the Render URL
2. Login with your username/password
3. You'll see n8n workflow editor!

## Step 6: Create YouTube Automation Workflow

I'll provide the workflow JSON after n8n is deployed.

---

## Important Notes

- **Persistent Storage:** Workflows are saved on disk (1GB)
- **24/7 Running:** Free tier may sleep after 15 min inactivity
- **Keep-Alive:** We'll add a cron job to ping it every 14 min
- **Timezone:** Set to Asia/Kolkata (IST)

---

## Next Steps After Deployment

1. Import YouTube automation workflow
2. Configure credentials
3. Test workflow
4. Setup schedule (8 AM & 8 PM)

**Ready to deploy? Push this to GitHub!** 🚀
