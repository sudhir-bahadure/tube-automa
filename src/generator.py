import os
import random
import requests
import asyncio
import edge_tts
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip, ImageClip
from moviepy.video.fx.all import crop, resize
from moviepy.config import change_settings

# Ensure ImageMagick is detected (Update path if needed on Local PC, but on GitHub Actions it's standard)
# change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

async def generate_audio(text, output_file="audio.mp3"):
    # Microsoft Edge Neural Voices (High Quality, Free)
    # en-US-ChristopherNeural is a deep, documentary style voice
    voice = "en-US-AriaNeural" # Female, Natural, Professional 
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def download_background_video(query="abstract", api_key=None, duration=15):
    # Fallback to a solid color if no API key or download fails
    if not api_key:
        print("No Pexels API Key provided, using generated background.")
        return None
        
    headers = {'Authorization': api_key}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=15&orientation=portrait"
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            videos = r.json().get('videos', [])
            if videos:
                # Pick a random video
                video_data = random.choice(videos)
                video_files = video_data.get('video_files', [])
                # Get the best quality HD file
                best_file = max(video_files, key=lambda x: x['width'] * x['height'])
                link = best_file['link']
                
                # Download
                print(f"Downloading background from Pexels: {link}")
                with open("bg_raw.mp4", "wb") as f:
                    f.write(requests.get(link).content)
                return "bg_raw.mp4"
    except Exception as e:
        print(f"Error downloading Pexels video: {e}")
        
    return None

def create_video(metadata, output_path="final_video.mp4", pexels_key=None):
    text = metadata['text']
    mode = metadata.get('mode', 'fact')
    
    print(f"Generating ({mode}) video: {text[:30]}...")
    
    # 1. Generate Audio
    asyncio.run(generate_audio(text, "temp_audio.mp3"))
    audio = AudioFileClip("temp_audio.mp3")
    duration = audio.duration + 1.0 # Add 1 second padding
    
    # 2. Get Background
    query = "nature dark aesthetic abstract" if mode == 'fact' else "funny confusing laughing reaction"
    bg_file = download_background_video(query, pexels_key, duration)
    
    if bg_file:
        clip = VideoFileClip(bg_file)
        if clip.duration < duration:
            clip = clip.loop(duration=duration)
        else:
            clip = clip.subclip(0, duration)
    else:
        clip = ColorClip(size=(1080, 1920), color=(20, 20, 20), duration=duration)
    
    # Resize to Vertical
    w, h = clip.size
    target_ratio = 9/16
    current_ratio = w/h
    
    if current_ratio > target_ratio:
        new_w = h * target_ratio
        clip = crop(clip, x1=(w/2 - new_w/2), width=new_w, height=h)
    else:
        new_h = w / target_ratio
        clip = crop(clip, y1=(h/2 - new_h/2), width=w, height=new_h)
        
    clip = clip.resize(newsize=(1080, 1920))
    
    # 3. Add Visuals (Styles)
    final_clip = None
    
    if mode == 'meme':
        # --- MEME STYLE (White Top Banner) ---
        setup_text = metadata.get('setup', '')
        
        # 1. White Banner (Top 25%)
        banner_h = 400
        banner = ColorClip(size=(1080, banner_h), color='white', duration=duration).set_position(('center', 'top'))
        
        # 2. Setup Text (Black, inside banner)
        setup_txt_clip = (TextClip(setup_text, fontsize=60, color='black', font='Liberation-Sans-Bold',
                                  method='caption', size=(950, banner_h-50), align='center')
                          .set_position(('center', 25)) # Slight padding top
                          .set_duration(duration))
                          
        # 3. Punchline (White with black stroke, bottom overlay)
        # Only show punchline in the second half approx
        punch_text = metadata.get('punchline', '')
        punch_start = duration * 0.4 # Reveal punchline 40% in
        punch_txt_clip = (TextClip(punch_text, fontsize=80, color='yellow', font='Liberation-Sans-Bold',
                                  method='caption', size=(900, None), stroke_color='black', stroke_width=4)
                          .set_position(('center', 1200)) # Bottom area
                          .set_start(punch_start)
                          .set_duration(duration - punch_start))
                          
        final_clip = CompositeVideoClip([clip, banner, setup_txt_clip, punch_txt_clip])
        
    else:
        # --- FACT STYLE (Centered Overlay) ---
        words = text.split()
        chunks = []
        chunk_size = 5
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i+chunk_size]))
            
        txt_clips = []
        chunk_duration = duration / len(chunks)
        
        for i, chunk in enumerate(chunks):
            txt = (TextClip(chunk, fontsize=70, color='white', font='Liberation-Sans-Bold', 
                           method='caption', size=(900, None), stroke_color='black', stroke_width=2)
                   .set_position('center')
                   .set_duration(chunk_duration)
                   .set_start(i * chunk_duration))
            txt_clips.append(txt)
            
        final_clip = CompositeVideoClip([clip] + txt_clips)
        
    final_clip = final_clip.set_audio(audio)
    final_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    
    try:
        os.remove("temp_audio.mp3")
        if bg_file: os.remove(bg_file)
    except:
        pass
        
    return output_path

if __name__ == "__main__":
    # Test run
    test_text = "Did you know? Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old."
    create_video(test_text, "test_output.mp4")
