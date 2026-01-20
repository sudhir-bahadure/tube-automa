import os
import logging
import json

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("automation.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def ensure_dir_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def save_json(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def load_json(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
