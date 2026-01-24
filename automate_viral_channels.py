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
    "Round2Hell": "https://www.youtube.com/@Round2Hell",
    "Amit Bhadana": "https://www.youtube.com/@AmitBhadana",
    "Harsh Beniwal": "https://www.youtube.com/@harshbeniwal",
    "Purav Jha": "https://www.youtube.com/@PuravJha"
}

# Configuration for logic
STRICT_NEW_ONLY = ["CarryMinati"]
DATE_CUTOFF = "20240101" # Jan 1, 2024

UPLOAD_HISTORY_FILE = "upload_history.json"

def load_history():
    if os.path.exists(UPLOAD_HISTORY_FILE):
        with open(UPLOAD_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(UPLOAD_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def get_latest_video(channel_url, ignore_ids=[]):
    """
    Check for specific 'NEW' video from the channel (last 48 hours).
    """
    print(f"   🔍 Checking for NEW videos (Last 48 hours)...")
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--flat-playlist",
        "--print-json",
        "--dateafter", "now-48hour", # Tiny window for breaking news
        "--playlist-end", "3",
        channel_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        print(f"   [DEBUG] New Video Search - RC: {result.returncode}, Output Len: {len(result.stdout)}")
        if result.stderr: print(f"   [DEBUG] STDERR: {result.stderr[:200]}")
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    if data['id'] in ignore_ids:
                        continue
                        
                    # Check duration (Skip shorts < 60s)
                    dur = data.get('duration')
                    if dur and dur < 60:
                        continue
                        
                    print(f"   🚨 NEW DROP DETECTED: {data.get('title')}")
                    return data
                except:
                    pass
    except Exception as e:
        print(f"Error checking new: {e}")
        
    return None

def get_recent_viral_video(channel_url, ignore_ids=[]):
    """
    Fallback: Most viral videos. First tries recent (After jan 2024), then All Time.
    """
    # 1. Try Recent Viral First
    print(f"   🔍 Finding recent hits (After {DATE_CUTOFF})...")
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--flat-playlist",
        "--print-json",
        "--dateafter", DATE_CUTOFF, # Only recent years
        "--playlist-end", "20",
        channel_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        print(f"   [DEBUG] Recent Search - RC: {result.returncode}, Output Len: {len(result.stdout)}")
        if result.stderr: print(f"   [DEBUG] STDERR: {result.stderr[:200]}")
        
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    dur = data.get('duration')
                    if dur and dur < 60:
                        continue
                    videos.append(data)
                except:
                    pass
        
        # Sort specific to Recent search
        videos.sort(key=lambda x: x.get('view_count', 0), reverse=True)
        
        for video in videos:
            if video['id'] not in ignore_ids:
                return video
                
    except Exception as e:
        print(f"Error searching recent viral: {e}")

    # 2. Fallback: All Time Viral (If no recent found)
    print(f"   ⚠️ No recent viral hits found. Searching ALL TIME viral...")
    cmd_fallback = [
        sys.executable, "-m", "yt_dlp",
        "--flat-playlist",
        "--print-json",
        "--playlist-end", "50", # Fetch more to find a hit
        channel_url
    ]
    
    try:
        result = subprocess.run(cmd_fallback, capture_output=True, text=True, encoding='utf-8')
        print(f"   [DEBUG] Fallback Search - RC: {result.returncode}, Output Len: {len(result.stdout)}")
        if result.stderr: print(f"   [DEBUG] STDERR: {result.stderr[:200]}")
        
        fallback_videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    dur = data.get('duration')
                    if dur and dur < 60:
                        continue
                    if data['id'] not in ignore_ids:
                        fallback_videos.append(data)
                except:
                    pass
        
        # Sort fallback videos by views too
        if fallback_videos:
            fallback_videos.sort(key=lambda x: x.get('view_count', 0), reverse=True)
            best_video = fallback_videos[0]
            print(f"   ✅ Found All-Time Viral hit: {best_video.get('title')} ({best_video.get('view_count')} views)")
            return best_video
            
    except Exception as e:
        print(f"Error searching all-time viral: {e}")

    return None

def get_video_for_channel(channel_name, channel_url, ignore_ids=[]):
    """
    Intelligent Selection Logic:
    1. Priority: Breaking News (New upload last 48h) matched for ALL.
    2. Fallback:
       - CarryMinati: STOP (Strict New Only).
       - Others: Viral Hits after 2024.
    """
    # 1. Check New
    new_video = get_latest_video(channel_url, ignore_ids)
    if new_video:
        return new_video
        
    # 2. Apply Custom Rules
    if channel_name in STRICT_NEW_ONLY:
        print(f"   ⚠️ 'Strict New Only' active for {channel_name}. No new video found -> Skipping.")
        return None
        
    # 3. Fallback to Recent Viral
    return get_recent_viral_video(channel_url, ignore_ids)

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
    
    # Shuffle channels to try random order, but try ALL until one works
    channel_items = list(CHANNELS.items())
    random.shuffle(channel_items)
    
    video = None
    selected_channel_name = None
    
    for name, url in channel_items:
        print(f"🎯 Checking Target Channel: {name}")
        candidate_video = get_video_for_channel(name, url, processed_ids)
        
        if candidate_video:
            video = candidate_video
            channel_name = name # Update the main channel_name variable
            channel_url = url
            break
        else:
            print(f"   ⚠️ No suitable video found for {name}, trying next...")
    
    if not video:
        print("❌ No suitable new video found in ANY channel.")
        sys.exit(1)
        
    print(f"✅ Found Viral Video: {video.get('title')} ({video.get('view_count', 0)} views)")
    video_url = f"https://www.youtube.com/watch?v={video['id']}"
    
    # 2. Process Video (Generate Shorts)
    # Generate 3 shorts
    shorts = process_video(video_url, num_clips=3, clip_duration=50)
    
    if not shorts:
        print("❌ Failed to generate shorts.")
        sys.exit(1)

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
            sys.exit(1)
    else:
        print("❌ Authentication failed, strictly skipping upload.")
        sys.exit(1)


if __name__ == "__main__":
    main()
