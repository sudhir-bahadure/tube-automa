import requests
import os

def upload_to_telegram(video_path, caption="", bot_token=None, chat_id=None):
    if not bot_token or not chat_id:
        print("Missing Telegram Credentials. Video saved locally but not uploaded.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    
    try:
        with open(video_path, 'rb') as video:
            files = {'video': video}
            data = {'chat_id': chat_id, 'caption': caption}
            
            print(f"Uploading {video_path} to Telegram...")
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                print("Video successfully sent to Telegram!")
                return True
            else:
                print(f"Failed to send video. Status: {response.status_code}, Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"Error sending to Telegram: {e}")
        return False
