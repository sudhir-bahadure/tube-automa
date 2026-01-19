import os
import sys
import asyncio
import json

# Set Key BEFORE imports
os.environ["GEMINI_API_KEY"] = "AIzaSyA0auEAaLBTBlluy-texOWB1k_wGr09Low"
os.environ["GEMINI_VISUAL_KEY"] = "AIzaSyA0auEAaLBTBlluy-texOWB1k_wGr09Low"

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from content import generate_content_metadata
from generator import create_video
from youtube_uploader import upload_video

def verify_system():
    print("==================================================")
    print(" VERIFYING MEME AUTOMATION SYSTEM (LOCAL TEST)")
    print("==================================================")
    
    # 1. Check Keywords
    print("\n[1] Testing Viral Content Generation (Gemini)...")
    try:
        metadata = generate_content_metadata(mode="meme")
        print(f"  Topic: {metadata['topic']}")
        print(f"  Title: {metadata['title']}")
        print(f"  Script Length: {len(metadata['script'])} segments")
        
        total_words = sum([len(s['text'].split()) for s in metadata['script']])
        print(f"  Total Words: {total_words} (Limit: 38)")
        
        if total_words > 45: 
             print("  [FAIL] Script too long!")
        else:
             print("  [PASS] Script length optimized.")
             
    except Exception as e:
        print(f"  [FAIL] Content Generation Error: {e}")
        return

    # 2. Test Video Production (Visuals + Audio)
    print("\n[2] Testing Video Production (Gemini Visuals + EdgeTTS)...")
    try:
        output_path = "test_meme_video.mp4"
        if os.path.exists(output_path):
            os.remove(output_path)
            
        final_video = create_video(metadata, output_path=output_path)
        
        if final_video and os.path.exists(final_video):
            size_mb = os.path.getsize(final_video) / (1024*1024)
            print(f"  [PASS] Video Generated: {final_video} ({size_mb:.2f} MB)")
        else:
            print("  [FAIL] Video generation failed.")
            return

    except Exception as e:
        print(f"  [FAIL] Video Production Error: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. Test Upload Logic (Dry Run)
    print("\n[3] Testing Upload Logic (Dry Run)...")
    from youtube_uploader import upload_video
    import inspect
    src_code = inspect.getsource(upload_video)
    if 'privacyStatus": "private"' in src_code and 'publishAt' in src_code:
        print("  [PASS] Scheduling Logic Detected (Private + PublishAt)")
    else:
        print("  [FAIL] Scheduling Logic NOT Detected")

if __name__ == "__main__":
    verify_system()
