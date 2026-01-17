import os
import shutil
from gradio_client import Client

def clone_voice(text, output_path, reference_audio="assets/voice_sample.wav"):
    """
    Clones a voice from a reference sample and generates audio for the given text.
    Uses free Hugging Face spaces via gradio_client.
    """
    if not os.path.exists(reference_audio):
        # Fallback to .mpeg if .wav wasn't created
        alt_ref = reference_audio.replace(".wav", ".mpeg")
        if os.path.exists(alt_ref):
            reference_audio = alt_ref
        else:
            print(f"Error: Reference voice sample not found at {reference_audio}")
            return None

    print(f"--- Cloning Voice for: '{text[:50]}...' ---")
    
    # We will try a few stable spaces for XTTS-v2 or similar
    spaces = [
        "coqui/xtts-v2", # Primary standard
        "mrfakename/E2-F5-TTS", # Newer, very fast
        "Plat-XTTS-v2" # Often has higher limits
    ]
    
    for space in spaces:
        try:
            print(f"[*] Attempting voice cloning via {space}...")
            client = Client(space)
            
            if "xtts-v2" in space.lower():
                # XTTS-v2 standard API
                result = client.predict(
                    text,	# Text to speak
                    "en",	# Language
                    reference_audio,	# Reference audio
                    reference_audio,	# Reference audio (duplicate for some APIs)
                    False,	# Agree to terms
                    False,	# Use sentence splitter
                    api_name="/predict"
                )
            else:
                # E2-F5-TTS or similar
                result = client.predict(
                    reference_audio,
                    "", # Reference text (optional)
                    text,
                    "E2-F5", # Model type
                    0.2, # Speed
                    api_name="/predict"
                )
            
            if result and os.path.exists(result):
                # result is usually a temporary filepath
                shutil.copy(result, output_path)
                print(f"  [OK] Audio cloned successfully via {space}")
                return output_path
                
        except Exception as e:
            print(f"  [WARN] Space {space} failed: {e}")
            continue

    print("  [ERROR] All voice cloning spaces failed.")
    return None
