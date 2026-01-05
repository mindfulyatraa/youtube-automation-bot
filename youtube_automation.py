import os
import sys
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
YOUTUBE_API_KEY = "AIzaSyDOXwfmQQnhw2P3FHauy_q0skaDd4i2Xqg"  # YouTube Data API key
DOWNLOAD_FOLDER = "downloads"
CLIPS_FOLDER = "clips"
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Shorts settings
CLIP_DURATION = 45  # seconds (max 60 for shorts)
MIN_VIEWS_THRESHOLD = 100000  # Minimum views for viral videos

# Automation settings
# UPLOAD_INTERVAL_HOURS = 10  # (Removed in favor of fixed daily schedule)
AUTO_UPLOAD = True  # Automatic upload on/off
CLIPS_PER_CYCLE = 1  # Har cycle me kitne clips upload karne hain

# Search queries rotation (variety ke liye)
SEARCH_QUERIES = [
    "podcast highlights usa",
    "viral moments usa",
    "trending podcast clips",
    "best podcast moments",
    "viral interview clips",
    "motivational speeches",
    "funny moments viral"
]

# ==================== SETUP ====================
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(CLIPS_FOLDER, exist_ok=True)

# Upload history track karne ke liye
UPLOAD_HISTORY_FILE = "upload_history.json"

