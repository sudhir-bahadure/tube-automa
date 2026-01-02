"""Quick test for long video metadata generation"""
import sys
import os
import io

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock the ypp_script_template module if needed, but we want to test content.py logic
# assertions
from src import content

def test_long_metadata():
    print("=" * 60)
    print("Testing Long Metadata Generation")
    print("=" * 60)
    
    print("\n[*] Generating long metadata...")
    # This might trigger network calls, but we just want to check the end result
    metadata = content.get_long_video_metadata()
    
    segments = metadata.get('segments', [])
    if not segments:
        print("[FAIL] No segments generated")
        return False
        
    last_segment = segments[-1]
    text = last_segment.get('text', '')
    
    print(f"\n[*] Last Segment Text:\n{text}")
    
    expected_hook = "subscribe to Daily Meme Dose"
    # Case insensitive check
    if expected_hook.lower() in text.lower():
        print(f"\n[SUCCESS] Found subscribe hook: '{expected_hook}'")
        return True
    else:
        print(f"\n[FAIL] Subscribe hook MISSING. Got: {text}")
        return False

if __name__ == "__main__":
    success = test_long_metadata()
    sys.exit(0 if success else 1)
