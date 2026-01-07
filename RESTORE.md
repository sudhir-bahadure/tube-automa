# 🚀 Project Restoration Guide (Post-Format)

If you have just formatted your PC or uninstalled everything, follow these steps to get TubeAutoma back up and running exactly where you left off.

## 1. Prerequisites
- **Git**: [Install Git for Windows](https://git-scm.com/download/win).
- **Python**: [Install Python 3.10+](https://www.python.org/downloads/). Ensure "Add Python to PATH" is checked during installation.
- **VS Code**: [Install VS Code](https://code.visualstudio.com/).
- **Antigravity**: Ensure the Antigravity extension is installed in VS Code.

## 2. Clone the Repository
Open a terminal (PowerShell) and run:
```powershell
cd D:\YT  # Or wherever you want the project
git clone https://github.com/sudhir-bahadure/tube-automa.git "youtube automation backup"
cd "youtube automation backup"
```

## 3. Environment Setup
Create a virtual environment and install dependencies:
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Restore Secrets (CRITICAL)
Since secrets are NOT stored in git for security, you must restore them manually.

### Locally (for development)
Create a `.env` file in the project root and paste your keys:
```text
YOUTUBE_CLIENT_ID=your_id_here
YOUTUBE_CLIENT_SECRET=your_secret_here
YOUTUBE_REFRESH_TOKEN=your_token_here
PEXELS_API_KEY=your_key_here
```
> [!TIP]
> You should have these saved in a secure location (Google Drive, Keep, or a Password Manager).

### GitHub (for Automation)
If you already set these in GitHub Secrets, you don't need to do anything for the automation to work. They will persist on GitHub's servers.

## 5. Resume with Antigravity
1. Open the folder in VS Code.
2. Type **/resume** in the chat.
3. Antigravity will automatically verify everything and continue the daily automation.

---
**Project State maintained in:** `used_jokes.json`, `used_videos.json` (Tracked by Git).
