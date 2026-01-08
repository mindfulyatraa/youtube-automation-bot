import schedule
import os
import time
import logging

# Configure logging
logging.basicConfig(
    filename='local_upload.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
import json
import random
import sys
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Import necessary functions from the main automation script
try:
    from youtube_automation import (
        get_authenticated_service, 
        transcribe_video, 
        detect_viral_keywords, 
        load_upload_history, 
        save_upload_history,
        UPLOAD_HISTORY_FILE
    )
except ImportError:
    print("❌ Critical: Could not import from youtube_automation.py")
    exit(1)

# Configuration
LOCAL_VIDEO_FOLDER = "local_videos"
COMPLETED_FOLDER = os.path.join(LOCAL_VIDEO_FOLDER, "completed")
os.makedirs(LOCAL_VIDEO_FOLDER, exist_ok=True)
os.makedirs(COMPLETED_FOLDER, exist_ok=True)

def generate_seo_from_transcript(transcript):
    # GENERIC FALLBACKS (If no transcript or no keywords)
    generic_titles = [
        "Wait for it... 😱 #Shorts",
        "You won't believe this 🔥 #Shorts",
        "Mind Blowing Facts 🤯 #Shorts",
        "Must Watch! ⚡ #Shorts",
        "Best Moment Ever 💯 #Shorts",
        "Did you know? 🤔 #Shorts",
        "Insane Moment! 💥 #Shorts"
    ]

    # Default to a random generic title first
    title = random.choice(generic_titles)
    desc_text = "Viral Video! Subscribe for more."
    tags = ['shorts', 'viral', 'trending']

    if transcript and 'text' in transcript:
        full_text = transcript['text'].strip()
        _, keywords = detect_viral_keywords(full_text)
        
        if keywords:
            main_keyword = keywords[0].title()
            templates = [
                f"🔥 {main_keyword}! #Shorts",
                f"This is {main_keyword} 😱 #Shorts",
                f"Wait for it... {main_keyword} 🔥",
                f"{main_keyword} Explained 🤯 #Shorts",
                f"Why {main_keyword}? 🤔 #Shorts"
            ]
            title = random.choice(templates)
            # Add specific tags from keywords
            tags = ['shorts', 'viral', 'trending'] + keywords[:10]
        
        if full_text:
            desc_text = full_text[:100] + "..."

    # Ensure title fits YouTube limit
    if len(title) > 95:
        title = title[:90] + "..."

    desc = f"""🔥 VIRAL SHORTS

{desc_text}

Subscribe for more!

#Shorts #Viral #Trending
"""
    return title, desc, tags

def run_scheduled_upload():
    print(f"\n⏰ Checking for local videos to upload - {datetime.now()}")
    
    # Scan folder
    files = [f for f in os.listdir(LOCAL_VIDEO_FOLDER) if os.path.isfile(os.path.join(LOCAL_VIDEO_FOLDER, f))]
    valid_files = [f for f in files if f.lower().endswith(('.mp4', '.mov', '.mkv'))]
    
    if not valid_files:
        print("❌ No videos found in 'local_videos' folder.")
        return

    # Process just ONE video per slot to match daily flow and being safe
    filename = valid_files[0]
    video_path = os.path.join(LOCAL_VIDEO_FOLDER, filename)
    
    history = load_upload_history()
    if filename in history.get('uploaded_local_files', []):
        print(f"⚠️ {filename} marked as uploaded in history but still in folder. Moving to completed.")
        try:
            os.rename(video_path, os.path.join(COMPLETED_FOLDER, filename))
        except: pass
        return

    print(f"🎬 Starting upload for: {filename}")

    # 1. Seo
    print("   🎧 Analying audio...")
    transcript = transcribe_video(video_path)
    
    # AI Title Generation (or Random Fallback) - NO Filenames
    title, desc, tags = generate_seo_from_transcript(transcript)

    # 2. Upload
    print(f"   📤 Uploading...")
    try:
        youtube = get_authenticated_service()
        body = {
            'snippet': {
                'title': title,
                'description': desc,
                'tags': tags,
                'categoryId': '24'
            },
            'status': {
                'privacyStatus': 'public', 
                'selfDeclaredMadeForKids': False
            }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"      🚀 {int(status.progress() * 100)}%")

        print(f"   ✅ Success! https://youtube.com/shorts/{response['id']}")

        # 3. Update History
        if 'uploaded_local_files' not in history:
            history['uploaded_local_files'] = []
        history['uploaded_local_files'].append(filename)
        save_upload_history(history)

        # 4. Move
        os.rename(video_path, os.path.join(COMPLETED_FOLDER, filename))
        print(f"   📂 Moved to completed folder.\n")
        
    except Exception as e:
        error_msg = f"Error in run_scheduled_upload: {str(e)}"
        print(f"   ❌ {error_msg}")
        logging.error(error_msg, exc_info=True)

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except: pass
    
    print("🤖 LOCAL VIDEO UPLOADER")
    print("="*50)
    print(f"📂 Folder: {LOCAL_VIDEO_FOLDER}")
    
    # Check for manual run
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        print("⚡ Manual Run Triggered! Uploading 1 video now...")
        run_scheduled_upload()
        print("\n✅ Manual run complete.")
        return

    print("✅ Schedule: 08:00 AM & 08:00 PM")
    print("✅ Status: WAITING for next slot...")
    print("="*50)

    # Schedule
    schedule.every().day.at("08:00").do(run_scheduled_upload)
    schedule.every().day.at("20:00").do(run_scheduled_upload)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
