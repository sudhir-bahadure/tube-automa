import os
import random
import requests
import asyncio
import edge_tts
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip, ImageClip, concatenate_videoclips
from moviepy.video.fx.all import crop, resize
# Removed silent logging override as it causes issues in some moviepy versions

async def generate_audio(text, output_file="audio.mp3"):
    # Microsoft Edge Neural Voices (High Quality, Free)
    voice = "en-US-AriaNeural" # Female, Natural, Professional 
    communicate = edge_tts.Communicate(text, voice)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await communicate.save(output_file)
            return
        except Exception as e:
            print(f"Audio generation attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2) # Backoff
            else:
                # If all else fails, we might need a backup or silent clip, but let's try to crash early if critical
                raise e

def download_background_video(query="abstract", api_key=None, output_file="bg_raw.mp4"):
    # Fallback to a solid color if no API key or download fails
    if not api_key:
        return None
        
    headers = {'Authorization': api_key}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=15&orientation=portrait"
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            videos = r.json().get('videos', [])
            if videos:
                video_data = random.choice(videos)
                video_files = video_data.get('video_files', [])
                # Prefer HD/Full HD but keep it manageable
                video_files = [v for v in video_files if v['width'] >= 720]
                if not video_files:
                    video_files = video_data.get('video_files', [])
                
                best_file = min(video_files, key=lambda x: abs(x['width'] - 1080))
                link = best_file['link']
                
                print(f"Downloading background from Pexels: {link}")
                with requests.get(link, stream=True, timeout=15) as res:
                    if res.status_code == 200:
                        with open(output_file, "wb") as f:
                            for chunk in res.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        # Verify file size (at least 100KB)
                        if os.path.exists(output_file) and os.path.getsize(output_file) > 102400:
                            return output_file
                        else:
                            print("Downloaded video is too small, likely corrupted.")
                            if os.path.exists(output_file): os.remove(output_file)
    except Exception as e:
        print(f"Error downloading Pexels video: {e}")
        
    return None


def create_video(metadata, output_path="final_video.mp4", pexels_key=None):
    mode = metadata.get('mode', 'fact')
    
    if mode == 'meme' and 'memes' in metadata:
        # --- NEW COMPILATION LOGIC FOR MEMES ---
        memes = metadata['memes']
        meme_clips = []
        temp_bg_files = []
        temp_audio_files = []
        
        print(f"Generating meme compilation with {len(memes)} jokes...")
        
        for i, meme in enumerate(memes):
            setup = meme['setup']
            punchline = meme['punchline']
            
            # 1. Generate Audio for this joke
            audio_path = f"temp_audio_{i}.mp3"
            script = f"{setup} ... ... {punchline} ... Hahaha!"
            asyncio.run(generate_audio(script, audio_path))
            audio_clip = AudioFileClip(audio_path)
            temp_audio_files.append(audio_path)
            
            duration = audio_clip.duration + 0.5
            # Fix: Pad audio to match video duration to avoid MoviePy OSError
            from moviepy.audio.AudioClip import CompositeAudioClip
            audio = CompositeAudioClip([audio_clip]).set_duration(duration)
            
            # 2. Get Background for this segment
            # Use unique filename to prevent locking/overwrite issues
            bg_filename = f"temp_bg_{i}.mp4"
            bg_file = download_background_video("funny reaction", pexels_key, bg_filename)
            clip = None
            if bg_file:
                try:
                    clip = VideoFileClip(bg_file)
                    # Explicitly check if we can read the first frame
                    _ = clip.get_frame(0) 
                    
                    if clip.duration < duration:
                        clip = clip.loop(duration=duration)
                    else:
                        clip = clip.subclip(0, duration)
                    temp_bg_files.append(bg_file) # Track for cleanup
                except Exception as e:
                    print(f"Corrupted video skip: {e}")
                    if clip: clip.close()
                    clip = None
            
            if not clip:
                # Random darkish colors fallback
                colors = [(30, 30, 30), (20, 40, 20), (40, 20, 20), (20, 20, 40)]
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
            banner_h = 350
            banner = ColorClip(size=(1080, banner_h), color=(255, 255, 255), duration=duration).set_position(('center', 'top'))
            
            # Subtle divider line
            divider = ColorClip(size=(1080, 5), color=(200, 200, 200), duration=duration).set_position(('center', banner_h))

            # Try common fonts
            font_list = ['Liberation-Sans-Bold', 'Arial', 'Impact', 'Verdana']
            setup_txt = None
            for font in font_list:
                try:
                    setup_txt = (TextClip(setup, fontsize=55, color='black', font=font,
                                          method='caption', size=(1000, banner_h-40), align='center')
                                  .set_position(('center', 20))
                                  .set_duration(duration))
                    selected_font = font
                    break
                except:
                    continue
            
            if not setup_txt:
                print("Warning: Could not create TextClip. ImageMagick might be missing.")
                # Fallback to just the background/banner if text fails (prevent crash)
                meme_segment = CompositeVideoClip([clip, banner, divider]).set_audio(audio)
            else:
                # More impact for punchline
                punch_start = duration * 0.5
                punch_txt = (TextClip(punchline, fontsize=100, color='white', font=selected_font,
                                     method='caption', size=(950, None), stroke_color='black', stroke_width=3)
                             .set_position(('center', 1100))
                             .set_start(punch_start)
                             .set_duration(duration - punch_start))
                
                # Combine Meme Segment
                meme_segment = CompositeVideoClip([clip, banner, divider, setup_txt, punch_txt]).set_audio(audio)
            meme_clips.append(meme_segment.set_duration(duration))

        # Final Concatenation
        final_video = concatenate_videoclips(meme_clips, method="compose")
        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        
        # Cleanup
        for f in temp_audio_files + temp_bg_files:
            try:
                if os.path.exists(f): os.remove(f)
            except:
                pass
            
        return output_path

    else:
        # --- FACT STYLE (OR SINGLE JOKE FALLBACK) ---
        text = metadata['text']
        print(f"Generating single video: {text[:30]}...")
        
        asyncio.run(generate_audio(text, "temp_audio.mp3"))
        audio_raw = AudioFileClip("temp_audio.mp3")
        duration = audio_raw.duration + 1.0
        from moviepy.audio.AudioClip import CompositeAudioClip
        audio = CompositeAudioClip([audio_raw]).set_duration(duration)
        
        query = "nature dark aesthetic abstract"
        bg_file = download_background_video(query, pexels_key)
        
        if bg_file:
            try:
                clip = VideoFileClip(bg_file)
                # Explicitly check if we can read the first frame
                _ = clip.get_frame(0)
                
                if clip.duration < duration:
                    clip = clip.loop(duration=duration)
                else:
                    clip = clip.subclip(0, duration)
            except Exception as e:
                print(f"Corrupted fact background skip: {e}")
                if clip: clip.close()
                clip = None
        
        if not clip:
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
            
        font_list = ['Liberation-Sans-Bold', 'Arial', 'Impact', 'Verdana']
        txt_clips = []
        chunk_duration = duration / len(chunks)
        for i, chunk in enumerate(chunks):
            txt = None
            for font in font_list:
                try:
                    txt = (TextClip(chunk, fontsize=70, color='white', font=font, 
                                   method='caption', size=(900, None), stroke_color='black', stroke_width=2)
                           .set_position('center')
                           .set_duration(chunk_duration)
                           .set_start(i * chunk_duration))
                    break
                except:
                    continue
            if txt:
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
