import sys
import os
import json

# Force UTF-8 for printing if possible
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Mock environment variables
os.environ["PEXELS_API_KEY"] = "mock_key"
os.environ["TELEGRAM_BOT_TOKEN"] = "mock_token"
os.environ["TELEGRAM_CHAT_ID"] = "mock_id"

sys.path.append(os.path.join(os.getcwd(), 'src'))
from content_enhanced import get_video_metadata, get_meme_metadata, get_long_video_metadata

def test_category(name, func):
    print(f"\n[RUNNING] Category: {name.upper()}")
    try:
        metadata = func()
        print(f"[SUCCESS] Title: {metadata['title']}")
        print(f"Mode: {metadata.get('mode', 'N/A')}")
        
        tags = metadata.get('tags', '').lower()
        if any(kw in tags for kw in ["meme", "funny", "joke", "fact", "long", "ai", "tech"]):
             print("[ALIGNMENT] Content is niche-aligned.")
        else:
             print("[WARNING] Content might be off-niche.")
             
        return True
    except Exception as e:
        print(f"[ERROR] Failed: {str(e)}")
        return False

print("Starting Full Workflow Audit (Meme Niche Verification)...")
results = []
results.append(test_category("Meme", get_meme_metadata))
results.append(test_category("Fact", get_video_metadata))
results.append(test_category("Long (Compilation)", get_long_video_metadata))

print("\n--- Final Results ---")
if all(results):
    print("ALL WORKFLOWS STABLE. SYSTEM READY.")
else:
    print("FIXES REQUIRED.")
    sys.exit(1)
