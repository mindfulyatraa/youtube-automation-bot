import os
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from youtube_automation import SCOPES

# Fix for Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

# Configuration
SHORTS_FOLDER = "shorts"
VIDEO_ID = "_uRdozeKuUg"
OUTPUT_BASE = os.path.join(SHORTS_FOLDER, f"carryminati_{VIDEO_ID}")
IMAGE_OVERLAY_PATH = "wait_for_end.jpg" # In current dir

# Specific clips to process (1-based index)
TARGET_CLIPS = [2, 3, 4, 5]

def get_authenticated_service():
    """Authenticate with YouTube"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return build('youtube', 'v3', credentials=creds)

def upload_video_scheduled(youtube, file, title, description, tags, publish_time_iso=None):
    print(f"📤 Preparing Upload: {title[:50]}...")
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '23'
        },
        'status': {
            'selfDeclaredMadeForKids': False
        }
    }
    
    if publish_time_iso:
        body['status']['privacyStatus'] = 'private'
        body['status']['publishAt'] = publish_time_iso
        print(f"   📅 Scheduled for: {publish_time_iso}")
    else:
        body['status']['privacyStatus'] = 'public'
        print(f"   🚀 Publishing Immediately")

    media = MediaFileUpload(file, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"   ⬆️ Uploading: {int(status.progress() * 100)}%")
            
    print(f"   ✅ Upload Complete! ID: {response['id']}")

def generate_seo(clip_num):
    titles = {
        2: "CarryMinati Caught off Guard! 😂 | Wait for end #shorts",
        3: "CarryMinati Best Roast Moment 🔥 | Funny #shorts",
        4: "CarryMinati vs Jalan - Hilarious! 🤣 | Wait for end #shorts",
        5: "CarryMinati Crazy Reaction 😂 | Must Watch #shorts"
    }
    base_title = titles.get(clip_num, "CarryMinati Funny Moment 😂 #shorts")
    
    desc = f"""
Wait for the end! 😂
Best viral funny moment from CarryMinati's new video 'Koffee with Jalan'.

#shorts #viral #funny #carryminati #roast

Credits:
Original Video: KOFFEE WITH JALAN | CARRYMINATI
Channel: CarryMinati

Content:
Fan-made short. Subscribe to CarryMinati for more!

Keywords:
carryminati, carryminati new video, carryminati roast, funny, comedy, viral shorts, indian youtube.
"""
    tags = ["carryminati", "minati", "carry", "funny", "comedy", "shorts", "viral", "trending", "wait for end"]
    return base_title, desc.strip(), tags

def main():
    print("=" * 60)
    print("🎬 APPLY IMAGE OVERLAY & UPLOAD")
    print("=" * 60)
    
    # Verify Image
    if not os.path.exists(IMAGE_OVERLAY_PATH):
        print(f"❌ Image not found: {IMAGE_OVERLAY_PATH}")
        # Try finding absolute path
        IMAGE_OVERLAY_PATH_ABS = os.path.abspath(IMAGE_OVERLAY_PATH)
        print(f"   Checked: {IMAGE_OVERLAY_PATH_ABS}")
        return

    # Raw Clips (Already have blurred BG from initial generation)
    RAW_FILES = {
        2: os.path.join(OUTPUT_BASE, "short_2_t266s.mp4"),
        3: os.path.join(OUTPUT_BASE, "short_3_t444s.mp4"),
        4: os.path.join(OUTPUT_BASE, "short_4_t622s.mp4"),
        5: os.path.join(OUTPUT_BASE, "short_5_t800s.mp4")
    }

    processed_files = {}

    print("\n🔨 Applying Image Overlay...")
    for clip_num in TARGET_CLIPS:
        input_path = RAW_FILES.get(clip_num)
        if not os.path.exists(input_path):
            print(f"⚠️ Raw clip not found: {input_path}")
            continue
            
        output_filename = f"final_image_short_{clip_num}.mp4"
        output_path = os.path.join(OUTPUT_BASE, output_filename)
        
        print(f"   Processing Clip {clip_num}...")
        
        # FFmpeg Overlay Image
        # Scale image to 800px width (maintain aspect)
        # Overlay at x=(W-w)/2 : y=150
        
        filter_complex = (
            f"[1:v]scale=800:-1[img];"
            f"[0:v][img]overlay=(W-w)/2:150[outv]"
        )
        
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-i", input_path,
            "-i", IMAGE_OVERLAY_PATH,
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", "0:a",
            "-c:v", "libx264", "-c:a", "copy",
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True)
            processed_files[clip_num] = output_path
            print(f"   ✓ Success: {output_filename}")
        except Exception as e:
            print(f"   ❌ FFmpeg Failed: {e}")

    # Upload
    print("\n🚀 Starting Upload Sequence...")
    try:
        youtube = get_authenticated_service()
    except:
        print("❌ Auth failed")
        return

    # Helper for Time
    def get_utc_for_ist(day_offset, hour_ist):
        dt_ist = datetime.now().replace(hour=hour_ist, minute=0, second=0, microsecond=0) + timedelta(days=day_offset)
        dt_utc = dt_ist - timedelta(hours=5, minutes=30)
        return dt_utc.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    schedule_map_utc = {
        2: None,
        3: get_utc_for_ist(0, 20),
        4: get_utc_for_ist(1, 8), 
        5: get_utc_for_ist(1, 20) 
    }
    
    for clip_num in TARGET_CLIPS:
        if clip_num not in processed_files:
            continue
            
        file_path = processed_files[clip_num]
        title, desc, tags = generate_seo(clip_num)
        publish_time = schedule_map_utc[clip_num]
        
        try:
            upload_video_scheduled(youtube, file_path, title, desc, tags, publish_time)
        except Exception as e:
            print(f"❌ Upload Error: {e}")
            if "published too far in the past" in str(e):
                print("   ⚠️ Retrying immediate...")
                upload_video_scheduled(youtube, file_path, title, desc, tags, None)

    print("\n✨ Done!")

if __name__ == "__main__":
    main()
