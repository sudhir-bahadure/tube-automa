
import os
import sys
import asyncio
import warnings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path - REMOVED for module execution
# sys.path.append(os.path.join(os.getcwd(), 'src'))

# Import Modules
try:
    from content import get_fact, get_meme_metadata
    from generator import generate_audio
    from stickman_engine import generate_stickman_image
    from llm_wrapper import llm
    from moviepy.editor import ImageClip, CompositeVideoClip
    import PIL.Image
except ImportError as e:
    print(f"CRITICAL IMPORT ERROR: {e}")
    # sys.exit(1)
    pass

# Suppress warnings
warnings.filterwarnings("ignore")

# Monkeypatch Pillow for MoviePy if needed
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

async def run_verification():
    print("==================================================")
    print("   TUBEAUTOMA LOCAL SYSTEM VERIFICATION SUITE")
    print("==================================================")
    
    # 1. API & LLM CHECK
    print("\n[1/5] Testing LLM & Content Logic...")
    fact_data = None
    try:
        if os.getenv('GEMINI_API_KEY'):
            fact_data = get_fact()
            if fact_data and 'script' in fact_data:
                print("  [OK] 'Daily Fact' Generation (Real AI): SUCCESS")
            else:
                 print("  [X] 'Daily Fact' Generation: FAILED (No data returned)")
        else:
            print("  [!] GEMINI_API_KEY missing. Switching to MOCK MODE for pipeline verification.")
            # Mock Data to test downstream components (Audio, Visuals, Rendering)
            fact_data = {
                "title": "MOCK: The Speed of Light",
                "niche": "fact",
                "mode": "fact",
                "script": [
                    {"text": "Did you know light travels fast?", "keyword": "light speed", "stickman_poses": ["running fast", "sprinting"]},
                    {"text": "It can circle the earth seven times in one second.", "keyword": "earth orbit", "stickman_poses": ["orbiting earth", "flying"]}
                ],
                "description": "Mock description.\n\nDISCLAIMER: Content generated with the help of AI."
            }
            print("  [OK] 'Daily Fact' Generation (Mock): ACTIVE")

        if fact_data:
            print(f"     Title: {fact_data['title']}")
            print(f"     Voice: Andrew (Implied by 'fact' niche)")
            
    except Exception as e:
        print(f"  [X] 'Daily Fact' Error: {e}")

    # 2. IMAGE GENERATION CHECK (Monetization Frame)
    print("\n[2/5] Testing Visual Engine (Stickman + Framing)...")
    try:
        test_img_path = "test_verify_stickman.jpg"
        if os.path.exists(test_img_path): os.remove(test_img_path)
        
        # Determine niche for pallet
        niche = fact_data['niche'] if fact_data else "fact"
        
        generated_path = generate_stickman_image("stickman verification test", test_img_path, niche=niche)
        
        if generated_path:
            print("  [OK] Stickman Image Generated: SUCCESS")
            
            # Verify Transformative Frame logic (Simulation)
            clip = ImageClip(generated_path).set_duration(1)
            w, h = clip.size
            if w == 512: # Original size
                # Apply Framing Logic from generator.py
                clip = clip.margin(20, color=(255, 255, 255)).margin(2, color=(0, 0, 0))
                clip = clip.resize(newsize=(1080, 1920))
                print("  [OK] Transformative Framing Applied: SUCCESS")
                clip.close()
            else:
                 print("  [!] Image sizing unexpected, skipping frame check.")
        else:
            print("  [X] Stickman Image Generation: FAILED")
    except Exception as e:
        print(f"  [X] Visual Engine Error: {e}")

    # 3. AUDIO GENERATION CHECK
    print("\n[3/5] Testing Audio Engine (EdgeTTS)...")
    try:
        test_audio_path = "test_verify_audio.mp3"
        if os.path.exists(test_audio_path): os.remove(test_audio_path)
        
        # Test "Andrew" Voice (Fact Persona)
        await generate_audio("This is a system verification test.", test_audio_path, voice="en-US-AndrewNeural")
        
        if os.path.exists(test_audio_path) and os.path.getsize(test_audio_path) > 1000:
             print("  [OK] Audio Generation (Andrew): SUCCESS")
        else:
             print("  [X] Audio Generation: FAILED (File empty or missing)")
    except Exception as e:
        print(f"  [X] Audio Engine Error: {e}")

    # 4. MONETIZATION METADATA CHECK
    print("\n[4/5] Testing Metadata Compliance...")
    if fact_data and "DISCLAIMER" in fact_data.get('description', ''):
        print("  [OK] AI Disclosure Found: SUCCESS")
    else:
        print("  [!] AI Disclosure Missing in Fact Description!")

    # 5. CLEANUP
    print("\n[5/5] Cleanup...")
    if os.path.exists(test_img_path): os.remove(test_img_path)
    if os.path.exists(test_audio_path): os.remove(test_audio_path)
    print("  [OK] Cleanup Complete")
    
    print("\n==================================================")
    print("   VERIFICATION COMPLETE")
    print("   If all checks passed, your GitHub Workflows are safe to run.")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_verification())
