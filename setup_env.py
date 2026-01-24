import os
import json

def setup_credentials_from_env():
    """
    Setup credentials from environment variables if files don't exist.
    This is needed for Render.com deployment where secrets are stored as env vars.
    """
    # Setup client_secrets.json from environment variable
    if not os.path.exists('client_secrets.json') and 'CLIENT_SECRETS_JSON' in os.environ:
        print("📝 Creating client_secrets.json from environment variable...")
        with open('client_secrets.json', 'w') as f:
            f.write(os.environ['CLIENT_SECRETS_JSON'])
    
    # Setup token.json from environment variable
    if not os.path.exists('token.json') and 'TOKEN_JSON' in os.environ:
        print("📝 Creating token.json from environment variable...")
        with open('token.json', 'w') as f:
            f.write(os.environ['TOKEN_JSON'])
    
    # Setup cookies.txt from environment variable (optional)
    if not os.path.exists('cookies.txt') and 'YOUTUBE_COOKIES' in os.environ:
        print("📝 Creating cookies.txt from environment variable...")
        with open('cookies.txt', 'w') as f:
            f.write(os.environ['YOUTUBE_COOKIES'])

if __name__ == "__main__":
    setup_credentials_from_env()
