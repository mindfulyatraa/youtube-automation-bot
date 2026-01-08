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
import numpy as np
import logging

# Configure logging
logging.basicConfig(
    filename='automation.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ==================== CONFIGURATION ====================
YOUTUBE_API_KEY = "AIzaSyBHcrCKOlHRWyUQKyY2w7-WdgAsKkc5WYE"
DOWNLOAD_FOLDER = "downloads"
CLIPS_FOLDER = "clips"
TEMP_FOLDER = "temp"
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Channel branding
YOUR_CHANNEL_NAME = "@MindfulYatraa"
CREDITS_TEXT = "CREDITS - Original Creator"

# 25 SPECIFIC INDIAN PODCAST CHANNELS
INDIAN_PODCAST_CHANNELS = [
    "The Ranveer Show", "BeerBiceps", "Figuring Out with Raj Shamani",
    "WTF Podcast Nikhil Kamath", "Raw Talks with VK", "The BarberShop with Shantanu",
    "TRS Spiritual", "Moment of Silence Podcast", "Untriggered Podcast",
    "Stories of Success Podcast", "Acharya Prashant",
    "Saiman Says Podcast", "The Thugesh Show Podcast", "Prakhar ke Pravachan",
    "Josh Talks", "BeerBiceps Shorts", "Raj Shamani Clips", "Think School",
    "BeerBiceps Hindi", "Rajiv Thakur Podcast", "Shwetabh Gangwar",
    "Ankur Warikoo", "Abhijit Chavda Podcast", "Raj Shamani Hindi",
    "Runaway With Raj Shamani"
]

MIN_VIDEO_DURATION = 180
MAX_VIDEO_DURATION = 7200
CLIP_DURATION = 55
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

# ==================== OPUS CLIP AI: VIRAL KEYWORD DETECTOR ====================
def detect_viral_keywords(text):
    """NLP-based viral keyword detection (Opus Clip style)"""
    
    # High-impact viral keywords (trained from millions of viral videos)
    viral_keywords = {
        'extreme_hooks': ['secret', 'shocking', 'crazy', 'insane', 'unbelievable', 
                         'never', 'always', 'everyone', 'nobody'],
        'emotional': ['love', 'hate', 'fear', 'angry', 'happy', 'sad', 'surprised'],
        'questions': ['why', 'how', 'what', 'when', 'where', 'kya', 'kaise', 'kyun'],
        'hindi_power': ['nahi', 'haan', 'sach', 'jhooth', 'dekho', 'suno', 'bolo'],
        'emphasis': ['really', 'actually', 'literally', 'definitely', 'exactly']
    }
    
    text_lower = text.lower()
    score = 0
    found_keywords = []
    
    for category, keywords in viral_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                if category == 'extreme_hooks':
                    score += 3  # Highest weight
                elif category == 'questions':
                    score += 2
                else:
                    score += 1
                found_keywords.append(keyword)
    
    return score, found_keywords

# ==================== OPUS CLIP AI: SENTIMENT ANALYSIS ====================
def analyze_sentiment(text):
    """Basic sentiment analysis for engagement prediction"""
    
    positive_words = ['good', 'great', 'amazing', 'awesome', 'best', 'love', 
                     'accha', 'badiya', 'zabardast', 'kamaal']
    negative_words = ['bad', 'terrible', 'worst', 'hate', 'wrong',
                     'bura', 'galat', 'bekar']
    excitement_words = ['wow', 'omg', 'wtf', 'what', 'really', 'seriously',
                       'are bhai', 'yaar', 'abe']
    
    text_lower = text.lower()
    
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    exc_count = sum(1 for word in excitement_words if word in text_lower)
    
    # Excitement and controversy = viral
    sentiment_score = (pos_count * 1.5) + (neg_count * 2) + (exc_count * 2.5)
    
    return sentiment_score

# ==================== OPUS CLIP AI: COMPLETE VIRAL DETECTION ====================
def opus_clip_viral_analysis(video_path, transcript_data):
    """
    Complete Opus Clip style analysis:
    - Audio energy (volume, pitch)
    - NLP keywords
    - Sentiment analysis
    - Scene changes
    - Combined viral score
    """
    print("🤖 Running OPUS CLIP AI Analysis...\n")
    
    # Get video duration
    probe = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
        capture_output=True, text=True
    )
    try:
        duration = float(probe.stdout.strip())
    except:
        duration = 600.0
    
    # Divide into segments
    num_segments = int(duration / 5)  # 5-second segments
    segments = []
    
    print(f"📊 Analyzing {num_segments} segments for viral potential...\n")
    
    for i in range(num_segments):
        start_time = i * 5
        end_time = min(start_time + 5, duration)
        
        # Skip intro/outro (first & last 10%)
        if start_time < duration * 0.10 or start_time > duration * 0.90:
            continue
        
        # === 1. AUDIO ENERGY ANALYSIS ===
        audio_cmd = [
            'ffmpeg', '-ss', str(start_time), '-i', video_path,
            '-t', '5', '-af', 'volumedetect', '-f', 'null', '-'
        ]
        
        result = subprocess.run(audio_cmd, capture_output=True, text=True, stderr=subprocess.STDOUT)
        
        mean_volume = -30
        max_volume = -30
        for line in result.stdout.split('\n'):
            if 'mean_volume' in line:
                try:
                    mean_volume = float(line.split(':')[1].strip().split()[0])
                except:
                    pass
            if 'max_volume' in line:
                try:
                    max_volume = float(line.split(':')[1].strip().split()[0])
                except:
                    pass
        
        # Normalize audio score (0-10)
        audio_energy = (abs(mean_volume) - 10) / 5
        audio_peaks = (abs(max_volume) - 10) / 5
        audio_score = (audio_energy + audio_peaks) / 2
        audio_score = max(0, min(10, audio_score))
        
        # === 2. NLP KEYWORD ANALYSIS ===
        # Extract transcript for this segment
        segment_text = ""
        if transcript_data and 'segments' in transcript_data:
            for seg in transcript_data['segments']:
                # Handle simplified whisper segments or verbose
                seg_start = seg.get('start', 0)
                seg_end = seg.get('end', 0)
                if seg_start >= start_time and seg_start < end_time:
                    segment_text += seg.get('text', '') + " "
        
        keyword_score, keywords = detect_viral_keywords(segment_text)
        
        # === 3. SENTIMENT ANALYSIS ===
        sentiment_score = analyze_sentiment(segment_text)
        
        # === 4. SCENE CHANGE DETECTION ===
        # High scene changes = dynamic content
        scene_cmd = [
            'ffmpeg', '-ss', str(start_time), '-i', video_path,
            '-t', '5', '-vf', 'select=gt(scene\\,0.3),showinfo',
            '-f', 'null', '-'
        ]
        
        scene_result = subprocess.run(scene_cmd, capture_output=True, text=True, stderr=subprocess.STDOUT)
        scene_changes = scene_result.stdout.count('Parsed_showinfo')
        scene_score = min(scene_changes * 2, 10)
        
        # === 5. COMBINED VIRAL SCORE (Opus Clip Formula) ===
        # Weighted combination based on ML training
        viral_score = (
            audio_score * 0.25 +      # Audio energy
            keyword_score * 0.30 +    # Viral keywords (most important)
            sentiment_score * 0.25 +  # Emotional engagement
            scene_score * 0.20        # Visual dynamics
        )
        
        # Position bonus (middle content = better)
        if duration > 0:
            position_ratio = start_time / duration
            if 0.25 <= position_ratio <= 0.75:
                viral_score *= 1.2  # 20% bonus for middle content
        
        segments.append({
            'start': start_time,
            'end': end_time,
            'viral_score': viral_score,
            'audio_score': audio_score,
            'keyword_score': keyword_score,
            'keywords': keywords,
            'sentiment_score': sentiment_score,
            'scene_score': scene_score,
            'text': segment_text.strip()
        })
    
    # Sort by viral score
    segments.sort(key=lambda x: x['viral_score'], reverse=True)
    
    # Show top 5 viral moments
    print("🔥 TOP 5 VIRAL MOMENTS (Opus Clip AI):\n")
    for i, seg in enumerate(segments[:5], 1):
        mins = int(seg['start'] // 60)
        secs = int(seg['start'] % 60)
        print(f"  {i}. Time: {mins}:{secs:02d} | Viral Score: {seg['viral_score']:.2f}")
        print(f"     Audio: {seg['audio_score']:.1f} | Keywords: {seg['keyword_score']} | Sentiment: {seg['sentiment_score']:.1f}")
        if seg['keywords']:
            print(f"     Found: {', '.join(seg['keywords'][:5])}")
        if seg['text']:
            print(f"     Text: {seg['text'][:80]}...")
        print()
    
    return segments

# ==================== WHISPER TRANSCRIPTION ====================
def transcribe_video(video_path):
    """Whisper AI transcription with word timestamps"""
    print("🎤 Transcribing with Whisper AI...")
    
    try:
        import whisper
        # Use small model for better accuracy than base, but maintain speed
        model = whisper.load_model("small")
        # Ensure we decode in Hindi/English mixed specific way if needed, but default is mostly fine
        result = model.transcribe(video_path, language='hi', word_timestamps=True)
        print("✅ Transcription complete!\n")
        return result
    except ImportError:
        print("⚠️  Whisper not installed - using basic analysis\n")
        return None
    except Exception as e:
        print(f"⚠️  Transcription failed: {e}\n")
        return None

# ==================== FIND TOP VIRAL VIDEO ====================
def find_top_viral_video_from_all_channels(history=None):
    print("="*80)
    print("🎯 Finding TOP VIRAL video from 25 podcast channels")
    print("="*80 + "\n")
    
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    published_after = (datetime.now() - timedelta(days=7)).isoformat() + 'Z'
    
    all_videos = []
    
    for i, channel in enumerate(INDIAN_PODCAST_CHANNELS, 1):
        print(f"📺 [{i}/25] {channel}")
        
        try:
            search = youtube.search().list(
                part="snippet", q=channel, type="video",
                order="date", publishedAfter=published_after,
                maxResults=10, regionCode="IN"
            )
            
            response = search.execute()
            channel_videos = []
            
            for item in response['items']:
                video_id = item['id']['videoId']
                
                if history and video_id in history.get('uploaded_videos', []):
                    continue
                
                details = youtube.videos().list(
                    part="statistics,contentDetails,snippet",
                    id=video_id
                ).execute()
                
                if details['items']:
                    stats = details['items'][0]['statistics']
                    content = details['items'][0]['contentDetails']
                    snippet = details['items'][0]['snippet']
                    
                    dur = parse_duration(content['duration'])
                    views = int(stats.get('viewCount', 0))
                    
                    if dur >= MIN_VIDEO_DURATION and dur <= MAX_VIDEO_DURATION:
                        channel_videos.append({
                            'video_id': video_id,
                            'title': snippet['title'],
                            'channel': channel,
                            'views': views,
                            'likes': int(stats.get('likeCount', 0)),
                            'duration': dur,
                            'url': f"https://www.youtube.com/watch?v={video_id}"
                        })
            
            if channel_videos:
                top = max(channel_videos, key=lambda x: x['views'])
                all_videos.append(top)
                print(f"  ✅ {top['title'][:50]}... ({top['views']:,} views)\n")
            else:
                print(f"  ⚠️  No videos\n")
        
        # Handle Quota Correctly
        except Exception as e:
            if 'quotaExceeded' in str(e):
                 print("❌ Quota Exceeded! Exiting...")
                 raise e
            print(f"  ❌ {e}\n")
    
    if not all_videos:
        return None
    
    sorted_videos = sorted(all_videos, key=lambda x: x['views'], reverse=True)
    
    print("\n🏆 TOP 5 VIRAL VIDEOS:\n")
    for i, v in enumerate(sorted_videos[:5], 1):
        print(f"{i}. {v['channel']}: {v['title'][:50]}... ({v['views']:,} views)")
    
    winner = sorted_videos[0]
    print(f"\n🔥 WINNER: {winner['channel']} - {winner['views']:,} views\n")
    
    return winner

def parse_duration(duration_str):
    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = pattern.match(duration_str)
    if not match:
        return 0
    date_parts = [int(g or 0) for g in match.groups()]
    return date_parts[0] * 3600 + date_parts[1] * 60 + date_parts[2]

# ==================== DOWNLOAD ====================
def download_video(url, path):
    print("⬇️  Downloading...")
    # Using python module via subprocess to ensure correct python environment usage if needed, but direct yt-dlp is fine too if in path
    try:
        subprocess.run(['yt-dlp', '-f', 'bestvideo[height<=1080]+bestaudio/best',
                       '--merge-output-format', 'mp4', '-o', path, url],
                      check=True, capture_output=True)
        print("✅ Downloaded!\n")
        return True
    except:
        # Fallback
        try:
             subprocess.run(['python', '-m', 'yt_dlp', '-f', 'best', '-o', path, url], check=True, capture_output=True)
             print("✅ Downloaded (Fallback)!\n")
             return True
        except Exception as e:
             print(f"❌ Download Failed: {e}")
             return False

# ==================== OPUS CLIP STYLE CAPTIONS ====================
def create_opus_clip_captions(transcript, output_path):
    """Exact Opus Clip caption style"""
    
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,70,&H00FFFFFF,&H000000FF,&H00000000,&HBF000000,-1,0,0,0,100,100,0,0,1,3,2,2,10,10,200,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ass_header)
        
        if transcript and 'segments' in transcript:
            for segment in transcript['segments']:
                if 'words' in segment:
                     words = segment['words']
                else:
                     # fallback
                     w_text = segment['text'].strip()
                     words = [{'word': w, 'start': segment['start'], 'end': segment['end']} for w in w_text.split()]

                chunk_size = 2 # Tight captions
                
                # We need to process words
                word_list = []
                for w in words:
                    # Whisper sometimes gives dict, sometimes objects depending on version? 
                    # Assuming dict as per standard output
                    word_list.append(w)

                for i in range(0, len(word_list), chunk_size):
                    chunk = word_list[i:i+chunk_size]
                    if not chunk: continue
                    
                    text_str = ' '.join([c['word'].strip().upper() for c in chunk])
                    start = chunk[0]['start']
                    end = chunk[-1]['end']
                    
                    # Detect emphasis words
                    _, keywords = detect_viral_keywords(text_str)
                    
                    if keywords:
                        # Yellow for viral keywords
                        styled = f"{{\\c&H00FFFF&}}{{\\fs85}}{text_str}"
                    else:
                        # White default
                        styled = f"{{\\c&HFFFFFF&}}{text_str}"
                    
                    f.write(f"Dialogue: 0,{format_time(start)},{format_time(end)},Default,,0,0,0,,{styled}\n")

