import os
import json
import subprocess
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import random
import re
import time
import schedule

# ==================== CONFIGURATION ====================
YOUTUBE_API_KEY = "AIzaSyDOXwfmQQnhw2P3FHauy_q0skaDd4i2Xqg" 
DOWNLOAD_FOLDER = "downloads"
CLIPS_FOLDER = "clips"
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Indian YouTubers focus
INDIAN_YOUTUBERS = [
    "Thugesh",
    "Ashish Chanchlani",
    "CarryMinati", 
    "BB Ki Vines",
    "Triggered Insaan",
    "Fukra Insaan",
    "Flying Beast",
    "Technical Guruji",
    "Ranveer Allahbadia podcast",
    "Beer Biceps",
    "Sandeep Maheshwari"
]

# Video settings
MIN_VIDEO_DURATION = 180  # 3 minutes (relaxed for Indian content)
MAX_VIDEO_DURATION = 7200
MIN_VIEWS_THRESHOLD = 50000  # Lower for Indian market
CLIP_DURATION = 55  # 55 seconds

# Upload timing - DAILY 8 AM & 8 PM
UPLOAD_TIMES = ["08:00", "20:00"]

# ==================== SETUP ====================
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(CLIPS_FOLDER, exist_ok=True)

UPLOAD_HISTORY_FILE = "upload_history.json"

