import os
import requests
import base64
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")
GITHUB_PAT = os.getenv("GITHUB_PAT")
PARENT_FOLDER = os.getenv("PARENT_FOLDER")
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents"

def safe_join(base, *paths):
    joined = os.path.join(base, *paths)
    normalized = os.path.normpath(joined)
    if not normalized.startswith(os.path.normpath(base)):
        raise ValueError("Path traversal detected")
    return normalized

def create_folder_structure(ctf, category, challenge_name, content, sender_username):
    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }
    content_with_author = f"{content}\n\nSolved by: {sender_username}"
    parent_path = PARENT_FOLDER
    create_folder_on_github(parent_path, headers)
    current_year = str(datetime.now().year)
    challenge_path = safe_join(parent_path, current_year, ctf)
    create_folder_on_github(challenge_path, headers)
    writeup_file = f"{category}-{challenge_name}.md"
    writeup_path = safe_join(challenge_path, writeup_file)
    response = requests.get(f"{GITHUB_API_URL}/{writeup_path}", headers=headers)
    if response.status_code == 200:
        existing_file = response.json()
        existing_content = base64.b64decode(existing_file["content"]).decode("utf-8")
        sha = existing_file["sha"]
        if existing_content.strip() == content_with_author.strip():
            print(f"File {writeup_path} already exists and content is identical. Skipping.")
            return "exist"
        else:
            print(f"File {writeup_path} exists but content has changed. Updating...")
            update_file_on_github(writeup_path, content_with_author, sha, headers)
            return "updated"
    else:
        print(f"File {writeup_path} does not exist. Creating...")
        upload_file_to_github(writeup_path, content_with_author, headers)
        return "created"

def create_folder_on_github(folder_path, headers):
    placeholder_file = f"{folder_path}/.gitkeep"
    data = {
        "message": f"Create folder: {folder_path}",
        "content": "",
        "branch": "main"
    }
    response = requests.put(f"{GITHUB_API_URL}/{placeholder_file}", json=data, headers=headers)
    if response.status_code not in [201, 422]:
        print(f"Failed to create folder {folder_path}: {response.status_code} - {response.text}")

def upload_file_to_github(file_path, file_content, headers):
    encoded_content = file_content.encode("utf-8")
    data = {
        "message": f"Add file: {file_path}",
        "content": base64.b64encode(encoded_content).decode("utf-8"),
        "branch": "main"
    }
    response = requests.put(f"{GITHUB_API_URL}/{file_path}", json=data, headers=headers)
    if response.status_code == 201:
        print(f"File uploaded successfully: {file_path}")
    else:
        print(f"Failed to upload file {file_path}: {response.status_code} - {response.text}")

def update_file_on_github(file_path, file_content, sha, headers):
    encoded_content = base64.b64encode(file_content.encode("utf-8")).decode("utf-8")
    data = {
        "message": f"Update file: {file_path}",
        "content": encoded_content,
        "sha": sha,
        "branch": "main"
    }
    response = requests.put(f"{GITHUB_API_URL}/{file_path}", json=data, headers=headers)
    if response.status_code == 200:
        print(f"File updated successfully: {file_path}")
    else:
        print(f"Failed to update file {file_path}: {response.status_code} - {response.text}")
