from moviepy.editor import *
import moviepy.video.fx.all as vfx
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

class VideoEditor:
    def _create_text_clip(self, text, size, fontsize, color, stroke_color, stroke_width, duration):
        """Creates a TextClip using PIL as a fallback to avoid ImageMagick issues."""
        try:
            # Try to load a font
            try:
                # Common Windows font paths
                font = ImageFont.truetype("arialbd.ttf", fontsize)
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", fontsize)
                except:
                    font = ImageFont.load_default()

            # Create an image with transparent background (RGBA)
            img = Image.new('RGBA', size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Wrap text manually
            import textwrap
            lines = textwrap.wrap(text, width=30) 
            
            current_h = 10 # Some top padding
            for line in lines:
                if hasattr(draw, 'textbbox'):
                    bbox = draw.textbbox((0, 0), line, font=font)
                    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                else:
                    w, h = draw.textsize(line, font=font)
                
                # Draw stroke
                if stroke_width > 0:
                    for offset_x in range(-stroke_width, stroke_width + 1):
                        for offset_y in range(-stroke_width, stroke_width + 1):
                            draw.text(((size[0]-w)/2 + offset_x, current_h + offset_y), line, font=font, fill=stroke_color)

                draw.text(((size[0]-w)/2, current_h), line, font=font, fill=color)
                current_h += h + 15
            
            # Convert to RGB array for MoviePy and also get alpha channel
            rgb_img = img.convert('RGB')
            alpha_img = img.convert('L') # Luminance as alpha
            
            # Create clip with mask for transparency
            clip = ImageClip(np.array(rgb_img)).set_duration(duration)
            mask = ImageClip(np.array(alpha_img), ismask=True).set_duration(duration)
            
            return clip.set_mask(mask)
            
        except Exception as e:
            print(f"PIL Text Render failed: {e}")
            return ColorClip(size=size, color=(0,0,0,0), duration=duration)
    def create_video(self, scenes, output_path, is_short=True, bg_music_path=None, style="noir"):
        """
        Stitches visualization, audio and subtitles with dynamic animations and transitions.
        style: "noir" (Standard dark surreal) or "stickman" (Minimalist stick figures on white)
        """
        import random
        import math
        
        # Target Dimensions
        if is_short:
            target_w, target_h = 1080, 1920
        else:
            target_w, target_h = 1920, 1080

        clips = []
        for i, scene in enumerate(scenes):
            try:
                # Load Audio
                audio_clip = AudioFileClip(scene['audio_path'])
                duration = audio_clip.duration
                
                # Load Visual (Video OR Image)
                v_path = scene['video_path']
                if os.path.exists(v_path):
                    if v_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                        # Process Image
                        img_clip = ImageClip(v_path).set_duration(duration)
                        
                        if style == "stickman":
                            # STICKMAN STYLE: Pure White BG, Centered, Fade In/Out, Pleasant Liveness
                            bg_clip = ColorClip(size=(target_w, target_h), color=(255, 255, 255)).set_duration(duration)
                            
                            # Base resize
                            img_clip = img_clip.resize(width=int(target_w * 0.7))
                            
                            # PLEASANT LIVENESS EFFECTS:
                            # 1. Floating: Vertical sway ±15px over 3 seconds
                            # 2. Breathing: Subtle scaling ±1.5% over 4 seconds
                            
                            v_action = scene.get('vocal_action', 'talking')
                            
                            # Base floating position
                            base_pos = lambda t: ('center', (target_h/2 - img_clip.h/2) + 15 * math.sin(2 * math.pi * 0.33 * t))
                            
                            # ACTION-AWARE OVERRIDES:
                            if v_action == 'jumping':
                                # Intense vertical bounce
                                video_clip = img_clip.set_position(lambda t: ('center', (target_h/2 - img_clip.h/2) - abs(100 * math.sin(2 * math.pi * 0.8 * t))))
                            elif v_action == 'waving':
                                # Smooth rotation sway
                                video_clip = img_clip.rotate(lambda t: 5 * math.sin(2 * math.pi * 0.5 * t)).set_position(base_pos)
                            elif v_action == 'shaking':
                                # High frequency jitter
                                video_clip = img_clip.set_position(lambda t: ('center', (target_h/2 - img_clip.h/2) + random.uniform(-10, 10)))
                            elif v_action == 'bouncing':
                                # Scale-based bounce
                                video_clip = img_clip.resize(lambda t: 1.0 + 0.1 * abs(math.sin(2 * math.pi * 0.7 * t))).set_position(base_pos)
                            else:
                                # Default Floating
                                video_clip = img_clip.set_position(base_pos)
                            
                            # Apply Breathing (Slow Scaling)
                            if v_action != 'bouncing':
                                video_clip = video_clip.resize(lambda t: 1.0 + 0.015 * math.sin(2 * math.pi * 0.25 * t))
                            
                            # Fade In / Fade Out
                            video_clip = video_clip.fadein(0.5).fadeout(0.5)
                            
                            # Composite over white background
                            video_clip = CompositeVideoClip([bg_clip, video_clip.set_start(0)])
                            
                            # NO FILTERS for stickman to keep background pure white
                        else:
                            # NOIR STYLE: Standard animated visuals
                            anim_type = random.choice(['zoom_in', 'zoom_out', 'pan_left', 'pan_right'])
                            base_scale = 1.3
                            if is_short:
                                img_clip = img_clip.resize(height=int(target_h * base_scale))
                            else:
                                img_clip = img_clip.resize(width=int(target_w * base_scale))
                                
                            img_clip = img_clip.crop(x_center=img_clip.w/2, y_center=img_clip.h/2, width=int(target_w * 1.1), height=int(target_h * 1.1))
                            
                            if anim_type == 'zoom_in':
                                video_clip = img_clip.resize(lambda t: 1.0 + 0.15 * (t/duration))
                            elif anim_type == 'zoom_out':
                                video_clip = img_clip.resize(lambda t: 1.15 - 0.15 * (t/duration))
                            elif anim_type == 'pan_left':
                                video_clip = img_clip.set_position(lambda t: (int(-0.1 * target_w * (t/duration)), 'center'))
                            elif anim_type == 'pan_right':
                                video_clip = img_clip.set_position(lambda t: (int(-0.1 * target_w * (1 - t/duration)), 'center'))
                            else:
                                video_clip = img_clip
                                
                            if anim_type.startswith('zoom'):
                                video_clip = video_clip.set_position('center')
                            
                            video_clip = video_clip.crop(x_center=video_clip.w/2, y_center=video_clip.h/2, width=target_w, height=target_h)

                    else:
                        # Video Handling
                        video_clip = VideoFileClip(v_path)
                        if video_clip.duration < duration:
                            video_clip = video_clip.loop(duration=duration)
                        else:
                            video_clip = video_clip.subclip(0, duration)
                        
                        if video_clip.w / video_clip.h > target_w / target_h:
                            video_clip = video_clip.resize(height=target_h)
                        else:
                            video_clip = video_clip.resize(width=target_w)
                        video_clip = video_clip.crop(x_center=video_clip.w/2, y_center=video_clip.h/2, width=target_w, height=target_h)
                else:
                    video_clip = ColorClip(size=(target_w, target_h), color=(0,0,0), duration=duration)

                video_clip = video_clip.set_audio(audio_clip)

                if i > 0 and style != "stickman": # Crossfade only for noir/standard
                    video_clip = video_clip.crossfadein(0.5)

                # Subtitles / Captions
                txt_h = 400
                if is_short:
                    txt_w = int(target_w * 0.9)
                    txt_clip = self._create_text_clip(
                        scene['text'], 
                        size=(txt_w, txt_h),
                        fontsize=50, 
                        color='black' if style == "stickman" else 'white', 
                        stroke_color='white' if style == "stickman" else 'black', 
                        stroke_width=2,
                        duration=duration
                    )
                    txt_clip = txt_clip.set_pos(('center', target_h * 0.8)).set_duration(duration)
                    final_scene = CompositeVideoClip([video_clip, txt_clip])
                else:
                    txt_w = int(target_w * 0.8)
                    txt_clip = self._create_text_clip(
                        scene['text'], 
                        size=(txt_w, txt_h),
                        fontsize=40, 
                        color='black' if style == "stickman" else 'white', 
                        stroke_color='white' if style == "stickman" else 'black', 
                        stroke_width=1,
                        duration=duration
                    )
                    txt_clip = txt_clip.set_pos(('center', target_h * 0.85)).set_duration(duration)
                    final_scene = CompositeVideoClip([video_clip, txt_clip])
                
                clips.append(final_scene)
                
            except Exception as e:
                print(f"Error processing scene: {e}")
        
        if clips:
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Add Background Music
            if bg_music_path and os.path.exists(bg_music_path):
                bg_audio = AudioFileClip(bg_music_path).volumex(0.08)
                if bg_audio.duration < final_video.duration:
                    bg_audio = bg_audio.loop(duration=final_video.duration)
                else:
                    bg_audio = bg_audio.subclip(0, final_video.duration)
                
                final_audio = CompositeAudioClip([final_video.audio, bg_audio])
                final_video = final_video.set_audio(final_audio)

            final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", temp_audiofile="temp_audio.m4a", threads=4)
            return True
        return False
