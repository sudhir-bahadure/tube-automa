from gradio_client import Client
import os
import subprocess

def transcribe_whisper(video_path):
    FFMPEG_PATH = r"C:\Users\SUDHIR\AppData\Local\Programs\Python\Python312\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win64-v4.2.2.exe"
    audio_path = "temp_audio_final.mp3"
    
    print("[*] Extracting audio...")
    cmd = [FFMPEG_PATH, "-i", video_path, "-q:a", "0", "-map", "a", audio_path, "-y"]
    subprocess.run(cmd, capture_output=True)

    try:
        print("[*] Calling AI Whisper...")
        client = Client("hf-audio/whisper-large-v3")
        # Call the first API function (index 0)
        result = client.predict(audio_path, "transcribe", fn_index=0)
        
        print("\n--- TRANSCRIPT ---")
        print(result)
        
        with open("captions_to_copy.txt", "w", encoding="utf-8") as f:
            f.write(str(result))
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

if __name__ == "__main__":
    transcribe_whisper(r"D:\YT\youtube automation backup\refined_short_fast.mp4")
