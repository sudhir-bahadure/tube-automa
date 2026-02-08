import os
import sys
import json
import asyncio
from pyfiglet import Figlet
from simple_term_menu import TerminalMenu
from content import get_fact, get_meme_metadata
from video_editor import VideoEditor
from generator import generate_audio
from gemini_visual_engine import generate_gemini_image
from llm_wrapper import llm

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    f = Figlet(font='slant')
    print(f.renderText('DIRECTOR MODE'))
    print("==================================================")
    print("   QUALITY FIRST. AUTOMATION SECOND.")
    print("==================================================")

def get_user_input(prompt_text):
    return input(f"\n[?] {prompt_text}: ").strip()

def select_option(options, title="Select an option:"):
    print(f"\n{title}")
    terminal_menu = TerminalMenu(options)
    menu_entry_index = terminal_menu.show()
    return options[menu_entry_index]

async def run_director():
    clear_screen()
    print_banner()

    # 1. Topic Selection
    print("\n[Step 1] Concept & Topic")
    topic_source = select_option(["Generate Viral Hooks (Dark Psych)", "Enter Custom Topic", "Exit"], "Choose Topic Source:")
    
    if topic_source == "Exit":
        sys.exit(0)
        
    selected_topic = ""
    if topic_source == "Generate Viral Hooks (Dark Psych)":
        print("\n[*] Brainstorming viral hooks...")
        # Use LLM to generate hooks
        hooks = llm.generate_psychology_titles()
        if not hooks:
            print("[!] Failed to generate hooks. Please enter manually.")
            selected_topic = get_user_input("Enter your topic")
        else:
            selected_topic = select_option(hooks, "Select a Killer Hook:")
    else:
        selected_topic = get_user_input("Enter your topic")

    print(f"\n[*] Selected Topic: {selected_topic}")
    
    # 2. Script Generation
    print("\n[Step 2] Scripting (Noir Style)")
    print("[*] Drafting script... (This takes 10-20s)")
    
    script_data = llm.generate_psychology_short_script(selected_topic)
    
    if not script_data:
        print("[!] Script generation failed.")
        return

    # User Review Loop
    while True:
        print("\n--- DRAFT SCRIPT ---")
        print(f"Title: {script_data.get('title')}")
        print("-" * 20)
        for i, scene in enumerate(script_data.get('scenes', [])):
            print(f"[{i+1}] {scene.get('text')}")
            print(f"    (Visual: {scene.get('visual_prompt')})")
        print("-" * 20)
        
        action = select_option(["Approve & Render", "Regenerate Script", "Edit Manually (JSON)", "Discard & Exit"], "Director's Call:")
        
        if action == "Approve & Render":
            break
        elif action == "Regenerate Script":
            print("[*] Regenerating...")
            script_data = llm.generate_psychology_short_script(selected_topic)
        elif action == "Edit Manually (JSON)":
            # Simple dump to temp file and await press
            with open("temp_script_edit.json", "w") as f:
                json.dump(script_data, f, indent=4)
            print(f"\n[!] Opened 'temp_script_edit.json'. Edit it and save.")
            input("Press Enter when done...")
            try:
                with open("temp_script_edit.json", "r") as f:
                    script_data = json.load(f)
                print("[*] Reloaded script.")
            except Exception as e:
                print(f"[!] Error loading file: {e}")
        elif action == "Discard & Exit":
            sys.exit(0)

    # 3. Asset Generation & Rendering
    print("\n[Step 3] Production")
    
    project_name = "".join(x for x in selected_topic if x.isalnum())[:20]
    output_dir = os.path.join("output", project_name)
    os.makedirs(output_dir, exist_ok=True)
    
    scenes = script_data.get('scenes', [])
    processed_scenes = []
    
    editor = VideoEditor()
    
    from tqdm import tqdm
    
    print(f"[*] Generative Phase: {len(scenes)} scenes")
    
    for i, scene in enumerate(tqdm(scenes)):
        scene_id = f"scene_{i:02d}"
        
        # Audio
        audio_path = os.path.join(output_dir, f"{scene_id}.mp3")
        await generate_audio(scene['text'], audio_path, voice="en-US-ChristopherNeural") # Deep voice
        
        # Visual
        visual_path = os.path.join(output_dir, f"{scene_id}.jpg")
        # Enhance prompt for Noir style
        noir_prompt = f"Dark Noir Style, High Contrast, {scene['visual_prompt']}, cinematic lighting, 8k, bw-photography"
        try:
            generate_gemini_image(noir_prompt, visual_path)
        except Exception as e:
            print(f"[!] Visual Gen Error: {e}")
            # Fallback black screen
            from PIL import Image
            Image.new('RGB', (1080, 1920), color='black').save(visual_path)

        processed_scenes.append({
            'audio_path': audio_path,
            'video_path': visual_path,
            'text': scene['text'], # Could be subtitles
            'vocal_action': 'talking' # Default for now
        })

    # 4. Final Render
    print("\n[Step 4] Final Cut")
    final_output = os.path.join(output_dir, "final_cut.mp4")
    
    # Select Music
    music_style = script_data.get('music_mood', 'tense')
    bg_music_path = f"assets/music/{music_style}.mp3" # Placeholder logic
    if not os.path.exists(bg_music_path):
        bg_music_path = None # Silent if missing
        
    editor.create_video(processed_scenes, final_output, is_short=True, bg_music_path=bg_music_path, style="noir")
    
    print(f"\n[SUCCESS] Video saved to: {final_output}")
    os.system(f"start {final_output}")

if __name__ == "__main__":
    try:
        asyncio.run(run_director())
    except KeyboardInterrupt:
        print("\n[!] Production Cancelled.")
