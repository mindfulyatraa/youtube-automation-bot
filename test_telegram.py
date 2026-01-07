import urllib.parse
import urllib.request
import time

def test_telegram():
    print("🇮🇳 Telegram Notification Tester")
    print("=================================")
    
    # Hardcoded for verification
    bot_token = "8296921285:AAFuQkkFOarlMXkFTZKJukW5KRcHuMqipcE".strip()
    chat_id = "5977525101".strip()
    
    print(f"\n📨 Sending to: {chat_id}")
    
    # Message format (Simple Text)
    message = "Test Message from Automation"
    
    try:
        data = urllib.parse.urlencode({
            'chat_id': chat_id,
            'text': message
        }).encode()
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 200:
                print("\n✅ Success! Check your Telegram now.")
            else:
                print(f"\n❌ Failed. Server code: {response.getcode()}")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_telegram()
