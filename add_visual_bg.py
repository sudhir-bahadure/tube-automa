import subprocess
import os

FFMPEG_PATH = r"C:\Users\SUDHIR\AppData\Local\Programs\Python\Python312\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win64-v4.2.2.exe"
INPUT_VIDEO = r"D:\YT\youtube automation backup\refined_short_fast.mp4"
OUTPUT_VIDEO = r"D:\YT\youtube automation backup\final_visual_short.mp4"

def add_background():
    # Filter Complex:
    # [bg]: Scale to 1080x1920 (fill) and apply heavy blur
    # [fg]: Scale original to fit inside (padding)
    # [v]: Overlay foreground on blurred background
    
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:20[bg]; "
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg]; "
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[v]"
    )

    cmd = [
        FFMPEG_PATH,
        "-i", INPUT_VIDEO,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "0:a", # Keep normalized audio from previous step
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "veryfast",
        "-c:a", "copy", # No need to re-encode audio
        "-y",
        OUTPUT_VIDEO
    ]

    print(f"Adding cinematic background...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"SUCCESS: Final video saved to {OUTPUT_VIDEO}")
    else:
        print(f"ERROR: {result.stderr}")

if __name__ == "__main__":
    add_background()
