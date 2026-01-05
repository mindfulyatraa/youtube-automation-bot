# YouTube Viral Shorts Automation

Automated tool to find, download, edit, and upload viral shorts to YouTube.

## Features

### 1. ⏰ Scheduled Uploads
- Automatically uploads new clips every **10 hours** (default).
- Runs 24/7 in the background.
- Customizable interval via `UPLOAD_INTERVAL_HOURS` in `youtube_automation.py`.

### 2. 🔄 Smart Video Tracking
- **Duplicate Prevention**: Skips videos that have already been processed.
- **History Tracking**: Keeps a record of uploads in `upload_history.json`.
- Ensures fresh contents are always found.

### 3. 🎲 Search Query Rotation
- Rotates through 7 different search queries (e.g., "podcast highlights usa", "viral moments usa").
- Ensures content variety.
- Customizable via `SEARCH_QUERIES` list.

### 4. 📊 Two Modes
- **Mode 1: Automated (24/7)** ✨
  - Uploads every 10 hours automatically.
  - Runs in background.
- **Mode 2: Manual (One-time)**
  - Runs a single cycle immediately.
  - Best for testing.

---

## 🛠️ Setup Instructions

### 1. Install Dependencies
You need Python installed. Then run:
```bash
pip install -r requirements.txt
```
*Note: You also need `ffmpeg` installed and added to your system PATH.*

### 2. API Setup
- **YouTube Data API Key**: Replace `YOUR_YOUTUBE_API_KEY` in `youtube_automation.py`.
- **OAuth Credentials**: command `client_secrets.json` file in the same directory (downloaded from Google Cloud Console).

## ▶️ How to Run

```bash
python youtube_automation.py
```

You will be prompted to choose a mode:
```
Kaunsa mode chahiye?
1. Automated (har 10 ghante)
2. Manual (ek baar run)

Enter (1/2):
```
Choose `1` for 24/7 automation.

## ⚙️ Customization

Edit `youtube_automation.py` to change settings:

```python
UPLOAD_INTERVAL_HOURS = 10  # Interval in hours
CLIPS_PER_CYCLE = 1         # Clips per upload cycle
MIN_VIEWS_THRESHOLD = 100000  # Minimum views to consider viral
```

## 🎯 Best Practices

- **Background Execution**:
  - Windows: `pythonw youtube_automation.py`
  - Linux/Mac: `nohup python youtube_automation.py &`
- **Server Deployment**: Deploy on AWS/DigitalOcean for true 24/7 uptime.
- **Monitoring**: Check `upload_history.json` to see what has been uploaded.