def load_upload_history():
    """Purane uploads ka record load karta hai"""
    if os.path.exists(UPLOAD_HISTORY_FILE):
        with open(UPLOAD_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {'uploaded_videos': [], 'last_upload_time': None}

def save_upload_history(history):
    """Upload history save karta hai"""
    with open(UPLOAD_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def is_already_processed(video_id, history):
    """Check karta hai ki video already process ho chuki hai"""
    return video_id in history['uploaded_videos']

# ==================== VIRAL TITLE & DESCRIPTION GENERATOR ====================
def generate_viral_title(original_title, clip_number):
    """Viral title generate karta hai"""
    
    # Viral keywords
    viral_words = [
        "🔥", "💯", "🚨", "⚡", "😱", 
        "SHOCKING", "INSANE", "VIRAL", "MUST WATCH", 
        "WOW", "MIND BLOWING", "CRAZY", "UNBELIEVABLE"
    ]
    
    # Title se important keywords nikalo
    words = re.findall(r'\b\w+\b', original_title)
    important_words = [w for w in words if len(w) > 4][:3]
    
    # Different viral title patterns
    patterns = [
        f"🔥 {' '.join(important_words[:2]).upper()} | Viral Moment #{clip_number}",
        f"😱 SHOCKING: {' '.join(important_words[:2])} | Must Watch",
        f"⚡ {important_words[0] if important_words else 'VIRAL'} Moment That Broke Internet 🚨",
        f"💯 This {important_words[0] if important_words else 'Video'} Went VIRAL! #{clip_number}",
        f"🚨 You Won't Believe This: {' '.join(important_words[:2])}",
        f"INSANE {important_words[0] if important_words else 'Moment'} 🔥 | Viral Short"
    ]
    
    # Random pattern select karo
    title = random.choice(patterns)
    
    # Length limit (max 100 chars for YouTube)
    if len(title) > 95:
        title = title[:95] + "..."
    
    return title

def generate_viral_description(original_title, views, video_url):
    """Viral description generate karta hai"""
    
    description_templates = [
        f"""🔥 THIS WENT VIRAL! 🔥

From a video with {views:,} views! This moment broke the internet 💯

Original video has millions of views and this is the BEST part! 

Watch till the end! ⚡

🎯 Follow for more viral content!
👍 Like if you enjoyed!
💬 Comment your thoughts!
🔔 Turn on notifications!

Full video: {video_url}

""",
        f"""😱 MIND = BLOWN 😱

This clip is from a MEGA VIRAL video ({views:,} views)!

Everyone is talking about this moment! 🚨

If you're not watching this, you're missing out! 💯

👉 FOLLOW for daily viral content
❤️ LIKE if this amazed you
💭 COMMENT what you think
🔔 TURN ON notifications

Source: {video_url}

""",
        f"""⚡ VIRAL ALERT ⚡

{views:,} views and counting! This is THE moment everyone's sharing 🔥

You NEED to see this! 💯

Hit that LIKE button if you loved it! 👍
FOLLOW for more viral shorts! 🚀
COMMENT your reaction! 💬

Full version: {video_url}

"""
    ]
    
    base_description = random.choice(description_templates)
    
    # Hashtags add karo
    hashtags = """
#Shorts #Viral #Trending #MustWatch #Viral2025 #ViralVideo #YouTubeShorts 
#Trending2025 #Amazing #Unbelievable #MindBlowing #Epic #BestMoments 
#ViralShorts #TrendingShorts #ExplorePage #ForYou #FYP #Wow #Insane
"""
    
    return base_description + hashtags

def generate_viral_tags():
    """Viral tags generate karta hai (500 character limit)"""
    
    tags = [
        # Core shorts tags
        "shorts", "viral", "trending", "youtube shorts", "viral shorts",
        "trending shorts", "viral video", "trending video",
        
        # Engagement tags  
        "must watch", "mind blowing", "shocking", "amazing", "unbelievable",
        "insane", "epic", "wow", "crazy", "best moments",
        
        # Year specific
        "2025", "viral 2025", "trending 2025", "best of 2025",
        
        # USA audience
        "usa", "america", "us trending", "us viral",
        
        # General viral
        "viral content", "viral clips", "trending now", "going viral",
        "internet breaking", "everyone watching", "must see",
        
        # Algorithm friendly
        "for you", "fyp", "explore", "recommended", "suggested"
    ]
    
    # Shuffle and return (YouTube accepts up to 500 chars total)
    random.shuffle(tags)
    return tags[:30]  # Top 30 tags

# ==================== STEP 1: FIND VIRAL VIDEOS ====================
def find_viral_videos(query="podcast highlights", max_results=5, history=None):
    """YouTube se viral videos dhoondhta hai (already processed videos skip karta hai)"""
    print("🔍 Viral videos search kar raha hoon...")
    
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # Last 7 days ki trending videos
    published_after = (datetime.now() - timedelta(days=7)).isoformat() + 'Z'
    
    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        order="viewCount",
        publishedAfter=published_after,
        maxResults=max_results * 2,  # Extra fetch karo filtering ke liye
        regionCode="US",
        relevanceLanguage="en"
    )
    
    response = request.execute()
    
    viral_videos = []
    for item in response['items']:
        video_id = item['id']['videoId']
        
        # Skip if already processed
        if history and is_already_processed(video_id, history):
            print(f"⏭️  Skipping (already processed): {item['snippet']['title'][:50]}")
            continue
        
        # Video details get karo (views, duration)
        video_details = youtube.videos().list(
            part="statistics,contentDetails",
            id=video_id
        ).execute()
        
        if video_details['items']:
            stats = video_details['items'][0]['statistics']
            duration = video_details['items'][0]['contentDetails']['duration']
            
            views = int(stats.get('viewCount', 0))
            
            if views >= MIN_VIEWS_THRESHOLD:
                viral_videos.append({
                    'video_id': video_id,
                    'title': item['snippet']['title'],
                    'views': views,
                    'url': f"https://www.youtube.com/watch?v={video_id}"
                })
                print(f"✅ Found: {item['snippet']['title']} - {views:,} views")
                
                if len(viral_videos) >= max_results:
                    break
    
    return viral_videos

# Adjust path to ffmpeg
FFMPEG_BINARY = "ffmpeg.exe"
if os.path.exists(os.path.abspath(FFMPEG_BINARY)):
    FFMPEG_BINARY = os.path.abspath(FFMPEG_BINARY)

def get_video_duration(video_path):
    """Video duration nikalta hai ffmpeg use karke (ffprobe fallback)"""
    try:
        command = [FFMPEG_BINARY, '-i', video_path]
        result = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        # Search for Duration: 00:00:00.00
        match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})", result.stderr)
        if match:
            h, m, s = map(float, match.groups())
            return h*3600 + m*60 + s
    except Exception as e:
        print(f"Error getting duration: {e}")
    return 0

