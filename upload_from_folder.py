import os
import time
import json
import random
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Import necessary functions from the main automation script
# We rely on your existing logic for auth, transcription, and viral analysis
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
    print("Make sure both scripts are in the same folder.")
    exit(1)

# Configuration
LOCAL_VIDEO_FOLDER = "local_videos"
COMPLETED_FOLDER = os.path.join(LOCAL_VIDEO_FOLDER, "completed")
os.makedirs(LOCAL_VIDEO_FOLDER, exist_ok=True)
os.makedirs(COMPLETED_FOLDER, exist_ok=True)

def generate_seo_from_transcript(transcript):
    """
    Generates viral Title, Description, and Tags based on video transcription.
    """
    if not transcript or 'text' not in transcript:
        return None

    full_text = transcript['text'].strip()
    
    # 1. Generate Title
    # Extract keywords
    _, keywords = detect_viral_keywords(full_text)
    
    # Create a hook based on text or keywords
    if keywords:
        main_keyword = keywords[0].title()
        # Add some variety
        templates = [
            f"🔥 {main_keyword}! #Shorts",
            f"This is {main_keyword} 😱 #Shorts",
            f"Wait for it... {main_keyword} 🔥",
            f"{main_keyword} Explained 🤯 #Shorts"
        ]
        title = random.choice(templates)
    else:
        # Fallback if no specific viral keywords found
        words = full_text.split()
        if len(words) > 5:
            short_hook = ' '.join(words[:5]) + "..."
            title = f"🔥 {short_hook} #Shorts"
        else:
            title = "Must Watch! 😱 #Shorts"

    # Ensure title is not too long
    if len(title) > 90:
        title = title[:87] + "..."

    # 2. Generate Description
    desc = f"""🔥 VIRAL SHORTS

{full_text[:100]}...

Subscribe for more!

#Shorts #Viral #Trending #Motivation #Facts
"""

    # 3. Generate Tags
    base_tags = ['shorts', 'viral', 'trending', 'youtube shorts']
    derived_tags = keywords[:5] if keywords else []
    tags = base_tags + derived_tags

    return title, desc, tags

def upload_local_file(files, history):
    youtube = get_authenticated_service()

    for filename in files:
        if filename.lower().endswith(('.mp4', '.mov', '.mkv')):
            video_path = os.path.join(LOCAL_VIDEO_FOLDER, filename)
            
            # Check if already uploaded
            # We can use filename as a unique ID for local files if we want, 
            # or calculate a hash. For simplicity, let's track filenames in a separate list or 
            # just rely on them being moved to 'completed' folder.
            # But user might paste new files with same names? Unlikely for "500 videos".
            # Let's check history by filename just in case.
            if filename in history.get('uploaded_local_files', []):
                print(f"⏭️  Skipping {filename} (Already uploaded)")
                continue

            print(f"\n🎬 Processing: {filename}")

            # 1. Transcribe for SEO
            print("   🎧 Analyzing audio for SEO...")
            transcript = transcribe_video(video_path)
            
            if not transcript:
                print("   ⚠️ No audio/transcription found. Using generic metadata.")
                title = f"Amazing Video! 🔥 {filename} #Shorts"
                desc = "Watch this viral video! #Shorts"
                tags = ['shorts', 'viral']
            else:
                title, desc, tags = generate_seo_from_transcript(transcript)
                print(f"   📝 Generated Title: {title}")

            # 2. Upload
            print(f"   📤 Uploading to YouTube...")
            try:
                body = {
                    'snippet': {
                        'title': title,
                        'description': desc,
                        'tags': tags,
                        'categoryId': '24' # Entertainment
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

                print(f"   ✅ Uploaded! https://youtube.com/shorts/{response['id']}")

                # 3. Update History
                if 'uploaded_local_files' not in history:
                    history['uploaded_local_files'] = []
                history['uploaded_local_files'].append(filename)
                save_upload_history(history)

                # 4. Move to Completed
                try:
                    completed_path = os.path.join(COMPLETED_FOLDER, filename)
                    os.rename(video_path, completed_path)
                    print(f"   📂 Moved to {COMPLETED_FOLDER}")
                except Exception as e:
                    print(f"   ⚠️ Could not move file: {e}")

            except Exception as e:
                print(f"   ❌ Upload Failed: {e}")

def main():
    print("🚀 LOCAL VIDEO UPLOADER started...")
    print(f"📂 Scanning folder: {LOCAL_VIDEO_FOLDER}")
    
    files = [f for f in os.listdir(LOCAL_VIDEO_FOLDER) if os.path.isfile(os.path.join(LOCAL_VIDEO_FOLDER, f))]
    
    if not files:
        print("❌ No videos found! Please paste your .mp4 files into the 'local_videos' folder.")
        return

    print(f"found {len(files)} videos.")
    
    history = load_upload_history()
    upload_local_file(files, history)
    
    print("\n✅ All Done!")

if __name__ == "__main__":
    main()
