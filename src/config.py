import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
    YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN")
    YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
    YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
    
    # YouTube Auth
    YOUTUBE_CLIENT_SECRET_FILE = "client_secrets.json"
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"
    YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

    # Content Settings
    NICHE = os.getenv("NICHE", "Deep Dark Psychology and Human Behavior")
    VIDEO_LANGUAGE = os.getenv("VIDEO_LANGUAGE", "en-US")
    VOICE_NAME = os.getenv("VOICE_NAME", "en-US-ChristopherNeural") # Deep, professional male voice
