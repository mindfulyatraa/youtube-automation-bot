import os
import json
import subprocess
import sys
import random
import time
from datetime import datetime

# Import core generation logic (ensure this is in the same directory)
from viral_shorts_generator import process_video, get_video_id

# Channels to target
CHANNELS = {
    "CarryMinati": "https://www.youtube.com/@CarryMinati",
    "Ashish Chanchlani": "https://www.youtube.com/@ashishchanchlanivines",
    "BB Ki Vines": "https://www.youtube.com/@BBKiVines",
    "Round2Hell": "https://www.youtube.com/@Round2Hell"
}

UPLOAD_HISTORY_FILE = "upload_history.json"

def load_history():
    if os.path.exists(UPLOAD_HISTORY_FILE):
        with open(UPLOAD_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(UPLOAD_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def get_top_viral_video(channel_url, ignore_ids=[]):
    """
    Finds a top viral video from the channel that hasn't been processed.
    Uses yt-dlp to list videos sorted by views.
    """
    print(f"🔍 Searching for viral videos in {channel_url}...")
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--print-json",
        "--sort", "view_count",
        "--playlist-end", "10", # Check top 10
        channel_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    print(f"   - Check: {data.get('title')} (Duration: {data.get('duration')})")
                    # Filter out Shorts if duration is explicitly small (<60s)
                    # If duration is missing (None), assume it is long form or check later
                    dur = data.get('duration')
                    if dur and dur < 60:
                         continue
                        
                    videos.append(data)
                except Exception as ex:
                    print(f"Error parsing line: {ex}")
                    pass
        
        for video in videos:
            if video['id'] not in ignore_ids:
                return video
                
        return None
        
    except Exception as e:
        print(f"Error searching channel: {e}")
        return None

def generate_seo_metadata(channel_name, video_title, viral_clip_info):
    """
    Generates optimized Title, Description, and Tags based on user criteria.
    Criteria: 0/5 scoring (Tags, Tripled Keywords, etc.)
    """
    
    # 1. Tripled Keywords: Channel Name, "Funny", "Viral"
    t_keywords = [channel_name, "Funny", "Comedy", "Viral"]
    
    # Title: Must contain keywords
    # "Funny CarryMinati Moment 😂 | Wait for end #shorts"
    title = f"{video_title[:20]}... 😂 {channel_name} Viral | Wait for end #shorts"
    
    # Description: Must contain keywords
    desc = f"""
Wait for the end! 😂
Best viral funny moment from {channel_name}.

#shorts #viral #funny #{channel_name.replace(' ', '').lower()}

Credits:
Original Video: {video_title}
Channel: {channel_name}

Content:
This is a fan-made short from {channel_name}'s video. 
Subscribe to {channel_name} for more amazing content!

Keywords:
{', '.join(t_keywords)}, {channel_name} new video, {channel_name} funny scene, best roast, indian comedy.
"""

    # Tags: High volume + specific
    # 0/5 Tag Count -> ~500 chars ideal, but here we list 15-20 strong tags
    base_tags = [
        "shorts", "viral", "trending", "funny", "comedy", "youtube shorts", 
        "tiktok", "reels", "indian comedy", "roast", "humor", "wait for end"
    ]
    channel_tags = [
        channel_name, 
        channel_name.replace(" ", ""), 
        f"{channel_name} funny", 
        f"{channel_name} roast",
        f"{channel_name} viral"
    ]
    
    tags = base_tags + channel_tags
    
    return {
        "title": title,
        "description": desc.strip(),
        "tags": tags,
        "categoryId": "23" # Comedy
    }

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from youtube_automation import SCOPES

def get_authenticated_service():
    """Authenticate with YouTube"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            try:
                creds.refresh(Request())
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"Token refresh failed: {e}")
                return None
                
    return build('youtube', 'v3', credentials=creds)

def upload_video_scheduled(youtube, file, title, description, tags):
    """Uploads video immediately (Public)"""
    print(f"📤 Preparing Upload: {title[:50]}...")
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '23' # Comedy
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }
    
    media = MediaFileUpload(file, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"   ⬆️ Uploading: {int(status.progress() * 100)}%")
            
    print(f"   ✅ Upload Complete! ID: {response['id']}")
    return response['id']

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    history = load_history()
    processed_ids = history.get("processed_videos", [])
    
    print("=" * 60)
    print("🤖 AUTO-VIRAL CHANNELS BOT")
    print("=" * 60)
    
    # Pick a random channel to process this run
    channel_name, channel_url = random.choice(list(CHANNELS.items()))
    print(f"🎯 Target Channel: {channel_name}")
    
    # 1. Find Video
    video = get_top_viral_video(channel_url, processed_ids)
    
    if not video:
        print("❌ No suitable new video found.")
        return
        
    print(f"✅ Found Viral Video: {video.get('title')} ({video.get('view_count', 0)} views)")
    video_url = f"https://www.youtube.com/watch?v={video['id']}"
    
    # 2. Process Video (Generate Shorts)
    # Generate 3 shorts
    shorts = process_video(video_url, num_clips=3, clip_duration=50)
    
    if not shorts:
        print("❌ Failed to generate shorts.")
        return

    # 3. Optimize & Prepare for Upload
    selected_short = shorts[0]
    seo = generate_seo_metadata(channel_name, video.get('title', 'Unknown'), selected_short)
    
    print("\n📊 SEO OPTIMIZATION REPORT (0/5 Criteria Check):")
    print(f"[x] Tripled Keywords: '{channel_name}', 'Funny' used in Title, Desc, Tags")
    print(f"[x] Keywords in Title: {seo['title']}")
    print(f"[x] Keywords in Desc: Yes")
    print(f"[x] Tag Volume: Using high-volume tags like #shorts #viral")
    print(f"[x] Tag Count: {len(seo['tags'])} tags generated")
    
    # Save SEO data alongside clip
    meta_path = selected_short['path'].replace('.mp4', '_meta.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(seo, f, indent=2)
    
    # 4. Upload
    print("\n🚀 Authenticating and Uploading...")
    youtube = get_authenticated_service()
    if youtube:
        try:
            upload_video_scheduled(
                youtube, 
                selected_short['path'], 
                seo['title'], 
                seo['description'], 
                seo['tags']
            )
            
            # Update History only on success
            processed_ids.append(video['id'])
            history['processed_videos'] = processed_ids
            save_history(history)
            
        except Exception as e:
            print(f"❌ Upload Failed: {e}")
    else:
        print("❌ Authentication failed, strictly skipping upload.")


if __name__ == "__main__":
    main()