def load_upload_history():
    if os.path.exists(UPLOAD_HISTORY_FILE):
        with open(UPLOAD_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {'uploaded_videos': [], 'last_upload_time': None}

def save_upload_history(history):
    with open(UPLOAD_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def parse_duration(duration_str):
    """ISO 8601 duration parser"""
    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = pattern.match(duration_str)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds

# ==================== INDIAN VIRAL VIDEOS FINDER ====================
def find_indian_viral_videos(max_results=3, history=None):
    """Indian YouTubers ki LATEST viral videos dhoondhta hai"""
    print("🇮🇳 Indian viral videos search kar raha hoon...\n")
    
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # Last 10 days ki videos (fresh content)
    published_after = (datetime.now() - timedelta(days=10)).isoformat() + 'Z'
    
    all_viral_videos = []
    
    # Har YouTuber ke latest videos check karo
    for youtuber in INDIAN_YOUTUBERS[:5]:  # Top 5 check karo
        try:
            print(f"🔍 Checking: {youtuber}")
            
            request = youtube.search().list(
                part="snippet",
                q=youtuber,
                type="video",
                order="date",  # Latest first
                publishedAfter=published_after,
                maxResults=3,
                regionCode="IN",
                relevanceLanguage="hi"
            )
            
            response = request.execute()
            
            for item in response['items']:
                video_id = item['id']['videoId']
                
                # Skip if already processed
                if history and video_id in history.get('uploaded_videos', []):
                    continue
                
                # Get video details
                video_details = youtube.videos().list(
                    part="statistics,contentDetails,snippet",
                    id=video_id
                ).execute()
                
                if video_details['items']:
                    stats = video_details['items'][0]['statistics']
                    duration_str = video_details['items'][0]['contentDetails']['duration']
                    snippet = video_details['items'][0]['snippet']
                    
                    duration_seconds = parse_duration(duration_str)
                    views = int(stats.get('viewCount', 0))
                    
                    # Check criteria
                    if (duration_seconds >= MIN_VIDEO_DURATION and 
                        duration_seconds <= MAX_VIDEO_DURATION and
                        views >= MIN_VIEWS_THRESHOLD):
                        
                        all_viral_videos.append({
                            'video_id': video_id,
                            'title': snippet['title'],
                            'views': views,
                            'duration': duration_seconds,
                            'channel': snippet['channelTitle'],
                            'url': f"https://www.youtube.com/watch?v={video_id}"
                        })
                        
                        print(f"  ✅ Found: {snippet['title'][:50]}...")
                        print(f"     Views: {views:,} | Duration: {duration_seconds//60}min\n")
                        
                        if len(all_viral_videos) >= max_results:
                            break
            
            if len(all_viral_videos) >= max_results:
                break
                
        except Exception as e:
            print(f"  ⚠️ Error checking {youtuber}: {e}\n")
            continue
    
    return all_viral_videos

# ==================== DOWNLOAD VIDEO ====================
def download_video(video_url, output_path):
    """Video download karta hai"""
    print(f"⬇️  Downloading: {video_url}")
    
    command = [
        'yt-dlp',
        '-f', 'bestvideo[height<=1080]+bestaudio/best',
        '--merge-output-format', 'mp4',
        '-o', output_path,
        video_url
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True)
        print(f"✅ Download complete!\n")
        return True
    except Exception as e:
        print(f"❌ Download failed: {e}\n")
        return False

# ==================== SMART CLIP EXTRACTION ====================
def find_best_clip_segment(video_path, duration):
    """Video ke MIDDLE part se best segment nikalta hai (intro/outro skip)"""
    
    # Skip first 10% and last 10% (intro/outro avoid)
    skip_start = duration * 0.1
    skip_end = duration * 0.9
    
    usable_duration = skip_end - skip_start
    
    if usable_duration < CLIP_DURATION:
        # Agar video choti hai to middle se lo
        start = duration * 0.3
    else:
        # Middle 60% me se random select
        start = skip_start + random.uniform(0, usable_duration - CLIP_DURATION)
    
    return max(skip_start, min(start, skip_end - CLIP_DURATION))

def extract_clip_fast(video_path, video_info):
    """FAST clip extraction - no heavy processing"""
    print(f"✂️  Extracting viral clip...\n")
    
    # Get video duration from info instead of ffprobe
    duration = video_info.get('duration', 0)
    
    # Fallback if duration is 0
    if duration == 0:
        try:
             # Try getting duration with ffmpeg if ffprobe missing
             result = subprocess.run(['ffmpeg', '-i', video_path], capture_output=True, text=True, stderr=subprocess.STDOUT)
             # Search for Duration: 00:00:00.00
             match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})\.\d+", result.stdout)
             if match:
                 h, m, s = map(int, match.groups())
                 duration = h*3600 + m*60 + s
             else:
                 duration = 600 # Fallback 10 mins
        except:
             duration = 600
    
    # Find best start time (avoiding intro/outro)
    start_time = find_best_clip_segment(video_path, duration)
    
    print(f"📍 Extracting from: {int(start_time//60)}:{int(start_time%60):02d}")
    
    clip_filename = f"clip_{video_info['video_id']}.mp4"
    clip_path = os.path.join(CLIPS_FOLDER, clip_filename)
    
    # Extract with captions burned in (FFmpeg subtitle filter)
    # Using arial.ttf, escaping correctly for windows if needed. 
    # FFmpeg on windows handles forward slashes usually, but let's be safe with simple path or none.
    # The user provided path: /Windows/Fonts/arial.ttf
    
    command = [
        'ffmpeg',
        '-ss', str(start_time),
        '-i', video_path,
        '-t', str(CLIP_DURATION),
        '-vf', (
            'scale=1080:1920:force_original_aspect_ratio=increase,'
            'crop=1080:1920,'
            "drawtext=fontfile='C\:/Windows/Fonts/arial.ttf':text='':fontsize=60:fontcolor=yellow:borderw=3:bordercolor=black:x=(w-text_w)/2:y=h*0.7"
        ),
        '-c:v', 'libx264',
        '-preset', 'fast',  # Fast encoding
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-y',
        clip_path
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, timeout=120)
        print(f"✅ Clip created: {clip_filename}\n")
        return {
            'path': clip_path,
            'filename': clip_filename,
            'start_time': start_time
        }
    except Exception as e:
        print(f"❌ Clip creation failed: {e}\n")
        return None

