import subprocess
import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class VideoEditorFFmpeg:
    """Direct FFmpeg-based video editor for robust automation."""
    
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
        
    def _find_ffmpeg(self):
        """Find FFmpeg executable."""
        # Try common locations
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0:
                return 'ffmpeg'
        except:
            pass
        
        # Try imageio-ffmpeg (bundled with MoviePy)
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except:
            pass
            
        raise RuntimeError("FFmpeg not found. Please install FFmpeg or imageio-ffmpeg.")
    
    def create_video(self, scenes, output_path, is_short=True, bg_music_path=None, style="noir"):
        """
        Create video using direct FFmpeg subprocess calls.
        
        Args:
            scenes: List of scene dicts with 'audio_path', 'video_path', 'text'
            output_path: Output video file path
            is_short: True for vertical (1080x1920), False for horizontal (1920x1080)
            bg_music_path: Optional background music path
            style: "noir" or "stickman"
        """
        logger.info(f"Creating video with {len(scenes)} scenes using FFmpeg...")
        
        # Target dimensions
        if is_short:
            width, height = 1080, 1920
        else:
            width, height = 1920, 1080
        
        # Create temp directory for intermediate files
        temp_dir = Path("temp/ffmpeg_assembly")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each scene into a video segment
        scene_videos = []
        for i, scene in enumerate(scenes):
            logger.info(f"Processing scene {i+1}/{len(scenes)}...")
            
            audio_path = scene['audio_path']
            image_path = scene['video_path']
            
            # Verify files exist
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Get audio duration using ffprobe
            duration = self._get_audio_duration(audio_path)
            logger.info(f"Scene {i+1} duration: {duration}s")
            
            # Create video segment from image + audio
            segment_path = temp_dir / f"segment_{i:03d}.mp4"
            self._create_segment(image_path, audio_path, segment_path, width, height, duration)
            scene_videos.append(str(segment_path))
        
        # Concatenate all segments
        logger.info("Concatenating segments...")
        concat_list = temp_dir / "concat_list.txt"
        with open(concat_list, 'w') as f:
            for video in scene_videos:
                f.write(f"file '{os.path.abspath(video)}'\n")
        
        # Concatenate without re-encoding (fast)
        temp_output = temp_dir / "concatenated.mp4"
        cmd = [
            self.ffmpeg_path,
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_list),
            '-c', 'copy',
            '-y',
            str(temp_output)
        ]
        
        self._run_ffmpeg(cmd, "Concatenating segments")
        
        # Add background music if provided
        if bg_music_path and os.path.exists(bg_music_path):
            logger.info("Adding background music...")
            final_output = output_path
            self._add_background_music(str(temp_output), bg_music_path, final_output)
        else:
            # Just copy the concatenated video to output
            import shutil
            shutil.copy(str(temp_output), output_path)
        
        logger.info(f"Video created successfully: {output_path}")
        return output_path
    
    def _get_audio_duration(self, audio_path):
        """Get audio duration using ffprobe."""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            audio_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return float(data['format']['duration'])
        except Exception as e:
            logger.warning(f"ffprobe failed, using fallback: {e}")
        
        # Fallback: use ffmpeg to get duration
        cmd = [
            self.ffmpeg_path,
            '-i', audio_path,
            '-f', 'null',
            '-'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        # Parse duration from stderr
        for line in result.stderr.split('\n'):
            if 'Duration:' in line:
                time_str = line.split('Duration:')[1].split(',')[0].strip()
                h, m, s = time_str.split(':')
                return float(h) * 3600 + float(m) * 60 + float(s)
        
        # Default to 3 seconds if we can't determine
        logger.warning(f"Could not determine duration for {audio_path}, using 3s")
        return 3.0
    
    def _create_segment(self, image_path, audio_path, output_path, width, height, duration):
        """Create a video segment from image and audio."""
        # Use FFmpeg to create video from static image + audio
        # Apply Ken Burns zoom effect for visual interest
        cmd = [
            self.ffmpeg_path,
            '-loop', '1',
            '-i', image_path,
            '-i', audio_path,
            '-vf', f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,zoompan=z='min(zoom+0.0015,1.1)':d={int(duration*30)}:s={width}x{height}:fps=30",
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-shortest',
            '-t', str(duration),
            '-y',
            str(output_path)
        ]
        
        self._run_ffmpeg(cmd, f"Creating segment: {output_path}")
    
    def _add_background_music(self, video_path, music_path, output_path, style="noir"):
        """Add background music to video with professional mixing."""
        # Noir needs lower background for psychological focus (0.10)
        # Stickman/Meme can be slightly higher (0.18)
        music_volume = 0.18 if style == "stickman" else 0.10
        
        # Mix video audio with background music
        # [1:a]volume=X[music] sets the bg music volume
        # amix=inputs=2:duration=shortest mixes them
        # Added a 1s fade-in/2s fade-out (afade) for the professional experience
        cmd = [
            self.ffmpeg_path,
            '-i', video_path,
            '-i', music_path,
            '-filter_complex', f'[1:a]volume={music_volume}[music];[0:a][music]amix=inputs=2:duration=shortest[aout];[aout]afade=t=in:ss=0:d=1,afade=t=out:st=seek_end-2:d=2[final_a]',
            '-map', '0:v',
            '-map', '[final_a]',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y',
            output_path
        ]
        
        self._run_ffmpeg(cmd, "Adding background music with professional mixing")
    
    def _run_ffmpeg(self, cmd, description):
        """Run FFmpeg command with error handling."""
        logger.info(f"{description}...")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise RuntimeError(f"FFmpeg failed: {description}\n{result.stderr}")
            
            return result
            
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"FFmpeg timeout: {description}")
        except Exception as e:
            raise RuntimeError(f"FFmpeg error: {description}\n{str(e)}")