# ==================== STEP 2: DOWNLOAD VIDEO ====================
def download_video(video_url, output_path):
    """yt-dlp se video download karta hai"""
    print(f"⬇️  Video download ho raha hai: {video_url}")
    
    # Use python -m yt_dlp instead of direct executable to ensure it runs
    command = [
        sys.executable, '-m', 'yt_dlp',
        '-f', 'bestvideo[height<=1080]+bestaudio/best',
        '--merge-output-format', 'mp4',
        '-o', output_path,
        video_url
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True)
        print(f"✅ Download complete: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Download failed: {e}")
        return False

# ==================== STEP 3: EXTRACT VIRAL CLIPS ====================
def extract_clips(video_path, video_info, num_clips=3):
    """Video se multiple clips extract karta hai"""
    print(f"✂️  Clips extract ho rahe hain...")
    
    # Video duration nikalo
    duration = get_video_duration(video_path)
    if duration == 0:
        print("❌ Could not determine video duration")
        return []
    
    clips = []
    
    # Multiple clips nikalo different timestamps se
    for i in range(num_clips):
        # Random start time (but leave room for clip duration)
        max_start = duration - CLIP_DURATION - 10
        if max_start < 0:
            max_start = 0
        
        start_time = random.uniform(10, max_start) if max_start > 10 else 0
        
        clip_filename = f"clip_{video_info['video_id']}_{i+1}_{int(start_time)}.mp4"
        clip_path = os.path.join(CLIPS_FOLDER, clip_filename)
        
        # FFmpeg se clip extract karo (vertical format for shorts)
        command = [
            FFMPEG_BINARY,
            '-ss', str(start_time),
            '-i', video_path,
            '-t', str(CLIP_DURATION),
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-y',
            clip_path
        ]
        
        try:
            subprocess.run(command, check=True, capture_output=True)
            print(f"✅ Clip {i+1} created: {clip_filename}")
            clips.append({
                'path': clip_path,
                'filename': clip_filename,
                'start_time': start_time
            })
        except subprocess.CalledProcessError as e:
            print(f"❌ Clip {i+1} failed: {e}")
    
    return clips

# ==================== STEP 4: UPLOAD TO YOUTUBE SHORTS ====================
def get_authenticated_service():
    """YouTube upload ke liye authentication"""
    credentials = None
    
    if os.path.exists('token.json'):
        credentials = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secrets.json', SCOPES)
        credentials = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(credentials.to_json())
    
    return build('youtube', 'v3', credentials=credentials)

