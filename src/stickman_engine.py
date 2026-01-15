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
    Now supports niche-specific color palettes.
    """
    # Clean and encode the prompt
    clean_pose = pose_description.lower().replace("stickman", "").strip()
    
    # Get niche-appropriate color palette
    color_palette = get_niche_color_palette(niche)
    
    # Construct a high-quality prompt for Pollinations
    # We want consistency: Black stickman, niche-appropriate background.
    prompt = (
        f"A clean 2D vector animation style illustration of a stickman {clean_pose}. "
        f"Use {color_palette} for background elements or props. "
        "The stickman should be black with smooth lines. High quality, flat design, aesthetic, clear visibility. "
        "White or very light solid background."
    )
    encoded_prompt = urllib.parse.quote(prompt)
    
    # Pollinations works best with standard sizes
    seed = random.randint(1, 1000000)
    # Use a backup model/seed strategy if needed? simpler prompt?
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=896&nologo=true&seed={seed}&model=flux"
    
    # Increased retries to 5 and timeout to 90s for reliability
    for attempt in range(5):
        try:
            print(f"  [*] Generating Stickman Pose (Attempt {attempt+1}): {pose_description}...")
            # 90s timeout to handle server load spikes
            response = requests.get(url, timeout=90)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                    return output_path
            else:
                print(f"  [WARN] Attempt {attempt+1} failed with status {response.status_code}")
        except Exception as e:
            print(f"  [WARN] Attempt {attempt+1} failed: {e}")
        
        # Exponential backoff: 2s, 4s, 8s, 16s
        if attempt < 4:
            wait_time = 2 ** (attempt + 1)
            print(f"  [RETRY] Waiting {wait_time}s before retry...")
            import time
            time.sleep(wait_time)
            
    return None

if __name__ == "__main__":
    # Test
    generate_stickman_image("running fast with a lightbulb idea", "test_stickman.jpg")
