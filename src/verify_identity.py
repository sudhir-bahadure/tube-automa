import os
import sys
from youtube_uploader import get_authenticated_service, get_channel_handle

def main():
    print("=== TubeAutoma Identity Debugger ===")
    
    # 1. Check Env Vars
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
    expected = os.environ.get("EXPECTED_HANDLE")
    
    print(f"[*] Checking Environment:")
    print(f"    CLIENT_ID: {'[SET]' if client_id else '[MISSING]'}")
    print(f"    CLIENT_SECRET: {'[SET]' if client_secret else '[MISSING]'}")
    print(f"    REFRESH_TOKEN: {'[SET]' if refresh_token else '[MISSING]'}")
    print(f"    EXPECTED_HANDLE: {expected if expected else '[NONE]'}")
    
    if not all([client_id, client_secret, refresh_token]):
        print("\n[!] ERROR: Missing basic credentials. Add them to your environment.")
        return

    # 2. Try Auth
    print("\n[*] Attempting YouTube Authentication...")
    youtube = get_authenticated_service()
    if not youtube:
        print("[!] FAILED: Could not build authenticated service.")
        return

    # 3. Get Identity
    print("[*] Fetching Channel Identity...")
    handle = get_channel_handle(youtube)
    
    print(f"\n[SUMMARY]")
    print(f"    Detected Handle: @{handle}")
    
    if handle == "unknown":
        print("    STATUS: [FAILED] (Authentication or Scopes issue)")
    elif expected and expected.lower() not in handle.lower():
        print(f"    STATUS: [MISMATCH] (Expected: {expected})")
    else:
        print("    STATUS: [MATCH] (Ready to Upload)")
        
    print("\n=====================================")

if __name__ == "__main__":
    main()