def upload_short(youtube, video_file, original_title, original_views, video_url, clip_number):
    """YouTube short upload karta hai with VIRAL title, description & tags"""
    
    # Viral title, description aur tags generate karo
    viral_title = generate_viral_title(original_title, clip_number)
    viral_description = generate_viral_description(original_title, original_views, video_url)
    viral_tags = generate_viral_tags()
    
    print(f"📤 Uploading with VIRAL metadata:")
    print(f"   Title: {viral_title}")
    print(f"   Tags: {len(viral_tags)} viral tags")
    
    body = {
        'snippet': {
            'title': viral_title,
            'description': viral_description,
            'tags': viral_tags,
            'categoryId': '24'  # Entertainment
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }
    
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    
    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")
    
    print(f"✅ Uploaded! Video ID: {response['id']}")
    print(f"   URL: https://youtube.com/shorts/{response['id']}\n")
    
    return response['id']

# ==================== MAIN WORKFLOW ====================
def run_upload_cycle():
    """Ek complete upload cycle chalata hai"""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("\n" + "="*60)
        print(f"🚀 Upload Cycle Started: {current_time}")
        print("="*60 + "\n")
        
        # Upload history load karo
        history = load_upload_history()
        
        # Random search query select karo (variety ke liye)
        search_query = random.choice(SEARCH_QUERIES)
        print(f"🔎 Search Query: {search_query}\n")
        
        # Step 1: Viral videos dhoondhna
        viral_videos = find_viral_videos(query=search_query, max_results=2, history=history)
        
        if not viral_videos:
            print("❌ Koi naye viral videos nahi mile! Next cycle me try karenge.")
            return
        
        print(f"\n✅ {len(viral_videos)} naye viral videos mile!\n")
        
        # Step 2-3: Download aur clips extract karna
        all_clips = []
        processed_video_ids = []
        
        for video in viral_videos:
            video_path = os.path.join(DOWNLOAD_FOLDER, f"{video['video_id']}.mp4")
            
            # Download
            if download_video(video['url'], video_path):
                # Extract clips (limited to CLIPS_PER_CYCLE)
                clips = extract_clips(video_path, video, num_clips=CLIPS_PER_CYCLE)
                
                for clip in clips:
                    clip['original_title'] = video['title']
                    clip['original_views'] = video['views']
                    clip['video_url'] = video['url']
                    all_clips.append(clip)
                
                processed_video_ids.append(video['video_id'])
                
                # Original video delete karo
                os.remove(video_path)
                print(f"🗑️  Original video deleted: {video_path}\n")
                
                # Agar enough clips mil gaye to stop
                if len(all_clips) >= CLIPS_PER_CYCLE:
                    break
        
        if not all_clips:
            print("❌ Clips nahi ban sake!")
            return
        
        print(f"\n✅ {len(all_clips)} clips ready for upload!\n")
        
        # Step 4: YouTube pe upload
        youtube = get_authenticated_service()
        uploaded_count = 0
        
        for i, clip in enumerate(all_clips[:CLIPS_PER_CYCLE]):
            try:
                video_id = upload_short(
                    youtube, 
                    clip['path'], 
                    clip['original_title'],
                    clip['original_views'],
                    clip['video_url'],
                    i+1
                )
                uploaded_count += 1
                print(f"✅ Clip {i+1} uploaded successfully!\n")
                
                # Small delay to avoid rate limits
                time.sleep(5)
                
            except Exception as e:
                print(f"❌ Upload failed for clip {i+1}: {e}\n")
        
        # Update history
        history['uploaded_videos'].extend(processed_video_ids)
        history['last_upload_time'] = current_time
        save_upload_history(history)
        
        print("\n" + "="*60)
        print(f"🎉 Cycle Complete! {uploaded_count} clips uploaded")
        print(f"⏰ Next upload: As per schedule (09:00 AM / 08:00 PM)")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Cycle error: {e}\n")
        print("⏰ Will retry in next cycle...\n")

def main():
    """Main function - automated mode ya manual mode"""
    print("🚀 YouTube Viral Shorts Automation")
    print("="*60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        mode = "2"
    else:
        mode = input("\nKaunsa mode chahiye?\n1. Automated (har 10 ghante)\n2. Manual (ek baar run)\n\nEnter (1/2): ").strip()
    
    if mode == "1":
        print(f"\n✅ Automated mode activated!")
        print(f"⏰ Uploads scheduled: Daily at 09:00 AM and 08:00 PM")
        print(f"📊 Clips per cycle: {CLIPS_PER_CYCLE}")
        print("\n🔄 Press Ctrl+C to stop\n")
        
        # Schedule setup - 9 AM aur 8 PM
        schedule.every().day.at("09:00").do(run_upload_cycle)
        schedule.every().day.at("20:00").do(run_upload_cycle)
        
        # Infinite loop - scheduler chalata rahega
        while True:
            schedule.run_pending()
            time.sleep(60)  # Har minute check karo
            
    else:
        # Manual mode - ek baar run
        print("\n✅ Manual mode - Running once...\n")
        run_upload_cycle()
        print("\n✅ Manual run complete!")
        print(f"📁 Clips saved in: {CLIPS_FOLDER}")
        sys.exit(0) # Exit cleanly for GitHub Actions

if __name__ == "__main__":
    main()
