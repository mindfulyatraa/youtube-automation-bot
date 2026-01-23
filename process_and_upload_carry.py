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

# Import from existing scripts
from youtube_automation import SCOPES

# Fix for Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

# Configuration
SHORTS_FOLDER = "shorts"
VIDEO_ID = "_uRdozeKuUg"
OUTPUT_BASE = os.path.join(SHORTS_FOLDER, f"carryminati_{VIDEO_ID}")

# Specific clips to process (1-based index from user request)
# User liked: 2, 3, 4, 5
TARGET_CLIPS = [2, 3, 4, 5]

def get_authenticated_service():
    """Authenticate with YouTube (copied/adapted from youtube_automation.py)"""
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
    """
    Uploads a video to YouTube with optional scheduling.
    """
    print(f"📤 Preparing Upload: {title[:50]}...")
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '23' # Comedy
        },
        'status': {
            'selfDeclaredMadeForKids': False
        }
    }
    
    if publish_time_iso:
        # Scheduled upload
        body['status']['privacyStatus'] = 'private'
        body['status']['publishAt'] = publish_time_iso
        print(f"   📅 Scheduled for: {publish_time_iso}")
    else:
        # Immediate public upload
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
    return response['id']

def generate_seo(clip_num):
    """Generate SEO metadata for specific clips"""
    
    # Titles customized for each clip (Simulated variety)
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
    
    tags = [
        "carryminati", "minati", "carry", "ajey nagar", "carryminati roast", 
        "funny", "comedy", "shorts", "viral", "trending", "wait for end",
        "carryminati new video", "koffee with jalan"
    ]
    
    return base_title, desc.strip(), tags

def main():
    print("=" * 60)
    print("🎬 PROCESS & UPLOAD - CARRYMINATI SHORTS")
    print("=" * 60)
    
    # 1. Process Existing Shorts (Add Overlay)
    created_files = {}
    
    # Existing files map (User provided paths)
    EXISTING_TUBE_FILES = {
        2: os.path.join(OUTPUT_BASE, "short_2_t266s.mp4"),
        3: os.path.join(OUTPUT_BASE, "short_3_t444s.mp4"),
        4: os.path.join(OUTPUT_BASE, "short_4_t622s.mp4"),
        5: os.path.join(OUTPUT_BASE, "short_5_t800s.mp4")
    }

    print("\n🔨 Adding 'Wait for End' to existing shorts...")
    
    # Font path selection
    font_path = "arial.ttf"
    if sys.platform != "win32":
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if not os.path.exists(font_path):
             font_path = "FreeSans.ttf"

    for clip_num in TARGET_CLIPS:
        input_path = EXISTING_TUBE_FILES.get(clip_num)
        if not input_path or not os.path.exists(input_path):
            print(f"⚠️ Clip not found: {input_path}")
            continue
            
        output_filename = f"final_ready_short_{clip_num}.mp4"
        output_path = os.path.join(OUTPUT_BASE, output_filename)
        
        print(f"   Processing Clip {clip_num}...")
        
        # Simple Drawtext Filter for existing video
        text_cmd = (
            f"drawtext=text='⚠️ WAIT FOR END ⚠️':fontfile='{font_path}':"
            f"fontcolor=white:fontsize=80:x=(w-text_w)/2:y=150:"
            f"borderw=5:bordercolor=black:shadowx=2:shadowy=2"
        )
        
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-i", input_path,
            "-vf", text_cmd,
            "-c:v", "libx264", "-c:a", "copy",
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True)
            created_files[clip_num] = output_path
            print(f"   ✓ Ready: {output_filename}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")

    # 2. Upload with Schedule
    print("\n🚀 Starting Upload Sequence...")
    try:
        youtube = get_authenticated_service()
    except Exception as e:
        print(f"❌ Auth Failed: {e}")
        return
    
    # Schedule Logic
    # 2: Now
    # 3: Tonight 8 PM (20:00)
    # 4: Tomorrow 8 AM (08:00)
    # 5: Tomorrow 8 PM (20:00)
    
    # Helper to get UTC ISO string for IST time
    def get_utc_for_ist(day_offset, hour_ist):
        # Current local time (IST) + offset days
        dt_ist_now = datetime.now()
        dt_target_ist = dt_ist_now.replace(hour=hour_ist, minute=0, second=0, microsecond=0) + timedelta(days=day_offset)
        
        # If today's target time is in the past, move to tomorrow?
        if day_offset == 0 and dt_target_ist < dt_ist_now:
             # Just start "now" or schedule 5 mins from now?
             pass

        # Convert to UTC: IST - 5:30
        dt_utc = dt_target_ist - timedelta(hours=5, minutes=30)
        return dt_utc.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    schedule_map_utc = {
        2: None,
        3: get_utc_for_ist(0, 20), # Today 20:00 IST
        4: get_utc_for_ist(1, 8),  # Tomorrow 08:00 IST
        5: get_utc_for_ist(1, 20)  # Tomorrow 20:00 IST
    }
    
    for clip_num in TARGET_CLIPS:
        if clip_num not in created_files:
            continue
            
        file_path = created_files[clip_num]
        title, desc, tags = generate_seo(clip_num)
        publish_time = schedule_map_utc[clip_num]
        
        try:
            upload_video_scheduled(youtube, file_path, title, desc, tags, publish_time)
        except Exception as e:
            print(f"❌ Error uploading clip {clip_num}: {e}")
            if "published too far in the past" in str(e) or "invalid value" in str(e):
                print("   ⚠️ Retrying with immediate upload...")
                try:
                    upload_video_scheduled(youtube, file_path, title, desc, tags, None)
                except Exception as ex:
                    print(f"   ❌ Retry failed: {ex}")

    print("\n✨ All tasks finished!")

if __name__ == "__main__":
    main()
