import os
import requests
import random
from PIL import Image, ImageDraw, ImageFont

def download_thumbnail_bg(topic, pexels_key, output_file="thumb_bg.jpg"):
    """Download a high-quality landscape background for the thumbnail"""
    if not pexels_key: return None
    headers = {'Authorization': pexels_key}
    query = f"cinematic {topic} tech"
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=10&orientation=landscape"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            photos = r.json().get('photos', [])
            if photos:
                img_url = random.choice(photos)['src']['landscape']
                res = requests.get(img_url, timeout=10)
                if res.status_code == 200:
                    with open(output_file, 'wb') as f: f.write(res.content)
                    return output_file
    except: pass
    return None

def create_thumbnail(topic, output_path="thumbnail.jpg", pexels_key=None):
    """Generate a professional thumbnail"""
    print(f"[*] Creating thumbnail for: {topic}")
    
    # 1. Base Image
    bg = download_thumbnail_bg(topic, pexels_key)
    if bg and os.path.exists(bg):
        img = Image.open(bg).convert("RGBA")
    else:
        img = Image.new("RGBA", (1280, 720), (15, 15, 25, 255))
    
    img = img.resize((1280, 720), Image.Resampling.LANCZOS)
    
    # 2. Draw 
    draw = ImageDraw.Draw(img)
    
    # Overlay for text contrast
    draw.rectangle((0, 0, 750, 720), fill=(0, 0, 0, 180))
    
    # 3. Text (Search for best available font)
    font_paths = [
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\impact.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    
    font_path = None
    for p in font_paths:
        if os.path.exists(p):
            font_path = p
            break
    
    try:
        font_main = ImageFont.truetype(font_path, 110)
        font_sub = ImageFont.truetype(font_path, 50)
    except:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        
    # Branding
    draw.text((50, 50), "2026 AI STRATEGY", font=font_sub, fill=(255, 220, 0, 255))
    
    # Topic split
    words = topic.upper().split()
    lines = []
    curr = []
    for w in words:
        if len(" ".join(curr + [w])) < 12: curr.append(w)
        else:
            lines.append(" ".join(curr))
            curr = [w]
    lines.append(" ".join(curr))
    
    y = 150
    for line in lines[:3]:
        draw.text((55, y+5), line, font=font_main, fill=(0,0,0,100)) # Shadow
        draw.text((50, y), line, font=font_main, fill=(255, 255, 255, 255))
        y += 130
        
    draw.text((50, 620), "NEW TECH BREAKTHROUGH", font=font_sub, fill=(0, 255, 150, 255))
    
    # Final save
    try:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_path, "JPEG", quality=90)
        print(f"[OK] Thumbnail ready: {output_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save thumbnail: {e}")
        
    if bg and os.path.exists(bg): os.remove(bg)
    return output_path

if __name__ == "__main__":
    create_thumbnail("AI Agents Future", "test_final.jpg")
