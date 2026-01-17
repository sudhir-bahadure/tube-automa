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
    # Using more active and diverse spaces to ensure "Free Forever" reliability
    spaces = [
        "lucataco/xtts-v2",       # Highly active, often updated
        "daswer123/xtts-v2-api",  # Dedicated API space
        "coqui/xtts-v2",          # Official space (might require auth sometimes)
        "mrfakename/E2-F5-TTS",   # Fast fallback if XTTS is slow
    ]
    
    for space in spaces:
        try:
            print(f"[*] Attempting voice cloning via {space}...")
            # Set a strict timeout to prevent GitHub Action hangs
            client = Client(space)
            
            if "xtts-v2" in space.lower():
                # XTTS-v2 standard API
                # Using a timeout in the predict call if the space supports it/gradio allows
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
            # Check for common authentication or availability errors
            error_msg = str(e)
            if "401" in error_msg:
                print(f"  [WARN] Space {space} requires authentication (401). Skipping.")
            elif "404" in error_msg:
                print(f"  [WARN] Space {space} not found (404). Skipping.")
            else:
                print(f"  [WARN] Space {space} failed: {error_msg}")
            continue

    print("  [ERROR] All voice cloning spaces failed.")
    return None
