import requests
from .config import Config

class AssetManager:
    def __init__(self):
        # if not Config.PEXELS_API_KEY:
        #     raise ValueError("PEXELS_API_KEY not found")
        self.headers = {"Authorization": Config.PEXELS_API_KEY or ""}
    
    def search_video(self, query, orientation="portrait"):
        """Searches Pexels for a video URL."""
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=1&orientation={orientation}"
        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()
            if data['videos']:
                # Get the best quality video file link
                video_files = data['videos'][0]['video_files']
                #Sort by quality (width)
                best_video = sorted(video_files, key=lambda x: x['width'], reverse=True)[0]
                return best_video['link']
        except Exception as e:
            print(f"Error searching video for {query}: {e}")
        return None

    def download_file(self, url, output_path):
        """Downloads a file from a URL."""
        if not url: return False
        try:
            response = requests.get(url, stream=True)
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False

    def generate_image(self, prompt, output_path, orientation="portrait"):
        """Generates an image using Pollinations.ai (Free) with enhanced styling."""
        import urllib.parse
        
        # Add flavor tags to the prompt to ensure rich, purely animated visuals
        # Increased focus on removing any text/UI elements/watermarks
        enhanced_prompt = f"{prompt}, high quality digital art, vibrant colors, centered composition, no text, no captions, no watermark, no logo, no qr code, no user interface, no signature"
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        
        # Dimensions for Pollinations
        if orientation == "portrait":
            width, height = 1080, 1920
        elif orientation == "landscape":
            width, height = 1920, 1080
        else: # Thumbnail
            width, height = 1280, 720
            
        import random
        seed = random.randint(1, 1000000)
        
        # Using specific parameters to avoid logos/text
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&enhance=true&seed={seed}&nofeed=true"
        
        return self.download_file(url, output_path)

    def generate_thumbnail(self, title, output_path):
        """Generates a high-clickability thumbnail image."""
        prompt = f"Highly evocative, mysterious psychology thumbnail for '{title}', surrealist ink wash, dark moody atmosphere, psychological noir, minimalist, no text, 8k, cinematic"
        return self.generate_image(prompt, output_path, orientation="thumbnail")
