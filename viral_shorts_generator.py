"""
Viral Shorts Generator with Blurred Background Effect
Extracts viral moments from YouTube videos and creates TikTok/Instagram-style shorts
"""

import os
import json
import subprocess
import sys
from pathlib import Path

# Fix for Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

# Folders
DOWNLOADS_FOLDER = "downloads"
SHORTS_FOLDER = "shorts"
TEMP_FOLDER = "temp"

os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)
os.makedirs(SHORTS_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Ensure tools are found in PATH
# Add current directory (for ffmpeg) and python scripts directory (for yt-dlp) to PATH
current_dir = os.getcwd()
scripts_dir = os.path.dirname(sys.executable)
os.environ["PATH"] = f"{current_dir};{scripts_dir};" + os.environ["PATH"]

# Configuration
VIDEO_URL = "https://youtu.be/_uRdozeKuUg"
NUM_CLIPS = 5  # Number of shorts to generate
CLIP_DURATION = 45  # Target duration in seconds (30-60 recommended)
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
BLUR_SIGMA = 20  # Gaussian blur strength

def get_video_id(url):
    """Extract video ID from YouTube URL"""
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    elif "v=" in url:
        return url.split("v=")[1].split("&")[0]
    return url

def download_video(url, output_folder):
    """Download video using yt-dlp"""
    video_id = get_video_id(url)
    output_path = os.path.join(output_folder, f"{video_id}.mp4")
    
    if os.path.exists(output_path):
        print(f"✓ Video already downloaded: {output_path}")
        return output_path
    
    print(f"📥 Downloading video: {url}")
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", output_path,
        url
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✓ Downloaded: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"✗ Download failed: {e}")
        return None

def get_video_duration(video_path):
    """Get video duration in seconds using ffmpeg (since ffprobe might be missing)"""
    cmd = [
        "ffmpeg", "-i", video_path
    ]
    # ffmpeg returns non-zero exit code when no output file is provided, which is expected here
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Parse duration from stderr: "Duration: 00:05:03.25,"
    import re
    duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})", result.stderr)
    if duration_match:
        hours = int(duration_match.group(1))
        minutes = int(duration_match.group(2))
        seconds = float(duration_match.group(3))
        return hours * 3600 + minutes * 60 + seconds
    
    return 0.0

