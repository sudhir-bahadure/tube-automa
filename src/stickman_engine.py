import requests
import random
import os
import urllib.parse

def generate_stickman_image(pose_description, output_path="temp_stickman.jpg"):
    """
    Generates a stickman image based on a pose description using Pollinations.ai.
    Style: Minimalist, black on white, professional.
    """
    # Clean and encode the prompt
    clean_pose = pose_description.lower().replace("stickman", "").strip()
    
    # Construct a high-quality prompt for Pollinations
    # We want consistency: Black stickman, white background.
    prompt = (
        f"A clean 2D vector animation style illustration of a stickman {clean_pose}. "
        "Use a pleasant, soft pastel color palette (e.g., soft blues, mint greens, warm yellows) for background elements or props. "
        "The stickman should be black with smooth lines. High quality, flat design, aesthetic, clear visibility. "
        "White or very light solid pastel background."
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
            import time
            time.sleep(2) # Brief wait before retry
            
    return None

if __name__ == "__main__":
    # Test
    generate_stickman_image("running fast with a lightbulb idea", "test_stickman.jpg")
