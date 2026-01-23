import os
import random
import logging

logger = logging.getLogger(__name__)

class MusicEngine:
    def __init__(self, base_path="assets/music"):
        self.base_path = base_path
        # Ensure base path exists
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
            # Create subfolders for common moods
            for mood in ['upbeat', 'high_energy', 'funny', 'chill', 'tense', 'suspenseful', 'dark', 'inspirational']:
                os.makedirs(os.path.join(self.base_path, mood), exist_ok=True)

    def get_track(self, mood):
        """Returns (path, credits) for a random music file."""
        mood = mood.lower().strip()
        mood_dir = os.path.join(self.base_path, mood)
        
        if not os.path.exists(mood_dir):
            logger.warning(f"Music mood folder not found: {mood}. Falling back.")
            # Try any random folder that actually has files
            if os.path.exists(self.base_path):
                for m in os.listdir(self.base_path):
                    potential_dir = os.path.join(self.base_path, m)
                    if os.path.isdir(potential_dir) and any(f.lower().endswith(('.mp3', '.wav', '.m4a')) for f in os.listdir(potential_dir)):
                        mood_dir = potential_dir
                        break
                else:
                    return None, None
            else:
                return None, None

        tracks = [f for f in os.listdir(mood_dir) if f.lower().endswith(('.mp3', '.wav', '.m4a'))]
        
        if not tracks:
            logger.warning(f"No tracks found in {mood_dir}.")
            # Search all folders
            for root, dirs, files in os.walk(self.base_path):
                all_tracks = [f for f in files if f.lower().endswith(('.mp3', '.wav', '.m4a'))]
                if all_tracks:
                    selected = random.choice(all_tracks)
                    selected_path = os.path.join(root, selected)
                    return selected_path, self._extract_credits(selected)
            return None, None

        selected = random.choice(tracks)
        path = os.path.join(mood_dir, selected)
        credits = self._extract_credits(selected)
        logger.info(f"Selected music: {selected} (Mood: {mood})")
        return path, credits

    def _extract_credits(self, filename):
        """Extracts Artist and Song name from 'Track Name - Artist Name.mp3' format."""
        name_without_ext = os.path.splitext(filename)[0]
        if " - " in name_without_ext:
            parts = name_without_ext.split(" - ")
            song = parts[0].strip().title()
            artist = parts[1].strip().title()
            return f"{song} by {artist}"
        return name_without_ext.replace('_', ' ').replace('-', ' ').strip().title()