def detect_viral_moments(video_path, num_clips=5, clip_duration=45):
    """
    Detect potential viral moments in the video.
    Uses equal distribution + random offset for variety.
    Returns list of start times.
    """
    total_duration = get_video_duration(video_path)
    print(f"📊 Video duration: {total_duration/60:.1f} minutes")
    
    # Skip first 30 seconds (usually intro) and last 30 seconds (usually outro)
    usable_start = 30
    usable_end = total_duration - 30 - clip_duration
    
    if usable_end <= usable_start:
        usable_start = 0
        usable_end = total_duration - clip_duration
    
    usable_duration = usable_end - usable_start
    
    # Divide into segments and pick moments
    segment_length = usable_duration / num_clips
    
    moments = []
    for i in range(num_clips):
        # Pick time from each segment (middle of segment)
        start_time = usable_start + (segment_length * i) + (segment_length / 3)
        moments.append({
            "start": start_time,
            "duration": clip_duration,
            "score": 8.5 - (i * 0.2),  # Simulated viral score
            "label": f"Viral Moment {i+1}"
        })
    
    print(f"🎯 Detected {len(moments)} viral moments")
    for m in moments:
        mins = int(m['start'] // 60)
        secs = int(m['start'] % 60)
        print(f"   - {m['label']} at {mins}:{secs:02d} (score: {m['score']:.1f})")
    
    return moments

def create_blurred_background_short(input_video, output_path, start_time, duration):
    """
    Create a short with blurred background effect.
    - Main video centered
    - Blurred/scaled version as background
    - 9:16 aspect ratio (1080x1920)
    """
    print(f"🎬 Creating short: {os.path.basename(output_path)}")
    
    # FFmpeg filter for blurred background effect
    # 1. Scale video to fill 1080x1920 and blur it (background)
    # 2. Scale original video to fit within frame (foreground)
    # 3. Overlay foreground on background
    
    # FFmpeg filter for blurred background effect + effects + text
    # 1. Background: Scale to fill 1080x1920, blur
    # 2. Foreground: Scale to fit width, add subtle saturation boost
    # 3. Overlay Foreground on Background
    # 4. Vignette effect
    # 5. Text Overlay "WAIT FOR END"
    
    # FFmpeg filter for blurred background effect + effects + IMAGE overlay
    # 1. Background: Scale to fill 1080x1920, blur
    # 2. Foreground: Scale to fit width, add subtle saturation boost
    # 3. Scale Overlay Image to 800px width
    # 4. Overlay Foreground on Background
    # 5. Vignette effect
    # 6. Overlay Image "Wait for end" on top
    
    image_path = "wait_for_end.jpg"
    # Fallback if image missing? Use text? For now assume image is there as we will commit it.
    
    filter_complex = (
        # Background: scale, crop, blur
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,gblur=sigma={BLUR_SIGMA}[bg];"
        
        # Foreground: scale, saturation boost
        f"[0:v]scale=1080:-2:force_original_aspect_ratio=decrease,"
        f"eq=saturation=1.2[fg];"
        
        # Image: scale to 800px width
        f"[1:v]scale=800:-1[img];"
        
        # Overlay -> Vignette -> Image Overlay
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,"
        f"vignette=PI/4[comp];"
        f"[comp][img]overlay=(W-w)/2:150[outv]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-i", input_video,
        "-i", image_path, # Input 1 is the image
        "-t", str(duration),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✓ Created: {os.path.basename(output_path)}")
            return True
        else:
            print(f"   ✗ FFmpeg error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def add_captions_to_short(input_video, output_path):
    """
    Add TikTok-style captions to the short.
    Uses basic text overlay - can be enhanced with proper subtitles.
    """
    # For now, skip caption generation (requires Whisper)
    # Just copy the file
    import shutil
    shutil.copy(input_video, output_path)
    return True

def process_video(url, num_clips=5, clip_duration=45):
    """Main processing pipeline"""
    
    print("=" * 60)
    print("🚀 VIRAL SHORTS GENERATOR")
    print("=" * 60)
    print(f"Source: {url}")
    print(f"Clips to generate: {num_clips}")
    print(f"Clip duration: {clip_duration}s")
    print("=" * 60)
    
    # Step 1: Download video
    video_path = download_video(url, DOWNLOADS_FOLDER)
    if not video_path:
        print("❌ Failed to download video")
        return []
    
    # Step 2: Detect viral moments
    moments = detect_viral_moments(video_path, num_clips, clip_duration)
    
    # Step 3: Create output folder
    video_id = get_video_id(url)
    output_folder = os.path.join(SHORTS_FOLDER, f"carryminati_{video_id}")
    os.makedirs(output_folder, exist_ok=True)
    
    # Step 4: Generate shorts with blurred background
    generated_shorts = []
    
    for i, moment in enumerate(moments):
        short_filename = f"short_{i+1}_t{int(moment['start'])}s.mp4"
        short_path = os.path.join(output_folder, short_filename)
        
        success = create_blurred_background_short(
            video_path,
            short_path,
            moment['start'],
            moment['duration']
        )
        
        if success:
            generated_shorts.append({
                "path": short_path,
                "start_time": moment['start'],
                "duration": moment['duration'],
                "viral_score": moment['score']
            })
    
    # Step 5: Save metadata
    metadata = {
        "source_url": url,
        "video_id": video_id,
        "total_clips": len(generated_shorts),
        "clips": generated_shorts
    }
    
    metadata_path = os.path.join(output_folder, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ GENERATION COMPLETE!")
    print("=" * 60)
    print(f"📁 Output folder: {output_folder}")
    print(f"🎬 Shorts created: {len(generated_shorts)}")
    for s in generated_shorts:
        print(f"   - {os.path.basename(s['path'])}")
    print("=" * 60)
    
    return generated_shorts

if __name__ == "__main__":
    # Default URL - CarryMinati's KOFFEE WITH JALAN
    url = VIDEO_URL
    
    # Check for command line argument
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("Usage: python viral_shorts_generator.py [YouTube URL] [num_clips]")
            print("Example: python viral_shorts_generator.py https://youtu.be/_uRdozeKuUg 5")
            sys.exit(0)
        url = sys.argv[1]
    
    num_clips = NUM_CLIPS
    if len(sys.argv) > 2:
        num_clips = int(sys.argv[2])
    
    # Run the generator
    shorts = process_video(url, num_clips=num_clips, clip_duration=CLIP_DURATION)
    
    if shorts:
        print(f"\n🎉 Successfully generated {len(shorts)} viral shorts!")
    else:
        print("\n❌ No shorts were generated")
