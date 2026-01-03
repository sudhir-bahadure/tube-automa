import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

def setup_youtube():
    print("=====================================================")
    print("      YOUTUBE CHANNEL AUTHENTICATION WIZARD")
    print("=====================================================")
    print("This script will help you generate the credentials needed")
    print("to upload videos to your SPECIFIC NEW CHANNEL.")
    print("\n[STEP 1] You need a OAuth 2.0 Client ID from Google Cloud Console.")
    print("         If you haven't created one yet, look at SECRETS_SETUP.md")
    print("=====================================================\n")

    # 1. Get Client Config
    client_config = {}
    if os.path.exists("client_secrets.json"):
        print("[*] Found 'client_secrets.json' in directory!")
        with open("client_secrets.json", "r") as f:
            client_config = json.load(f)
    else:
        print("Paste your Client ID and Client Secret below:")
        default_id = "134780437780-fnvpe4bqc11s6k9648cbcr0cibj9qc7f.apps.googleusercontent.com"
        client_id = input(f"Client ID (Press Enter for default): ").strip() or default_id
        client_secret = input("Client Secret: ").strip()
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
    print("THAT OWNS THE ***NEW CHANNEL*** you want to upload to.")
    print("If it's a Brand Account, select that specific Brand Account.")
    
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)
    
    print("\n=====================================================")
    print("             AUTHENTICATION SUCCESSFUL!              ")
    print("=====================================================")
    print("Save these 3 values as GitHub Secrets:")
    print("-----------------------------------------------------")
    print(f"YOUTUBE_CLIENT_ID:     {client_config['installed']['client_id']}")
    print(f"YOUTUBE_CLIENT_SECRET: {client_config['installed']['client_secret']}")
    print(f"YOUTUBE_REFRESH_TOKEN: {creds.refresh_token}")
    print("-----------------------------------------------------")
    
    # Save to file so the Agent can read it
    with open("temp_auth_result.txt", "w") as f:
        f.write(f"YOUTUBE_CLIENT_ID={client_config['installed']['client_id']}\n")
        f.write(f"YOUTUBE_CLIENT_SECRET={client_config['installed']['client_secret']}\n")
        f.write(f"YOUTUBE_REFRESH_TOKEN={creds.refresh_token}\n")
    print("[*] Secrets saved to 'temp_auth_result.txt'")

    print("NOTE: The Refresh Token is the key to accessing your specific channel forever.")

if __name__ == "__main__":
    setup_youtube()