# ==================== SIMPLE VIRAL CAPTIONS (FFmpeg based) ====================
def add_viral_captions_simple(video_path, output_path):
    """Simple but effective viral captions using FFmpeg"""
    print("📝 Adding viral captions...\n")
    
    # Extract audio for Whisper
    audio_path = video_path.replace('.mp4', '_audio.wav')
    
    audio_command = [
        'ffmpeg',
        '-i', video_path,
        '-vn',
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        '-y',
        audio_path
    ]
    
    try:
        subprocess.run(audio_command, check=True, capture_output=True, timeout=30)
        
        # Use Whisper for transcription (if available)
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(audio_path, language='hi')  # Hindi support
            
            # Create SRT file
            srt_path = video_path.replace('.mp4', '.srt')
            create_srt_file(result['segments'], srt_path)
            
            # Burn subtitles into video
            # NOTE: FFmpeg subtitles filter path escaping on Windows is tricky.
            # Using relative path or forward slashes helps.
            # escape backslashes in srt_path
            
            escaped_srt = srt_path.replace('\\', '/').replace(':', '\\:')
            
            burn_command = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"subtitles='{escaped_srt}':force_style='Fontsize=24,PrimaryColour=&H00FFFF,OutlineColour=&H000000,BorderStyle=3,Outline=2,Shadow=1,Alignment=2'",
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            
            subprocess.run(burn_command, check=True, capture_output=True, timeout=60)
            
            # Cleanup
            if os.path.exists(audio_path): os.remove(audio_path)
            if os.path.exists(srt_path): os.remove(srt_path)
            
            print("✅ Viral captions added!\n")
            return True
            
        except ImportError:
            print("⚠️  Whisper not available, uploading without captions\n")
            # Just copy the file
            import shutil
            shutil.copy(video_path, output_path)
            if os.path.exists(audio_path): os.remove(audio_path)
            return True
            
    except Exception as e:
        print(f"⚠️  Caption error: {e}, uploading without captions\n")
        import shutil
        shutil.copy(video_path, output_path)
        return True

def create_srt_file(segments, srt_path):
    """Create SRT subtitle file"""
    with open(srt_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, 1):
            start = format_timestamp(segment['start'])
            end = format_timestamp(segment['end'])
            text = segment['text'].strip().upper()  # Uppercase for viral effect
            
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

# ==================== VIRAL METADATA ====================
def generate_viral_title(original_title):
    """Hindi + English mix viral title"""
    
    # Extract keywords
    words = re.findall(r'\b\w+\b', original_title)
    important = [w for w in words if len(w) > 3][:3]
    
    emojis = ["🔥", "😂", "💯", "⚡", "😱", "🤣"]
    
    patterns = [
        f"{random.choice(emojis)} {' '.join(important[:2]).upper()} | Viral Moment",
        f"Dekho Ye {random.choice(emojis)} | {important[0] if important else 'VIRAL'}",
        f"OMG {random.choice(emojis)} {' '.join(important[:2])} | Must Watch",
        f"Pagal Moment {random.choice(emojis)} | {important[0] if important else 'Epic'}",
        f"Crazy {random.choice(emojis)} | {' '.join(important[:2])}"
    ]
    
    return random.choice(patterns)[:100]

def generate_viral_description(original_title, views, channel, video_url):
    """Indian style description"""
    
    return f"""🔥 YE MOMENT VIRAL HO GAYA! 🔥

{channel} ki video se - {views:,}+ views! 💯

Poora video dekho: {video_url}

🎯 FOLLOW karo daily viral content ke liye!
👍 LIKE karo agar pasand aaya!
💬 COMMENT me batao kya laga!
🔔 BELL icon dabao!

#Shorts #Viral #India #Trending #IndianYouTuber #{channel.replace(' ', '')} 
#ViralVideo #Trending2025 #FunnyVideos #Comedy #Entertainment #Desi 
#HindiComedy #IndianComedy #MustWatch #Epic #Hilarious #Crazy
"""

def generate_viral_tags(channel):
    """Indian audience tags"""
    tags = [
        "shorts", "viral", "trending", "india", "hindi", 
        "indian youtuber", channel.lower(), "comedy", "funny",
        "viral video", "trending shorts", "indian comedy",
        "desi", "entertainment", "must watch", "epic",
        "hilarious", "crazy", "pagal", "मजेदार"
    ]
    return tags[:30]

# ==================== UPLOAD ====================
def get_authenticated_service():
    credentials = None
    if os.path.exists('token.json'):
        credentials = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
        credentials = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(credentials.to_json())
    return build('youtube', 'v3', credentials=credentials)

