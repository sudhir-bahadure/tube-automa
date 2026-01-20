
import asyncio
import json
import os
from src.llm_wrapper import LLMWrapper
from src.utils import setup_logging

def main():
    print("Starting Psychology Content Generation Test...")
    try:
        llm = LLMWrapper()
        
        # 1. Generate Titles
        print("Generating Titles...")
        titles = llm.generate_psychology_titles()
        if titles:
            print(f"Generated {len(titles)} titles:")
            print(json.dumps(titles, indent=2))
            with open("output/psychology_titles.json", "w") as f:
                json.dump(titles, f, indent=2)
        else:
            print("Failed to generate titles.")
            return

        # 2. Generate Script for First Title
        selected_title = titles[0]
        print(f"\nGenerating Script for: {selected_title}")
        script = llm.generate_psychology_script(selected_title)
        
        if script:
            print("Script Generated successfully.")
            print(f"Title: {script.get('title')}")
            print(f"Angle: {script.get('deduced_angle')}")
            print(f"Scenes: {len(script.get('scenes', []))}")
            
            with open("output/psychology_script.json", "w") as f:
                json.dump(script, f, indent=2)
        else:
            print("Failed to generate script.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
