import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

import argparse

def setup_youtube(client_id_arg=None, client_secret_arg=None):
    print("=====================================================")
    print("      YOUTUBE CHANNEL AUTHENTICATION WIZARD")
    print("=====================================================")
    print("This script will help you generate the credentials needed")
    print("to upload videos to your SPECIFIC CHANNEL.")
    
    # 1. Get Client Config
    client_config = {}
    if os.path.exists("client_secrets.json"):
        print("[*] Found 'client_secrets.json' in directory!")
        with open("client_secrets.json", "r") as f:
            client_config = json.load(f)
    else:
        print("\n[STEP 1] Setting up OAuth Client Credentials...")
        default_id = "134780437780-fnvpe4bqc11s6k9648cbcr0cibj9qc7f.apps.googleusercontent.com"
        
        client_id = client_id_arg or input(f"Client ID (Press Enter for default): ").strip() or default_id
        client_secret = client_secret_arg or input("Client Secret: ").strip()
        
        if not client_secret:
            print("[!] ERROR: Client Secret is required.")
            return

        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost"]
            }
        }

    # 2. Run OAuth Flow
    print("\n[STEP 2] Authenticating...")
    print("A browser window will open. PLEASE LOGIN WITH THE ACCOUNT")
    print("THAT OWNS THE CHANNEL you want to upload to.")
    
    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly"
    ]
    
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)
    
    print("\n=====================================================")
    print("             AUTHENTICATION SUCCESSFUL!              ")
    print("=====================================================")
    print(f"YOUTUBE_CLIENT_ID:     {client_config['installed']['client_id']}")
    print(f"YOUTUBE_CLIENT_SECRET: {client_config['installed']['client_secret']}")
    print(f"YOUTUBE_REFRESH_TOKEN: {creds.refresh_token}")
    print("=====================================================\n")
    
    # Save to file
    with open("temp_auth_result.txt", "w") as f:
        f.write(f"YOUTUBE_CLIENT_ID={client_config['installed']['client_id']}\n")
        f.write(f"YOUTUBE_CLIENT_SECRET={client_config['installed']['client_secret']}\n")
        f.write(f"YOUTUBE_REFRESH_TOKEN={creds.refresh_token}\n")
    print("[*] Secrets saved to 'temp_auth_result.txt'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Auth Setup")
    parser.add_argument("--client-id", help="Google Cloud OAuth Client ID")
    parser.add_argument("--client-secret", help="Google Cloud OAuth Client Secret")
    args = parser.parse_args()
    
    setup_youtube(args.client_id, args.client_secret)
