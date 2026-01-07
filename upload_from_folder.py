import schedule
import os
import time
import json
import random
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
    if not transcript or 'text' not in transcript:
        return None

    full_text = transcript['text'].strip()
    _, keywords = detect_viral_keywords(full_text)
    
    if keywords:
        main_keyword = keywords[0].title()
        templates = [
            f"🔥 {main_keyword}! #Shorts",
            f"This is {main_keyword} 😱 #Shorts",
            f"Wait for it... {main_keyword} 🔥",
            f"{main_keyword} Explained 🤯 #Shorts"
        ]
        title = random.choice(templates)
    else:
        words = full_text.split()
        if len(words) > 5:
            short_hook = ' '.join(words[:5]) + "..."
            title = f"🔥 {short_hook} #Shorts"
        else:
            title = "Must Watch! 😱 #Shorts"

    if len(title) > 90:
        title = title[:87] + "..."

    desc = f"""🔥 VIRAL SHORTS

{full_text[:100]}...

Subscribe for more!

#Shorts #Viral #Trending #Motivation #Facts
"""
    tags = ['shorts', 'viral', 'trending'] + (keywords[:5] if keywords else [])
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
    
    if not transcript:
        print("   ⚠️ Transcription failed/empty. Using defaults.")
        title = f"Must Watch! {filename} #Shorts"
        desc = "Viral Video! #Shorts"
        tags = ['shorts']
    else:
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
        print(f"   ❌ Error: {e}")

def main():
    print("🤖 LOCAL VIDEO SCHEDULER STARTED")
    print("="*50)
    print("✅ Monitoring 'local_videos' folder")
    print("✅ Schedule: 08:00 AM & 08:00 PM")
    print("✅ Status: WAITING for next slot...")
    print("="*50)

    # Schedule
    schedule.every().day.at("08:00").do(run_scheduled_upload)
    schedule.every().day.at("20:00").do(run_scheduled_upload)

    # Run once immediately ONLY if confirming (Optional, but user said "rok de" so maybe NOT run now)
    # The user said "jab mai bolunga tab on karna". So we should just start the scheduler and let it wait.
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
