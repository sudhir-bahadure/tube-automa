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
    
    # Increased retries to 6 for stability
    for attempt in range(6):
        try:
            # Switch to fallback prompt after 3 failed attempts
            current_prompt = main_prompt if attempt < 3 else fallback_prompt
            encoded_prompt = urllib.parse.quote(current_prompt)
            
            # Use a fresh seed for every attempt
            seed = random.randint(1, 1000000)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=896&nologo=true&seed={seed}&model=flux"
            
            # Use shorter timeout for first 2 attempts to trigger fallback faster
            # But keep 90s for later attempts if server is just slow
            timeout = 30 if attempt < 2 else 90
            
            print(f"  [*] Stickman Pose (Attempt {attempt+1}): {current_prompt[:60]}...")
            
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
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
            
    return None

if __name__ == "__main__":
    # Test
    generate_stickman_image("running fast with a lightbulb idea", "test_stickman.jpg")
