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
import sys

# ==================== CONFIGURATION ====================
YOUTUBE_API_KEY = "AIzaSyDOXwfmQQnhw2P3FHauy_q0skaDd4i2Xqg" # Preserved API Key
DOWNLOAD_FOLDER = "downloads"
CLIPS_FOLDER = "clips"
TEMP_FOLDER = "temp"
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Your channel branding
YOUR_CHANNEL_NAME = "@MindfulYatraa"  # Updated based on corpus name hint, user can change
CREDITS_TEXT = "CREDITS - Original Creator"   

# Indian YouTubers
INDIAN_YOUTUBERS = [
    "Thugesh", "Ashish Chanchlani", "CarryMinati", "BB Ki Vines",
    "Triggered Insaan", "Fukra Insaan", "Flying Beast", 
    "Ranveer Allahbadia", "Beer Biceps", "Sandeep Maheshwari",
    "Technical Guruji", "Amit Bhadana"
]

# Video settings
MIN_VIDEO_DURATION = 180
MAX_VIDEO_DURATION = 7200
MIN_VIEWS_THRESHOLD = 50000
CLIP_DURATION = 55

# Upload timing - 8 AM & 8 PM
UPLOAD_TIMES = ["08:00", "20:00"]

# ==================== SETUP ====================
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(CLIPS_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

UPLOAD_HISTORY_FILE = "upload_history.json"

def load_upload_history():
    if os.path.exists(UPLOAD_HISTORY_FILE):
        with open(UPLOAD_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {'uploaded_videos': [], 'last_upload_time': None}

def save_upload_history(history):
    with open(UPLOAD_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

# ==================== FIND INDIAN VIRAL VIDEOS ====================
def find_indian_viral_videos(max_results=3, history=None):
    print("🇮🇳 Indian viral videos search...\n")
    
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    published_after = (datetime.now() - timedelta(days=10)).isoformat() + 'Z'
    
    all_videos = []
    
    for youtuber in INDIAN_YOUTUBERS[:5]:
        try:
            print(f"🔍 Checking: {youtuber}")
            
            request = youtube.search().list(
                part="snippet",
                q=youtuber,
                type="video",
                order="date",
                publishedAfter=published_after,
                maxResults=3,
                regionCode="IN"
            )
            
            response = request.execute()
            
            for item in response['items']:
                video_id = item['id']['videoId']
                
                if history and video_id in history.get('uploaded_videos', []):
                    continue
                
                video_details = youtube.videos().list(
                    part="statistics,contentDetails,snippet",
                    id=video_id
                ).execute()
                
                if video_details['items']:
                    stats = video_details['items'][0]['statistics']
                    duration_str = video_details['items'][0]['contentDetails']['duration']
                    snippet = video_details['items'][0]['snippet']
                    
                    duration = parse_duration(duration_str)
                    views = int(stats.get('viewCount', 0))
                    
                    if (duration >= MIN_VIDEO_DURATION and 
                        duration <= MAX_VIDEO_DURATION and
                        views >= MIN_VIEWS_THRESHOLD):
                        
                        all_videos.append({
                            'video_id': video_id,
                            'title': snippet['title'],
                            'views': views,
                            'duration': duration,
                            'channel': snippet['channelTitle'],
                            'url': f"https://www.youtube.com/watch?v={video_id}"
                        })
                        
                        print(f"  ✅ {snippet['title'][:50]}")
                        
                        if len(all_videos) >= max_results:
                            break
            
            if len(all_videos) >= max_results:
                break
                
        except Exception as e:
            print(f"  ⚠️  {e}\n")
            continue
    
    return all_videos

def parse_duration(duration_str):
    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = pattern.match(duration_str)
    if not match:
        return 0
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    return h * 3600 + m * 60 + s

# ==================== DOWNLOAD ====================
def download_video(video_url, output_path):
    print(f"⬇️  Downloading...")
    
    command = [
        'yt-dlp',
        '-f', 'bestvideo[height<=1080]+bestaudio/best',
        '--merge-output-format', 'mp4',
        '-o', output_path,
        video_url
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True)
        print(f"✅ Downloaded\n")
        return True
    except:
        print(f"❌ Failed\n")
        return False

# ==================== YOUTUBE COPYRIGHT-FREE MUSIC ====================
YOUTUBE_AUDIO_LIBRARY = [
    "https://www.youtube.com/watch?v=VIDEO_ID_HERE",  # Add YouTube Audio Library track URLs
]

def download_background_music():
    """YouTube Audio Library se background music download karta hai"""
    music_path = os.path.join(TEMP_FOLDER, "bg_music.mp3")
    
    if os.path.exists(music_path):
        return music_path
    
    # Placeholder - aap YouTube Audio Library se koi bhi copyright-free track download kar sakte ho
    print("⚠️  Background music manually add karo: temp/bg_music.mp3")
    return None

# ==================== SMART AUTO-FRAMING FOR PODCASTS ====================
def auto_frame_video(input_path, output_path):
    """Smart auto-framing - faces ko track karta hai"""
    print("🎯 Auto-framing (face tracking)...")
    
    command = [
        'ffmpeg',
        '-i', input_path,
        '-vf', (
            # Detect faces and center crop
            'crop=ih*9/16:ih:iw/2-ih*9/32:0,'  # 9:16 crop centered
            'scale=1080:1920'
        ),
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'copy',
        '-y',
        output_path
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, timeout=60)
        return True
    except:
        return False

# ==================== PROFESSIONAL CAPTIONS (TikTok/YouTube Style) ====================
def create_viral_hindi_captions(video_path, start_time, duration):
    """Hindi captions with Whisper - TikTok/YouTube Shorts style"""
    print("📝 Creating viral Hindi captions...")
    
    # Extract audio
    audio_path = os.path.join(TEMP_FOLDER, "audio.wav")
    
    audio_cmd = [
        'ffmpeg',
        '-ss', str(start_time),
        '-i', video_path,
        '-t', str(duration),
        '-vn',
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        '-y',
        audio_path
    ]
    
    try:
        subprocess.run(audio_cmd, check=True, capture_output=True, timeout=30)
        
        # Whisper transcription
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(audio_path, language='hi', word_timestamps=True)
            
            # Create ASS subtitle file (advanced styling)
            ass_path = os.path.join(TEMP_FOLDER, "captions.ass")
            create_tiktok_style_ass(result, ass_path)
            
            os.remove(audio_path)
            return ass_path
            
        except ImportError:
            print("⚠️  Whisper not installed")
            if os.path.exists(audio_path): os.remove(audio_path)
            return None
            
    except:
        return None

def create_tiktok_style_ass(transcription, output_path):
    """TikTok/YouTube Shorts style ASS captions banata hai"""
    
    # ASS file header with styling
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,70,&H00FFFF,&H000000FF,&H00000000,&HBF000000,-1,0,0,0,100,100,0,0,1,3,2,2,10,10,180,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ass_header)
        
        # Process segments
        if 'segments' in transcription:
            for segment in transcription['segments']:
                text = segment['text'].strip().upper()
                start = format_ass_time(segment['start'])
                end = format_ass_time(segment['end'])
                
                # Split into words for emphasis effect
                words = text.split()
                
                # Har 2-3 words ek line me (fast pacing)
                chunk_size = random.randint(2, 3)
                for i in range(0, len(words), chunk_size):
                    chunk = ' '.join(words[i:i+chunk_size])
                    
                    # Calculate timing
                    word_duration = (segment['end'] - segment['start']) / len(words)
                    chunk_start = segment['start'] + (i * word_duration)
                    chunk_end = chunk_start + (chunk_size * word_duration)
                    
                    # Important words ko highlight (random color)
                    if any(word in chunk.lower() for word in ['nahi', 'kya', 'hai', 'wow', 'crazy']):
                        # Yellow for emphasis
                        styled_chunk = f"{{\\c&H00FFFF&}}{chunk}"
                    else:
                        # White default
                        styled_chunk = f"{{\\c&HFFFFFF&}}{chunk}"
                    
                    f.write(f"Dialogue: 0,{format_ass_time(chunk_start)},{format_ass_time(chunk_end)},Default,,0,0,0,,{styled_chunk}\n")

def format_ass_time(seconds):
    """Convert seconds to ASS timestamp"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

# ==================== ADD CHANNEL CREDITS OVERLAY ====================
def add_channel_credits(input_path, output_path):
    """Bottom me channel credit overlay add karta hai"""
    print("🏷️  Adding channel credits...")
    
    command = [
        'ffmpeg',
        '-i', input_path,
        '-vf', (
            f"drawtext=text='{YOUR_CHANNEL_NAME}':"
            "fontfile=/Windows/Fonts/arial.ttf:fontsize=40:"
            "fontcolor=white:borderw=2:bordercolor=black:"
            "x=(w-text_w)/2:y=h-100,"
            f"drawtext=text='{CREDITS_TEXT}':"
            "fontfile=/Windows/Fonts/arial.ttf:fontsize=30:"
            "fontcolor=yellow:borderw=2:bordercolor=black:"
            "x=(w-text_w)/2:y=h-60"
        ),
        '-c:a', 'copy',
        '-y',
        output_path
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, timeout=60)
        return True
    except:
        return False

# ==================== COLOR GRADING ====================
def apply_color_grading(input_path, output_path):
    """Professional color grading apply karta hai"""
    print("🎨 Applying color grading...")
    
    # Cinematic look - saturation + contrast boost
    command = [
        'ffmpeg',
        '-i', input_path,
        '-vf', (
            'eq=contrast=1.2:brightness=0.05:saturation=1.3,'
            'unsharp=5:5:1.0:5:5:0.0'  # Sharpen
        ),
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '20',  # High quality
        '-c:a', 'copy',
        '-y',
        output_path
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, timeout=90)
        return True
    except:
        return False

# ==================== ADD BACKGROUND MUSIC ====================
def add_background_music(video_path, output_path, music_path=None):
    """Background music add karta hai (low volume)"""
    
    if not music_path or not os.path.exists(music_path):
        print("⚠️  No background music")
        return video_path
    
    print("🎵 Adding background music...")
    
    command = [
        'ffmpeg',
        '-i', video_path,
        '-i', music_path,
        '-filter_complex',
        '[1:a]volume=0.15[a1];[0:a][a1]amix=inputs=2:duration=shortest[aout]',
        '-map', '0:v',
        '-map', '[aout]',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-y',
        output_path
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, timeout=60)
        return output_path
    except:
        return video_path

# ==================== COMPLETE VIDEO PROCESSING ====================
def process_viral_clip(video_path, video_info):
    """Complete professional processing with all effects"""
    print(f"🎬 Processing viral clip...\n")
    
    # Get duration
    try:
        probe = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
            capture_output=True, text=True
        )
        duration = float(probe.stdout.strip())
    except Exception as e:
         print(f"Error getting duration: {e}")
         duration = 600 # Fallback

    
    # Smart clip selection (skip intro/outro)
    skip_start = duration * 0.15
    skip_end = duration * 0.85
    usable = skip_end - skip_start
    
    if usable < CLIP_DURATION:
        start_time = duration * 0.3
    else:
        start_time = skip_start + random.uniform(0, usable - CLIP_DURATION)
    
    print(f"📍 Clip from: {int(start_time//60)}:{int(start_time%60):02d}\n")
    
    # Step 1: Extract base clip
    temp1 = os.path.join(TEMP_FOLDER, "step1_extract.mp4")
    
    extract_cmd = [
        'ffmpeg',
        '-ss', str(start_time),
        '-i', video_path,
        '-t', str(CLIP_DURATION),
        '-c', 'copy',
        '-y',
        temp1
    ]
    
    subprocess.run(extract_cmd, check=True, capture_output=True)
    
    # Step 2: Auto-frame (9:16 with face tracking)
    temp2 = os.path.join(TEMP_FOLDER, "step2_framed.mp4")
    auto_frame_video(temp1, temp2)
    
    # Step 3: Color grading
    temp3 = os.path.join(TEMP_FOLDER, "step3_graded.mp4")
    apply_color_grading(temp2, temp3)
    
    # Step 4: Add Hindi captions
    ass_path = create_viral_hindi_captions(video_path, start_time, CLIP_DURATION)
    
    if ass_path:
        temp4 = os.path.join(TEMP_FOLDER, "step4_captions.mp4")
        
        # NOTE: Using simplified path handling for Windows to avoid escaping issues
        # ass filter needs escaped path.
        ass_path_str = ass_path.replace('\\', '/').replace(':', '\\:')
        
        caption_cmd = [
            'ffmpeg',
            '-i', temp3,
            '-vf', f"ass='{ass_path_str}'",
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '20',
            '-c:a', 'copy',
            '-y',
            temp4
        ]
        
        try:
            subprocess.run(caption_cmd, check=True, capture_output=True, timeout=90)
            current_clip = temp4
        except:
            current_clip = temp3
    else:
        current_clip = temp3
    
    # Step 5: Add channel credits
    temp5 = os.path.join(TEMP_FOLDER, "step5_credits.mp4")
    add_channel_credits(current_clip, temp5)
    
    # Step 6: Add background music (optional)
    bg_music = download_background_music()
    
    final_path = os.path.join(CLIPS_FOLDER, f"final_{video_info['video_id']}.mp4")
    
    if bg_music:
        add_background_music(temp5, final_path, bg_music)
    else:
        import shutil
        shutil.copy(temp5, final_path)
    
    # Cleanup temp files
    try:
        for temp in [temp1, temp2, temp3, temp4, temp5]:
            if os.path.exists(temp):
                os.remove(temp)
        if ass_path and os.path.exists(ass_path):
            os.remove(ass_path)
    except:
        pass
    
    print(f"✅ Final clip ready: {final_path}\n")
    
    return {
        'path': final_path,
        'filename': os.path.basename(final_path),
        'start_time': start_time
    }

# ==================== VIRAL METADATA ====================
def generate_viral_title(original_title):
    words = re.findall(r'\b\w+\b', original_title)
    important = [w for w in words if len(w) > 3][:3]
    emojis = ["🔥", "😂", "💯", "⚡", "😱", "🤣"]
    
    patterns = [
        f"{random.choice(emojis)} {' '.join(important[:2]).upper()} | Viral",
        f"Dekho {random.choice(emojis)} | {important[0] if important else 'EPIC'}",
        f"OMG {random.choice(emojis)} {' '.join(important[:2])}",
    ]
    
    return random.choice(patterns)[:100]

def generate_viral_description(title, views, channel, url):
    return f"""🔥 VIRAL MOMENT! 🔥

{channel} se - {views:,}+ views! 💯

Full video: {url}

🎯 Follow karo daily viral content ke liye!
👍 Like | 💬 Comment | 🔔 Subscribe

{CREDITS_TEXT}

#Shorts #Viral #India #Trending #{channel.replace(' ', '')} #ViralVideo 
#Trending2025 #FunnyVideos #Comedy #Entertainment #Desi #HindiComedy 
#MustWatch #Epic #Hilarious
"""

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

def upload_short(youtube, video_file, title, views, channel, url):
    viral_title = generate_viral_title(title)
    viral_desc = generate_viral_description(title, views, channel, url)
    
    print(f"📤 Uploading: {viral_title}\n")
    
    body = {
        'snippet': {
            'title': viral_title,
            'description': viral_desc,
            'tags': ['shorts', 'viral', 'india', 'hindi', channel.lower()],
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
    
    print(f"✅ https://youtube.com/shorts/{response['id']}\n")
    return response['id']

# ==================== DAILY UPLOAD ====================
def run_daily_upload(manual_url=None):
    try:
        print("\n" + "="*70)
        print(f"🇮🇳 PROFESSIONAL VIRAL SHORTS - {datetime.now()}")
        print("="*70 + "\n")
        
        history = load_upload_history()
        
        videos = []
        if manual_url:
            print(f"🔗 Processing Manual URL: {manual_url}")
            # Mock video details for manual run
            video_id = "manual_video"
            if "youtu.be" in manual_url:
                video_id = manual_url.split('/')[-1].split('?')[0]
            elif "v=" in manual_url:
                video_id = manual_url.split('v=')[-1].split('&')[0]
            
            videos = [{
                'video_id': video_id,
                'title': "Manual Test Video",
                'views': 999999,
                'duration': 600,
                'channel': "Manual Test Channel",
                'url': manual_url
            }]
        else:
             videos = find_indian_viral_videos(max_results=2, history=history)
        
        if not videos:
            print("❌ No new videos\n")
            return
        
        video = videos[0]
        print(f"🎬 {video['title'][:60]}")
        print(f"   {video['channel']} | {video['views']:,} views\n")
        
        video_path = os.path.join(DOWNLOAD_FOLDER, f"{video['video_id']}.mp4")
        
        if not download_video(video['url'], video_path):
            return
        
        # Professional processing with all effects
        clip = process_viral_clip(video_path, video)
        
        if not clip:
            if os.path.exists(video_path): os.remove(video_path)
            return
        
        # Upload
        youtube = get_authenticated_service()
        upload_short(youtube, clip['path'], video['title'], 
                    video['views'], video['channel'], video['url'])
        
        # Cleanup
        if os.path.exists(video_path): os.remove(video_path)
        
        # Update history
        history['uploaded_videos'].append(video['video_id'])
        history['last_upload_time'] = datetime.now().isoformat()
        save_upload_history(history)
        
        print("="*70)
        print("🎉 Upload complete!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")

def main():
    print("🇮🇳 PROFESSIONAL VIRAL SHORTS AUTOMATION")
    print("="*70)
    print("✅ Indian YouTubers focus")
    print("✅ Auto-framing (face tracking)")
    print("✅ Viral Hindi captions (TikTok style)")
    print("✅ Color grading + effects")
    print("✅ Channel credits overlay")
    print("✅ Background music")
    print("✅ Daily 8 AM & 8 PM uploads")
    print("="*70)
    
    # Check for CLI args first (GitHub Actions compatibility)
    if len(sys.argv) > 1:
        if sys.argv[1] == "--run-now":
             run_daily_upload()
             return
        if sys.argv[1] == "--url" and len(sys.argv) > 2:
             manual_url = sys.argv[2]
             run_daily_upload(manual_url=manual_url)
             return

    # Important setup
    print(f"\n⚠️  SETUP REQUIRED:")
    print(f"1. Edit line 17: YOUR_CHANNEL_NAME = '@YourChannel'")
    print(f"2. Add background music: temp/bg_music.mp3")
    print(f"3. Install: pip install openai-whisper\n")
    
    mode = input("Mode?\n1. Scheduled (8AM & 8PM)\n2. Run Now\n\nEnter (1/2): ").strip()
    
    if mode == "1":
        print("\n✅ Scheduled mode!")
        print("📅 Daily: 8:00 AM & 8:00 PM\n")
        
        schedule.every().day.at("08:00").do(run_daily_upload)
        schedule.every().day.at("20:00").do(run_daily_upload)
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        print("\n✅ Running now...\n")
        run_daily_upload()

if __name__ == "__main__":
    main()
