import os
import json
import datetime

# Paths to important files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

TRACKING_FILES = [
    os.path.join(BASE_DIR, 'used_jokes.json'),
    os.path.join(BASE_DIR, 'used_videos.json'),
    os.path.join(ASSETS_DIR, 'daily_plan.json'),
    os.path.join(ASSETS_DIR, 'strategy_history.json'),
    os.path.join(ASSETS_DIR, 'analyst_directives.json'),
    os.path.join(ASSETS_DIR, 'jokes_db.json')
]

def check_json_integrity(file_path):
    """Checks if a JSON file is valid. If not, attempts to fix or reset it."""
    if not os.path.exists(file_path):
        print(f"[?] Doctor: {os.path.basename(file_path)} missing. Initializing...")
        return False, "missing"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True, "ok"
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[!] Doctor: Integrity error in {os.path.basename(file_path)}: {e}")
        return False, "corrupted"

def repair_file(file_path, status):
    """Repairs or resets a corrupted or missing file."""
    filename = os.path.basename(file_path)
    print(f"[*] Doctor: Repairing {filename}...")
    
    default_content = {}
    if filename == 'jokes_db.json':
        # Don't reset the main DB if missing, warn instead
        print(f"  [CRITICAL] {filename} is missing/corrupted! Please restore from backup.")
        return
    
    if filename == 'used_jokes.json' or filename == 'used_videos.json':
        default_content = {}
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_content, f, indent=2)
        print(f"  [SUCCESS] {filename} reset to default.")
    except Exception as e:
        print(f"  [ERROR] Failed to repair {filename}: {e}")

def cleanup_temp_files():
    """Removes leftover temporary files from failed runs."""
    print("[*] Doctor: Cleaning up temporary assets...")
    count = 0
    for file in os.listdir(BASE_DIR):
        if file.endswith((".mp4", ".mp3", ".wav")) and file.startswith(("viral_", "temp_")):
            try:
                os.remove(os.path.join(BASE_DIR, file))
                count += 1
            except:
                pass
    print(f"  [OK] Removed {count} temporary files.")

def main():
    print(f"\n--- TubeAutoma Doctor: Health Check {datetime.datetime.now().isoformat()} ---")
    
    # 1. Ensure directories exist
    for d in [ASSETS_DIR, LOGS_DIR]:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"[*] Created missing directory: {os.path.basename(d)}")

    # 2. Check JSON Integrity
    for file_path in TRACKING_FILES:
        is_ok, status = check_json_integrity(file_path)
        if not is_ok:
            repair_file(file_path, status)

    # 3. Cleanup temp files
    cleanup_temp_files()

    # 4. Success Signature
    print("\n--- Health Check Complete: System is Operational ---")

if __name__ == "__main__":
    main()
