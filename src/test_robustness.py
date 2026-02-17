
import os
import sys
from PIL import Image
import numpy as np

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from .asset_manager import AssetManager
    from .video_editor import VideoEditor
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.getcwd(), 'src'))
    from asset_manager import AssetManager
    from video_editor import VideoEditor

def test_robust_download():
    print("\n--- Testing Robust Download ---")
    asset_mgr = AssetManager()
    
    # Test 1: Invalid URL
    print("[Test 1] Invalid URL...")
    success = asset_mgr.download_file("https://invalid.url/image.jpg", "temp_invalid.jpg", max_retries=1)
    print(f"Result: {'PASS' if not success else 'FAIL'} (Expected False)")
    
    # Test 2: Verify integrity check (simulate corrupt file)
    print("[Test 2] Corrupt Image Verification...")
    with open("temp_corrupt.jpg", "w") as f:
        f.write("This is not an image file. It's just text.")
    
    # Normally we would test download_file, but here we'll just check if PIL can open it
    try:
        with Image.open("temp_corrupt.jpg") as img:
            img.verify()
        print("Result: FAIL (PIL opened a text file as image?)")
    except:
        print("Result: PASS (PIL correctly identified corrupt file)")
    
    if os.path.exists("temp_corrupt.jpg"):
        os.remove("temp_corrupt.jpg")

def test_video_editor_fallback():
    print("\n--- Testing Video Editor Fallback ---")
    editor = VideoEditor()
    
    # Create mock scenes
    # Scene 1: Valid Path but Corrupt File
    with open("corrupt_visual.jpg", "w") as f:
        f.write("error slop")
    
    # Scene 2: Missing Path (None)
    
    scenes = [
        {
            'audio_path': 'assets/music/funny/funny.mp3' if os.path.exists('assets/music/funny/funny.mp3') else None,
            'video_path': 'corrupt_visual.jpg',
            'text': 'This scene has a corrupt image.'
        },
        {
            'audio_path': None,
            'video_path': None,
            'text': 'This scene has no image path.'
        }
    ]
    
    # We need real audio for MoviePy to not crash on audio duration
    # Let's use an existing audio file if available
    audio_asset = os.path.join('assets', 'music', 'funny', 'A Stroll - Density & Time.mp3')
    if os.path.exists(audio_asset):
        real_audio_path = audio_asset
    else:
        # Create a dummy silent file if absolutely needed, but let's try to find any mp3
        real_audio_path = None
        for root, dirs, files in os.walk('assets/music'):
            for file in files:
                if file.endswith('.mp3'):
                    real_audio_path = os.path.join(root, file)
                    break
            if real_audio_path: break

    if real_audio_path:
        scenes[0]['audio_path'] = real_audio_path
        scenes[1]['audio_path'] = real_audio_path
        print(f"Using audio asset: {real_audio_path}")
    else:
        print("Warning: No audio assets found. MoviePy might fail.")

    print("[Test] Rendering video with corrupt/missing assets...")
    try:
        print(f"Calling create_video with {len(scenes)} scenes...")
        # Note: We're passing None for audio_path to trigger the internal silence fallback
        success = editor.create_video(
            scenes=scenes, 
            output_video_path="robustness_test_output.mp4", 
            is_short=True, 
            style="stickman"
        )
        print(f"Result: {'PASS' if success else 'FAIL'} (Rendering finished despite errors)")
    except Exception as e:
        print(f"Result: FAIL (Crashed in test script: {e})")
        import traceback
        traceback.print_exc()

    # Cleanup
    print("Cleaning up...")
    for f in ["corrupt_visual.jpg", "robustness_test_output.mp4", "temp_silent.wav", "temp_invalid.jpg"]:
        if os.path.exists(f): 
            try: 
                os.remove(f)
                print(f" Removed {f}")
            except: pass

if __name__ == "__main__":
    try:
        test_robust_download()
        test_video_editor_fallback()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
