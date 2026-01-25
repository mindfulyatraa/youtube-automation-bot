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
    "next_run": None,
    "error_log": None,
    "output_log": None,
    "progress": None
}

def run_automation():
    """Run the YouTube automation script"""
    global last_run_status
    
    print(f"\n{'='*60}")
    print(f"🤖 STARTING AUTOMATION - {datetime.now()}")
    print(f"{'='*60}\n")
    
    last_run_status["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    last_run_status["status"] = "🔄 Running..."
    last_run_status["progress"] = "Starting automation..."
    last_run_status["error_log"] = None
    last_run_status["output_log"] = None
    
    try:
        # Run the automation script
        last_run_status["progress"] = "Executing script..."
        
        result = subprocess.run(
            [sys.executable, "automate_viral_channels.py"],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        # Store output logs
        last_run_status["output_log"] = result.stdout[-2000:] if result.stdout else "No output"
        
        if result.returncode == 0:
            last_run_status["status"] = "✅ Success"
            last_run_status["progress"] = "Completed successfully!"
            last_run_status["error_log"] = None
            print("\n✅ Automation completed successfully!")
        else:
            last_run_status["status"] = f"❌ Failed (exit code {result.returncode})"
            last_run_status["progress"] = "Failed - check error log below"
            last_run_status["error_log"] = result.stderr[-2000:] if result.stderr else "No error details available"
            print(f"\n❌ Automation failed with exit code {result.returncode}")
            print(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        last_run_status["status"] = "⏱️ Timeout (>1 hour)"
        last_run_status["progress"] = "Timed out after 1 hour"
        last_run_status["error_log"] = "Process exceeded 1 hour timeout limit"
        print("\n⏱️ Automation timed out after 1 hour")
    except Exception as e:
        last_run_status["status"] = f"❌ Error: {str(e)}"
        last_run_status["progress"] = "Exception occurred"
        last_run_status["error_log"] = str(e)
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
    
    # Determine status color
    status_class = 'success' if '✅' in last_run_status['status'] else 'error' if '❌' in last_run_status['status'] else 'running'
    
    # Build error log section
    error_section = ""
    if last_run_status.get('error_log'):
        error_section = f"""
            <details open>
                <summary style="cursor: pointer; font-weight: bold; color: #721c24; padding: 10px; background: #f8d7da; border-radius: 5px; margin: 10px 0;">
                    ❌ Error Details (Click to expand/collapse)
                </summary>
                <pre style="background: #f8d7da; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; max-height: 300px; overflow-y: auto;">{last_run_status['error_log']}</pre>
            </details>
        """
    
    # Build output log section
    output_section = ""
    if last_run_status.get('output_log'):
        output_section = f"""
            <details>
                <summary style="cursor: pointer; font-weight: bold; color: #0c5460; padding: 10px; background: #d1ecf1; border-radius: 5px; margin: 10px 0;">
                    📋 Output Log (Click to expand/collapse)
                </summary>
                <pre style="background: #d1ecf1; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; max-height: 300px; overflow-y: auto;">{last_run_status['output_log']}</pre>
            </details>
        """
    
    # Build progress section
    progress_section = ""
    if last_run_status.get('progress'):
        progress_class = 'running' if '🔄' in last_run_status['status'] else 'info'
        progress_section = f"""
            <div class="status {progress_class}">
                <strong>Progress:</strong> {last_run_status['progress']}
            </div>
        """
    
    return f"""
    <html>
    <head>
        <title>YouTube Automation Bot</title>
        <meta http-equiv="refresh" content="10">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 900px; margin: 40px auto; }}
            h1 {{ color: #333; }}
            .status {{ padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .success {{ background: #d4edda; color: #155724; }}
            .running {{ background: #fff3cd; color: #856404; animation: pulse 2s infinite; }}
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
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.7; }}
            }}
            details {{ margin: 15px 0; }}
            summary {{ margin-bottom: 10px; }}
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
            
            {progress_section}
            
            <div class="status {status_class}">
                <strong>Last Status:</strong> {last_run_status['status']}
            </div>
            
            {error_section}
            
            {output_section}
            
            <div class="status info">
                <strong>Next Scheduled Run:</strong> {last_run_status['next_run'] or 'Calculating...'}
            </div>
            
            <hr>
            
            <div class="button-container">
                <a href="/trigger" class="test-button">🚀 RUN TEST NOW</a>
            </div>
            
            <div class="warning">
                <strong>⚠️ Note:</strong> Test run may take 10-15 minutes to complete. 
                The page will auto-refresh every 10 seconds to show live progress. Check logs above for details.
            </div>
            
            <hr>
            
            <h3>📅 Automatic Schedule</h3>
            <ul>
                <li>8:00 AM IST (2:30 AM UTC)</li>
                <li>8:00 PM IST (2:30 PM UTC)</li>
            </ul>
            
            <p><em>Page auto-refreshes every 10 seconds</em></p>
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
