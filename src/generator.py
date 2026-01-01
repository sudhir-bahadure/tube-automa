import os
import random
import requests
import asyncio
import edge_tts
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip, ImageClip, concatenate_videoclips
from moviepy.video.fx.all import crop, resize

async def generate_audio(text, output_file="audio.mp3"):
    # Microsoft Edge Neural Voices (High Quality, Free)
    voice = "en-US-AriaNeural" # Female, Natural, Professional 
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def download_background_video(query="abstract", api_key=None):
    # Fallback to a solid color if no API key or download fails
    if not api_key:
        return None
        
    headers = {'Authorization': api_key}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=15&orientation=portrait"
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            videos = r.json().get('videos', [])
            if videos:
                video_data = random.choice(videos)
                video_files = video_data.get('video_files', [])
                best_file = max(video_files, key=lambda x: x['width'] * x['height'])
                link = best_file['link']
                
                print(f"Downloading background from Pexels: {link}")
                with open("bg_raw.mp4", "wb") as f:
                    f.write(requests.get(link).content)
                return "bg_raw.mp4"
    except Exception as e:
        print(f"Error downloading Pexels video: {e}")
        
    return None


def create_video(metadata, output_path="final_video.mp4", pexels_key=None):
    mode = metadata.get('mode', 'fact')
    
    if mode == 'meme' and 'memes' in metadata:
        # --- NEW COMPILATION LOGIC FOR MEMES ---
        memes = metadata['memes']
        meme_clips = []
        temp_audio_files = []
        
        print(f"Generating meme compilation with {len(memes)} jokes...")
        
        for i, meme in enumerate(memes):
            setup = meme['setup']
            punchline = meme['punchline']
            
            # 1. Generate Audio for this joke
            audio_path = f"temp_audio_{i}.mp3"
            script = f"{setup} ... ... {punchline} ... Hahaha!"
            asyncio.run(generate_audio(script, audio_path))
            audio = AudioFileClip(audio_path)
            temp_audio_files.append(audio_path)
            
            duration = audio.duration + 0.5
            
            # 2. Get Background for this segment
            # We fetch a new background for each joke to keep it engaging
            bg_file = download_background_video("funny reaction", pexels_key)
            if bg_file:
                clip = VideoFileClip(bg_file)
                if clip.duration < duration:
                    clip = clip.loop(duration=duration)
                else:
                    clip = clip.subclip(0, duration)
            else:
                # Random darkish colors
                colors = [(30, 30, 30), (20, 40, 20), (40, 20, 20)]
                clip = ColorClip(size=(1080, 1920), color=random.choice(colors), duration=duration)
            
            # Resize logic (DRY later maybe)
            w, h = clip.size
            target_ratio = 9/16
            if w/h > target_ratio:
                new_w = h * target_ratio
                clip = crop(clip, x1=(w/2 - new_w/2), width=new_w, height=h)
            else:
                new_h = w / target_ratio
                clip = crop(clip, y1=(h/2 - new_h/2), width=w, height=new_h)
            clip = clip.resize(newsize=(1080, 1920))
            
            # 3. Add Meme Style Overlay
            banner_h = 400
            banner = ColorClip(size=(1080, banner_h), color=(255, 255, 255), duration=duration).set_position(('center', 'top'))
            
            setup_txt = (TextClip(setup, fontsize=60, color='black', font='Liberation-Sans-Bold',
                                  method='caption', size=(950, banner_h-50), align='center')
                          .set_position(('center', 25))
                          .set_duration(duration))
            
            punch_start = duration * 0.4
            punch_txt = (TextClip(punchline, fontsize=90, color='yellow', font='Liberation-Sans-Bold',
                                 method='caption', size=(900, None), stroke_color='black', stroke_width=4)
                         .set_position(('center', 1200))
                         .set_start(punch_start)
                         .set_duration(duration - punch_start))
            
            # Combine Meme Segment
            meme_segment = CompositeVideoClip([clip, banner, setup_txt, punch_txt]).set_audio(audio)
            meme_clips.append(meme_segment)
            
            if bg_file and os.path.exists(bg_file): os.remove(bg_file)

        # Final Concatenation
        final_video = concatenate_videoclips(meme_clips, method="compose")
        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        
        # Cleanup
        for f in temp_audio_files:
            if os.path.exists(f): os.remove(f)
            
        return output_path

    else:
        # --- FACT STYLE (OR SINGLE JOKE FALLBACK) ---
        text = metadata['text']
        print(f"Generating single video: {text[:30]}...")
        
        asyncio.run(generate_audio(text, "temp_audio.mp3"))
        audio = AudioFileClip("temp_audio.mp3")
        duration = audio.duration + 1.0
        
        query = "nature dark aesthetic abstract"
        bg_file = download_background_video(query, pexels_key)
        
        if bg_file:
            clip = VideoFileClip(bg_file)
            if clip.duration < duration:
                clip = clip.loop(duration=duration)
            else:
                clip = clip.subclip(0, duration)
        else:
            clip = ColorClip(size=(1080, 1920), color=(20, 20, 20), duration=duration)
        
        w, h = clip.size
        target_ratio = 9/16
        if w/h > target_ratio:
            new_w = h * target_ratio
            clip = crop(clip, x1=(w/2 - new_w/2), width=new_w, height=h)
        else:
            new_h = w / target_ratio
            clip = crop(clip, y1=(h/2 - new_h/2), width=w, height=new_h)
        clip = clip.resize(newsize=(1080, 1920))
        
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
            
        final_clip = CompositeVideoClip([clip] + txt_clips).set_audio(audio)
        final_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        
        try:
            os.remove("temp_audio.mp3")
            if bg_file: os.remove(bg_file)
        except:
            pass
            
        return output_path

if __name__ == "__main__":
    # Test run
    test_meta = {
        "text": "Did you know? Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old.",
        "mode": "fact"
    }
    create_video(test_meta, "test_output.mp4")
