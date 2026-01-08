# GitHub Actions Automation Setup

Since you cannot keep your laptop on 24/7, we have moved the automation to the cloud using **GitHub Actions**.

## 1. What will be automated?
The **Viral Podcast Automation** (`youtube_automation.py`) will now run automatically on GitHub servers:
- **Daily at 8:00 AM IST**
- **Daily at 8:00 PM IST**

> ⚠️ **Note:** The "Local Video Uploader" (`local_videos` folder) **cannot** run on GitHub Actions because those files are on your laptop. You must run `upload_from_folder.py` manually when you are using your laptop if you want to upload those files.

## 2. Setup Config (Important)
For the cloud automation to work, it needs your login credentials. You need to save them as "Secrets" in GitHub.

1.  Open `client_secrets.json` on your laptop, copy the **entire content**.
2.  Go to your GitHub Repo: **Settings** > **Secrets and variables** > **Actions**.
3.  Click **New repository secret**.
4.  **Name**: `CLIENT_SECRETS_JSON`
5.  **Secret**: Paste the content you copied.
6.  Click **Add secret**.

Repeat for `token.json`:
1.  Open `token.json` on your laptop, copy the **entire content**.
2.  Click **New repository secret** again.
3.  **Name**: `TOKEN_JSON`
4.  **Secret**: Paste the content.
5.  Click **Add secret**.

## 3. Activate
1.  Push the new code to GitHub:
    ```bash
    git add .
    git commit -m "Added GitHub Actions automation"
    git push origin main
    ```
2.  Go to the **Actions** tab in your GitHub repo.
3.  You will see "Daily YouTube Automation".
4.  You can wait for the schedule (8 AM/PM) OR run it manually by clicking "Run workflow" to test it immediately.
