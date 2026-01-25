"""
Keep-Alive Web Server for Render.com
This Flask server keeps the Render web service alive and runs scheduled automation.
"""

import os
import threading
import time
from datetime import datetime
from flask import Flask
import schedule
import subprocess
import sys

app = Flask(__name__)

# Track last run status
last_run_status = {
    "last_run": None,
    "status": "Not started yet",
    "next_run": None
}

def run_automation():
    """Run the YouTube automation script"""
    global last_run_status
    
    print(f"\n{'='*60}")
    print(f"🤖 STARTING AUTOMATION - {datetime.now()}")
    print(f"{'='*60}\n")
    
    last_run_status["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    last_run_status["status"] = "Running..."
    
    try:
        # Run the automation script
        result = subprocess.run(
            [sys.executable, "automate_viral_channels.py"],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            last_run_status["status"] = "✅ Success"
            print("\n✅ Automation completed successfully!")
        else:
            last_run_status["status"] = f"❌ Failed (exit code {result.returncode})"
            print(f"\n❌ Automation failed with exit code {result.returncode}")
            print(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        last_run_status["status"] = "⏱️ Timeout (>1 hour)"
        print("\n⏱️ Automation timed out after 1 hour")
    except Exception as e:
        last_run_status["status"] = f"❌ Error: {str(e)}"
        print(f"\n❌ Error running automation: {e}")
    
    print(f"\n{'='*60}")
    print(f"🏁 AUTOMATION FINISHED - {datetime.now()}")
    print(f"{'='*60}\n")

def schedule_jobs():
    """Schedule automation to run at 8 AM and 8 PM IST"""
    # IST is UTC+5:30
    # 8:00 AM IST = 2:30 AM UTC
    # 8:00 PM IST = 2:30 PM UTC
    
    schedule.every().day.at("02:30").do(run_automation)  # 8 AM IST
    schedule.every().day.at("14:30").do(run_automation)  # 8 PM IST
    
    print("📅 Scheduled automation:")
    print("   - 8:00 AM IST (2:30 AM UTC)")
    print("   - 8:00 PM IST (2:30 PM UTC)")
    
    # Update next run time
    next_job = schedule.next_run()
    if next_job:
        last_run_status["next_run"] = next_job.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Run scheduler in background thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
            # Update next run time
            next_job = schedule.next_run()
            if next_job:
                last_run_status["next_run"] = next_job.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("✅ Background scheduler started!")

@app.route('/')
def home():
    """Health check endpoint"""
    return f"""
    <html>
    <head>
        <title>YouTube Automation Bot</title>
        <meta http-equiv="refresh" content="30">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 800px; margin: 40px auto; }}
            h1 {{ color: #333; }}
            .status {{ padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .success {{ background: #d4edda; color: #155724; }}
            .running {{ background: #fff3cd; color: #856404; }}
            .error {{ background: #f8d7da; color: #721c24; }}
            .info {{ background: #d1ecf1; color: #0c5460; }}
            code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
            .test-button {{ 
                display: inline-block;
                background: #28a745;
                color: white;
                padding: 15px 30px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: bold;
                font-size: 18px;
                margin: 20px 0;
                transition: background 0.3s;
                border: none;
                cursor: pointer;
            }}
            .test-button:hover {{ background: #218838; }}
            .button-container {{ text-align: center; margin: 30px 0; }}
            .warning {{ background: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 YouTube Automation Bot</h1>
            
            <div class="status info">
                <strong>Status:</strong> Server is running ✅
            </div>
            
            <div class="status info">
                <strong>Last Run:</strong> {last_run_status['last_run'] or 'Never'}
            </div>
            
            <div class="status {'success' if '✅' in last_run_status['status'] else 'error' if '❌' in last_run_status['status'] else 'running'}">
                <strong>Last Status:</strong> {last_run_status['status']}
            </div>
            
            <div class="status info">
                <strong>Next Scheduled Run:</strong> {last_run_status['next_run'] or 'Calculating...'}
            </div>
            
            <hr>
            
            <div class="button-container">
                <a href="/trigger" class="test-button">🚀 RUN TEST NOW</a>
            </div>
            
            <div class="warning">
                <strong>⚠️ Note:</strong> Test run may take 10-15 minutes to complete. 
                The page will auto-refresh to show progress. Check "Last Status" for results.
            </div>
            
            <hr>
            
            <h3>📅 Automatic Schedule</h3>
            <ul>
                <li>8:00 AM IST (2:30 AM UTC)</li>
                <li>8:00 PM IST (2:30 PM UTC)</li>
            </ul>
            
            <p><em>Page auto-refreshes every 30 seconds</em></p>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """Simple health check for monitoring"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.route('/trigger')
def trigger():
    """Manual trigger endpoint (for testing)"""
    threading.Thread(target=run_automation, daemon=True).start()
    return """
    <html>
    <head>
        <meta http-equiv="refresh" content="2;url=/">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 100px; background: #f5f5f5; }
            .message { background: white; padding: 40px; border-radius: 10px; display: inline-block; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #28a745; }
        </style>
    </head>
    <body>
        <div class="message">
            <h1>✅ Test Started!</h1>
            <p>Automation is now running in the background...</p>
            <p>Redirecting back to dashboard...</p>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 YOUTUBE AUTOMATION SERVER STARTING")
    print("="*60 + "\n")
    
    # Schedule jobs
    schedule_jobs()
    
    # Get port from environment (Render sets this)
    port = int(os.environ.get('PORT', 5000))
    
    print(f"\n🌐 Server will run on port {port}")
    print(f"📍 Health check: http://localhost:{port}/")
    print(f"🔧 Manual trigger: http://localhost:{port}/trigger")
    print("\n" + "="*60 + "\n")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