def upload_short(youtube, video_file, original_title, views, channel, video_url):
    """Upload with viral metadata"""
    
    viral_title = generate_viral_title(original_title)
    viral_desc = generate_viral_description(original_title, views, channel, video_url)
    viral_tags = generate_viral_tags(channel)
    
    print(f"📤 Uploading: {viral_title}\n")
    
    body = {
        'snippet': {
            'title': viral_title,
            'description': viral_desc,
            'tags': viral_tags,
            'categoryId': '24'
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }
    
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"⬆️  {int(status.progress() * 100)}%")
    
    print(f"✅ UPLOADED! https://youtube.com/shorts/{response['id']}\n")
    return response['id']

# ==================== SCHEDULED UPLOADS ====================
def run_daily_upload():
    """Daily upload cycle - 8 AM & 8 PM"""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("\n" + "="*60)
        print(f"🇮🇳 INDIAN VIRAL SHORTS - {current_time}")
        print("="*60 + "\n")
        
        history = load_upload_history()
        
        # Find viral videos
        viral_videos = find_indian_viral_videos(max_results=2, history=history)
        
        if not viral_videos:
            print("❌ No new viral videos found\n")
            return
        
        # Process first video
        video = viral_videos[0]
        print(f"🎬 Processing: {video['title'][:60]}")
        print(f"   Channel: {video['channel']}")
        print(f"   Views: {video['views']:,}\n")
        
        video_path = os.path.join(DOWNLOAD_FOLDER, f"{video['video_id']}.mp4")
        
        # Download
        if not download_video(video['url'], video_path):
            return
        
        # Extract clip (FAST - no heavy AI)
        clip = extract_clip_fast(video_path, video)
        
        if not clip:
            if os.path.exists(video_path):
                os.remove(video_path)
            return
        
        # Add captions (if Whisper available, else skip)
        final_clip = os.path.join(CLIPS_FOLDER, f"final_{clip['filename']}")
        add_viral_captions_simple(clip['path'], final_clip)
        
        # Upload
        youtube = get_authenticated_service()
        
        upload_short(
            youtube,
            final_clip,
            video['title'],
            video['views'],
            video['channel'],
            video['url']
        )
        
        # Cleanup
        if os.path.exists(video_path): os.remove(video_path)
        if os.path.exists(clip['path']): os.remove(clip['path'])
        
        # Update history
        history['uploaded_videos'].append(video['video_id'])
        history['last_upload_time'] = current_time
        save_upload_history(history)
        
        print("="*60)
        print("🎉 Upload successful!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")

def main():
    """Main scheduler - 8 AM & 8 PM daily"""
    print("🇮🇳 INDIAN VIRAL SHORTS AUTOMATION")
    print("="*60)
    print("✅ Focus: Indian YouTubers (Thugesh, Ashish, Carry, etc.)")
    print("✅ Schedule: Daily 8 AM & 8 PM")
    print("✅ Fast processing (2-3 min per video)")
    print("✅ Smart clip selection (no intro/outro)")
    print("✅ Viral captions (Hindi + English)")
    print("="*60)
    
    # Auto-run for verification as per user request ("abhi upload karke dikha")
    # But usually we ask. However, previous turn implied immediacy.
    # To be safe and compliant with the code logic:
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--run-now":
         run_daily_upload()
         return

    mode = input("\nMode?\n1. Scheduled (Daily 8AM & 8PM)\n2. Run Now (once)\n\nEnter (1/2): ").strip()
    
    if mode == "1":
        print("\n✅ Scheduled mode activated!")
        print("📅 Uploads: Daily at 8:00 AM & 8:00 PM")
        print("🔄 Press Ctrl+C to stop\n")
        
        # Schedule for 8 AM and 8 PM
        schedule.every().day.at("08:00").do(run_daily_upload)
        schedule.every().day.at("20:00").do(run_daily_upload)
        
        # Check if we should run now
        current_hour = datetime.now().hour
        if current_hour < 8 or (current_hour >= 8 and current_hour < 20):
            print("⏰ Next upload: Today 8:00 PM\n")
        else:
            print("⏰ Next upload: Tomorrow 8:00 AM\n")
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        print("\n✅ Running once...\n")
        run_daily_upload()

if __name__ == "__main__":
    main()
