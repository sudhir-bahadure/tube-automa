import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    # These are the only Google models permitted by the zero-cost pipeline.
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    GEMINI_FREE_TIER_ONLY = os.getenv("GEMINI_FREE_TIER_ONLY", "true").lower() == "true"
    GEMINI_FREE_MODELS = ("gemini-3.8-flash", "gemini-3.5-flash-lite")

    # Optional, independently rate-limited free-tier fallbacks. These are only
    # used when both a credential and an explicit free-tier confirmation exist.
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_FREE_TIER_CONFIRMED = os.getenv("GROQ_FREE_TIER_CONFIRMED", "false").lower() == "true"
    GROQ_FREE_MODEL = "openai/gpt-oss-20b"
    CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
    CLOUDFLARE_WORKERS_FREE_CONFIRMED = os.getenv(
        "CLOUDFLARE_WORKERS_FREE_CONFIRMED", "false"
    ).lower() == "true"
    # Current free-plan model; the previous Llama 3.1 route is deprecated.
    CLOUDFLARE_FREE_MODEL = "@cf/zai-org/glm-4.7-flash"

    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
    YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN")
    YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
    YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
    
    # YouTube Auth
    YOUTUBE_CLIENT_SECRET_FILE = "client_secrets.json"
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"
    YOUTUBE_SCOPES = [
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.force-ssl",
        "https://www.googleapis.com/auth/yt-analytics.readonly",
    ]

    # Content Settings
    NICHE = os.getenv("NICHE", "Relatable Daily Life Humour and Human Experience")
    VIDEO_LANGUAGE = os.getenv("VIDEO_LANGUAGE", "en-US")
    VOICE_NAME = os.getenv("VOICE_NAME", "en-US-ChristopherNeural") # Deep, professional male voice
