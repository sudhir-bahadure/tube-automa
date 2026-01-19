import os
import google.generativeai as genai
from dotenv import load_dotenv
import time

def transcribe_video(video_path):
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        return

    genai.configure(api_key=api_key)

    print(f"[*] Uploading video for transcription: {video_path}")
    # Upload the file to the Gemini File API
    video_file = genai.upload_file(path=video_path)
    print(f"[*] File uploaded: {video_file.name}")

    # Wait for processing
    while video_file.state.name == "PROCESSING":
        print(".", end="", flush=True)
        time.sleep(2)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        print("\nError: Video processing failed.")
        return

    print("\n[*] Video processed. Generating transcript...")
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = """
    Transcribe the speech in this video. 
    Provide the transcription in a format suitable for the YouTube Studio 'Edit as text' subtitle box.
    Group the words into readable phrases with their start and end timestamps in HH:MM:SS format.
    
    Example format:
    00:00:01 - 00:00:04
    This is the first phrase.
    
    00:00:05 - 00:00:08
    This is the second phrase.
    """
    
    response = model.generate_content([video_file, prompt])
    
    print("\n--- TRANSCRIPT ---")
    print(response.text)
    
    # Store for walkthrough
    with open("final_captions.txt", "w", encoding="utf-8") as f:
        f.write(response.text)

if __name__ == "__main__":
    transcribe_video(r"D:\YT\youtube automation backup\refined_short_fast.mp4")
