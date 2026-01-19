import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))
from llm_wrapper import llm

def generate_metadata():
    load_dotenv()
    
    topic = "POV: When you finally understand the assignment"
    
    # generate_viral_title only takes topic, keywords, and max_chars
    title = llm.generate_viral_title(topic)
    tags = llm.generate_optimized_tags(topic)
    
    # Simple script segments for description generator
    segments = [{"content": "When you think you're cool in your leather jacket but the white earphones give you away."}]
    description = llm.optimize_description(title, segments)
    
    print("--- VIRAL METADATA ---")
    print(f"TITLE: {title}")
    print("\nDESCRIPTION:")
    print(description)
    print("\nTAGS:")
    print(tags)

if __name__ == "__main__":
    generate_metadata()
