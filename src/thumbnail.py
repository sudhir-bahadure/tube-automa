from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import random

def create_thumbnail(image_path, text, output_path="thumbnail.jpg"):
    """
    Create a high-contrast thumbnail.
    image_path: Path to background image (1920x1080).
    text: Short punchy text.
    """
    try:
        # Load Image
        if os.path.exists(image_path):
            img = Image.open(image_path).convert("RGB")
        else:
            # Fallback gradient/solid
            img = Image.new("RGB", (1920, 1080), color=(20, 20, 30))
        
        draw = ImageDraw.Draw(img)
        
        # Resize to standard if needed
        img = img.resize((1920, 1080))
        
        # Darken background slightly to make text pop
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 80))
        img.paste(Image.alpha_composite(img.convert("RGBA"), overlay), (0,0))
        draw = ImageDraw.Draw(img)

        # Font setup (Try to find a system bold font)
        # On Linux (GitHub Actions), paths are /usr/share/fonts/...
        font_paths = [
            "arialbd.ttf", 
            "Impact.ttf", 
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        ]
        
        font = None
        for path in font_paths:
            try:
                font = ImageFont.truetype(path, 150)
                break
            except:
                continue
                
        if not font:
            font = ImageFont.load_default()

        # Wrap text (naive)
        words = text.upper().split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            # Check width
            line_str = " ".join(current_line)
            bbox = draw.textbbox((0, 0), line_str, font=font)
            if bbox[2] - bbox[0] > 1700: # Padding
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
            
        # Draw Text
        y_text = 200
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            x_text = (1920 - text_w) / 2
            
            # Text Stroke (Black border)
            stroke_width = 8
            draw.text((x_text, y_text), line, font=font, fill="white", stroke_fill="black", stroke_width=stroke_width)
            
            y_text += text_h + 30
            
        # Add "TubeAutoma" subtle watermark? No, user removed branding.
        
        img = img.convert("RGB")
        img.save(output_path, "JPEG", quality=90)
        return output_path
        
    except Exception as e:
        print(f"Thumbnail generation failed: {e}")
        return None
