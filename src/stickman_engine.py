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
    prompt = f"Minimalist professional black stickman {clean_pose}, pure white background, simple clean lines, high contrast, 4k, digital art"
    encoded_prompt = urllib.parse.quote(prompt)
    
    # Lower resolution for faster/more reliable generation
    # Pollinations works best with standard sizes
    seed = random.randint(1, 1000000)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=896&nologo=true&seed={seed}"
    
    for attempt in range(3):
        try:
            print(f"  [*] Generating Stickman Pose (Attempt {attempt+1}): {pose_description}...")
            response = requests.get(url, timeout=40)
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
