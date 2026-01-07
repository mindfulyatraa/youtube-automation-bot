import os
import sys
from youtube_automation import opus_clip_viral_analysis, transcribe_video

def test_ai_on_local_file(file_path):
    print(f"🧪 Testing Opus Clip AI on: {file_path}")
    
    if not os.path.exists(file_path):
        print("❌ File not found!")
        return

    # 1. Transcribe
    print("\n1️⃣ Running Whisper Transcription...")
    transcript = transcribe_video(file_path)
    
    # 2. Opus AI Analysis
    print("\n2️⃣ Running Opus Clip Analysis...")
    opus_clip_viral_analysis(file_path, transcript)

if __name__ == "__main__":
    # Use the first argument or a default file
    target = sys.argv[1] if len(sys.argv) > 1 else r"clips\final_TUDAhyaYS9g.mp4"
    test_ai_on_local_file(target)
