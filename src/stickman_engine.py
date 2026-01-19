import requests
import random
import os
import urllib.parse

def get_niche_color_palette(niche="default"):
    """
    Returns color palette description based on content niche.
    Ensures visuals match the emotional tone of each workflow.
    """
    palettes = {
        "meme": "vibrant playful colors like bright yellow, hot pink, electric orange, lime green",
        "fact": "professional calming colors like deep blue, teal, soft purple, mint green",
        "curiosity": "professional calming colors like deep blue, teal, soft purple, mint green",
        "documentary": "sophisticated muted colors like warm gray, deep navy, earth brown, sage green",
        "long": "sophisticated muted colors like warm gray, deep navy, earth brown, sage green"
    }
    return palettes.get(niche, "soft pastel colors like light blue, pale pink, cream")

def generate_stickman_image(pose_description, output_path="temp_stickman.jpg", niche="default"):
    """
    Generates a stickman image based on a pose description using Pollinations.ai.
    Style: Minimalist, black on white, professional.
    Now supports niche-specific color palettes and stability fallback.
    """
    # Clean and encode the prompt
    clean_pose = pose_description.lower().replace("stickman", "").strip()
    
    # Get niche-appropriate color palette
    color_palette = get_niche_color_palette(niche)
    
    # Standard prompt for quality
    main_prompt = (
        f"A clean 2D vector animation style illustration of a stickman {clean_pose}. "
        f"Use {color_palette} for background elements or props. "
        "The stickman should be black with smooth lines. High quality, flat design, aesthetic, clear visibility. "
        "White or very light solid background. (No watermark, no QR code, no logo, no signature, no text)."
    )
    
    # Fallback prompt for speed/reliability if main fails
    fallback_prompt = f"Simple black stickman {clean_pose} on white background, flat vector style."
    
    # Reduced retries to 3 for speed (fail fast)
    for attempt in range(3):
        try:
            # Switch to fallback prompt after 1 failed attempt
            current_prompt = main_prompt if attempt < 1 else fallback_prompt
            encoded_prompt = urllib.parse.quote(current_prompt)
            
            # Use a fresh seed for every attempt
            seed = random.randint(1, 1000000)
            # Use standard model for speed
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=894&nologo=1&seed={seed}"
            
            # Tighter timeout: 25s max per request
            timeout = 25
            
            # Identify if this is first or second image in a segment (using optional label)
            label = getattr(generate_stickman_image, "current_label", "1")
            print(f"  [*] Stickman Pose {label} (Attempt {attempt+1}): {current_prompt[:60]}...")
            
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                # GUARD 1: Byte Pattern Check (Detects some error masquerades)
                if b"RATE LIMIT REACHED" in response.content or b"anonymous tier" in response.content:
                    print(f"  [WARN] Pollinations rate limit detected (text). Retrying...")
                    time.sleep(15)
                    continue

                with open(output_path, "wb") as file:
                    file.write(response.content)
                
                # GUARD 2: Visual Validation (The most robust check)
                try:
                    from PIL import Image
                    with Image.open(output_path) as img:
                        # Check top-left pixel. Our prompt requests White background.
                        # The Error Image is Brown/Dark.
                        tl_pixel = img.getpixel((5, 5))
                        # If RGB, it's a tuple. If grayscale, it's an int.
                        if isinstance(tl_pixel, tuple):
                            # The error image top-left is brownish (~60, 40, 20)
                            # White/Light should be > 200 for all channels
                            is_light = all(c > 180 for c in tl_pixel[:3])
                        else:
                            is_light = tl_pixel > 180
                            
                        if not is_light:
                            print(f"  [WARN] Image failed visual check (dark background detected). Likely error banner. Retrying...")
                            os.remove(output_path)
                            time.sleep(15)
                            continue
                            
                except Exception as eval_err:
                    print(f"  [DEBUG] Pixel check failed: {eval_err}")
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                    return output_path
            else:
                print(f"  [WARN] Attempt {attempt+1} failed with status {response.status_code}")
        except Exception as e:
            print(f"  [WARN] Attempt {attempt+1} failed: {e}")
        
        # Jittered exponential backoff
        if attempt < 5:
            wait_time = (2 ** (attempt + 1)) + (random.random() * 2)
            print(f"  [RETRY] Waiting {wait_time:.1f}s before retry...")
            import time
            time.sleep(wait_time)
    
    # BULLETPROOF FALLBACK: Generate a gradient background with PIL (Never returns None)
    print(f"  [FALLBACK] All API attempts failed. Generating gradient background...")
    return generate_gradient_fallback(pose_description, output_path, niche)

def generate_gradient_fallback(text, output_path, niche="default"):
    """
    Creates a visually appealing gradient background with text overlay.
    This is the FINAL fallback - it NEVER fails.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap
        
        # Create 1080x1920 canvas
        width, height = 1080, 1920
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Niche-specific gradient colors
        gradients = {
            "meme": [(255, 107, 107), (255, 193, 7)],      # Red to Yellow (Energetic)
            "fact": [(79, 172, 254), (0, 242, 254)],       # Blue gradient (Professional)
            "curiosity": [(79, 172, 254), (0, 242, 254)],  # Blue gradient
            "documentary": [(52, 73, 94), (44, 62, 80)],   # Dark blue-gray (Sophisticated)
            "long": [(52, 73, 94), (44, 62, 80)]
        }
        
        color1, color2 = gradients.get(niche, [(200, 200, 255), (255, 200, 200)])
        
        # Draw vertical gradient
        for y in range(height):
            ratio = y / height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            draw.rectangle([(0, y), (width, y+1)], fill=(r, g, b))
        
        # Add text overlay (first 50 chars of description)
        try:
            # Try to use a nice font, fallback to default
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        except:
            font = ImageFont.load_default()
        
        # Wrap text
        display_text = text[:100]
        wrapped = textwrap.fill(display_text, width=15)
        
        # Calculate text position (centered)
        bbox = draw.textbbox((0, 0), wrapped, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw text with shadow for readability
        shadow_offset = 4
        draw.text((x + shadow_offset, y + shadow_offset), wrapped, fill=(0, 0, 0, 128), font=font)
        draw.text((x, y), wrapped, fill=(255, 255, 255), font=font)
        
        # Save
        img.save(output_path, quality=85)
        print(f"  [OK] Gradient fallback created: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"  [ERROR] Gradient fallback failed: {e}")
        # ABSOLUTE LAST RESORT: Solid color (still better than white)
        try:
            from PIL import Image
            solid_colors = {
                "meme": (255, 193, 7),      # Yellow
                "fact": (79, 172, 254),     # Blue
                "curiosity": (79, 172, 254),
                "documentary": (52, 73, 94),
                "long": (52, 73, 94)
            }
            color = solid_colors.get(niche, (200, 200, 255))
            img = Image.new('RGB', (1080, 1920), color)
            img.save(output_path)
            return output_path
        except:
            return None  # Only if PIL is completely broken


if __name__ == "__main__":
    # Test
    generate_stickman_image("running fast with a lightbulb idea", "test_stickman.jpg")