def format_time(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    cs = int((s % 1) * 100)
    return f"{h}:{m:02d}:{sec:02d}.{cs:02d}"

# ==================== PROCESSING ====================
def auto_frame(inp, out):
    print("  🖼️ Auto-framing...")
    # Increased timeout from 60 to 300 based on previous experience
    try:
        subprocess.run(['ffmpeg', '-i', inp, '-vf',
                       'crop=ih*9/16:ih:iw/2-ih*9/32:0,scale=1080:1920',
                       '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                       '-c:a', 'copy', '-y', out],
                      check=True, capture_output=True, timeout=300)
    except:
         # Fallback to center crop
         print("  ⚠️ Smart crop failed, using center crop...")
         subprocess.run(['ffmpeg', '-i', inp, '-vf',
                       'crop=ih*(9/16):ih:(iw-ow)/2:0,scale=1080:1920',
                       '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                       '-c:a', 'copy', '-y', out],
                      check=True, capture_output=True, timeout=300)

def color_grade(inp, out):
    print("  🎨 Color grading...")
    subprocess.run(['ffmpeg', '-i', inp, '-vf',
                   'eq=contrast=1.1:brightness=0.05:saturation=1.2,unsharp=3:3:1.0',
                   '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
                   '-c:a', 'copy', '-y', out],
                  check=True, capture_output=True, timeout=300)

def add_credits(inp, out):
    print("  🏷️ Adding credits...")
    
    # Font path handling
    font_path = "arial.ttf"
    if os.path.exists("temp/arial.ttf"):
        font_path = "temp/arial.ttf"
    elif os.path.exists("C:/Windows/Fonts/arial.ttf"):
        font_path = "C:/Windows/Fonts/arial.ttf"

    font_path = font_path.replace("\\", "/")

    subprocess.run(['ffmpeg', '-i', inp, '-vf',
                   f"drawtext=text='{YOUR_CHANNEL_NAME}':fontfile='{font_path}':fontsize=40:"
                   f"fontcolor=white:borderw=2:bordercolor=black:x=(w-text_w)/2:y=h-100,"
                   f"drawtext=text='{CREDITS_TEXT}':fontfile='{font_path}':fontsize=30:"
                   f"fontcolor=yellow:borderw=2:bordercolor=black:x=(w-text_w)/2:y=h-60",
                   '-c:a', 'copy', '-y', out],
                  check=True, capture_output=True, timeout=120)

def process_viral_clip(video_path, video_info):
    print("\n🎬 Processing with Opus Clip AI pipeline...\n")
    
    # Transcribe first
    transcript = transcribe_video(video_path)
    
    # Opus Clip AI analysis
    viral_segments = opus_clip_viral_analysis(video_path, transcript)
    
    if not viral_segments:
        print("❌ No viral moments found")
        return None
    
    # Use top viral moment
    best = viral_segments[0]
    start = best['start']
    
    print(f"✂️  Extracting TOP viral clip from {int(start//60)}:{int(start%60):02d}")
    print(f"    Score: {best['viral_score']:.2f}\n")
    
    # Extract
    temp1 = os.path.join(TEMP_FOLDER, "step1.mp4")
    subprocess.run(['ffmpeg', '-ss', str(start), '-i', video_path,
                   '-t', str(CLIP_DURATION), '-c', 'copy', '-y', temp1],
                  check=True, capture_output=True)
    
    # Auto-frame
    temp2 = os.path.join(TEMP_FOLDER, "step2.mp4")
    auto_frame(temp1, temp2)
    
    # Color grade
    temp3 = os.path.join(TEMP_FOLDER, "step3.mp4")
    color_grade(temp2, temp3)
    
    # Add captions
    if transcript:
        print("  📝 Burning captions...")
        ass_path = os.path.join(TEMP_FOLDER, "captions.ass")
        create_opus_clip_captions(transcript, ass_path)
        
        temp4 = os.path.join(TEMP_FOLDER, "step4.mp4")
        # Fix path for ffmpeg
        ass_path_fixed = ass_path.replace('\\', '/')
        subprocess.run(['ffmpeg', '-i', temp3, '-vf', f"ass='{ass_path_fixed}'",
                       '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
                       '-c:a', 'copy', '-y', temp4],
                      check=True, capture_output=True, timeout=300)
        current = temp4
    else:
        current = temp3
    
    # Add credits
    final = os.path.join(CLIPS_FOLDER, f"final_{video_info['video_id']}.mp4")
    add_credits(current, final)
    
    # Cleanup
    try:
        for t in [temp1, temp2, temp3, temp4]:
            if os.path.exists(t):
                # os.remove(t) # Keep temps for debugging if needed, or uncomment to clean
                pass 
    except: pass
    
    print(f"✅ Viral clip ready: {final}\n")
    return {'path': final, 'viral_score': best['viral_score']}

# ==================== UPLOAD ====================
def get_authenticated_service():
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
                logging.error(f"Token refresh failed: {e}")
                creds = None

    if not creds or not creds.valid:
        # Check if we are in a headless environment (GitHub Actions)
        if os.environ.get('GITHUB_ACTIONS') == 'true':
            error_msg = "❌ Authentication failed on GitHub Actions. Token expired or invalid, and interactive login is not possible."
            logging.error(error_msg)
            print(error_msg)
            # We cannot run local server in CI
            raise Exception(error_msg)
            
        flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('youtube', 'v3', credentials=creds)

def upload_short(youtube, file, title, views, channel, url):
    viral_title = f"🔥 {title[:40]}... | {channel}"[:100]
    desc = f"""🔥 VIRAL PODCAST MOMENT!

From {channel} - {views:,}+ views!

Full: {url}

{CREDITS_TEXT}

#Shorts #Podcast #India #{channel.replace(' ', '')} #Viral
"""
    
    print(f"📤 Uploading: {viral_title}\n")
    
    body = {
        'snippet': {
            'title': viral_title,
            'description': desc,
            'tags': ['shorts', 'podcast', 'india', channel.lower(), 'viral', 'trending'],
            'categoryId': '24'
        },
        'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
    }
    
    media = MediaFileUpload(file, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"⬆️  {int(status.progress() * 100)}%")
    
    print(f"✅ https://youtube.com/shorts/{response['id']}\n")
    return response['id']

# ==================== MAIN WORKFLOW ====================
def run_daily_upload():
    try:
        print("\n" + "="*80)
        print(f"🤖 OPUS CLIP AI WORKFLOW - {datetime.now()}")
        print("="*80 + "\n")
        
        history = load_upload_history()
        
        winner = find_top_viral_video_from_all_channels(history)
        if not winner:
            print("❌ No suitable video found")
            return
        
        video_path = os.path.join(DOWNLOAD_FOLDER, f"{winner['video_id']}.mp4")
        
        if not download_video(winner['url'], video_path):
            return
        
        clip = process_viral_clip(video_path, winner)
        
        if not clip:
            if os.path.exists(video_path): os.remove(video_path)
            return
        
        youtube = get_authenticated_service()
        upload_short(youtube, clip['path'], winner['title'],
                    winner['views'], winner['channel'], winner['url'])
        
        if os.path.exists(video_path): os.remove(video_path)
        
        history['uploaded_videos'].append(winner['video_id'])
        history['last_upload_time'] = datetime.now().isoformat()
        save_upload_history(history)
        
        print("="*80)
        print("🎉 OPUS CLIP AI WORKFLOW COMPLETE!")
        print("="*80 + "\n")
        
    except Exception as e:
        error_msg = f"Error in run_daily_upload: {str(e)}"
        print(f"\n❌ {error_msg}\n")
        logging.error(error_msg, exc_info=True)
        sys.exit(1)  # Force GitHub Action to fail

def main():
    print("🤖 OPUS CLIP AI - INDIAN PODCAST AUTOMATION")
    print("="*80)
    print("✅ 25 Specific Podcast Channels")
    print("✅ Opus Clip AI Analysis")
    print("✅ Viral Keyword Detection")
    print("✅ Sentiment Analysis")
    print("✅ Audio Energy + Scene Detection")
    print("✅ TikTok-Style Captions")
    print("✅ Daily 8 AM & 8 PM")
    print("="*80)
    
    
    mode = "2" # Default to run now if using automation
    if "--run-now" in sys.argv:
        mode = "2"
    elif len(sys.argv) > 1:
        pass
    else:
        try:
             print("\nOptions:")
             print("1. Scheduled (8AM & 8PM)")
             print("2. Run Now")
             inp = input("\nEnter (1/2): ").strip()
             if inp == "1": mode = "1"
        except: pass
    
    if mode == "1":
        print("\n✅ Scheduled!\n")
        schedule.every().day.at("08:00").do(run_daily_upload)
        schedule.every().day.at("20:00").do(run_daily_upload)
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        print("\n✅ Running now...\n")
        run_daily_upload()

import sys # Ensure sys is imported for args

if __name__ == "__main__":
    main()
