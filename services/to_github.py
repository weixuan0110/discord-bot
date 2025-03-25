import os
import requests
import base64
import datetime

GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")
GITHUB_PAT = os.getenv("GITHUB_PAT")
PARENT_FOLDER = os.getenv("PARENT_FOLDER")

GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents"

def create_folder_structure(ctf, category, challenge_name, content, sender_username):
    """
    Creates a folder structure and uploads content/files to GitHub.
    :param category: Main folder name (Category). (This is now ignored)
    :param challenge_name: Subfolder name (Challenge Name).
    :param content: Content to be uploaded as a README.md file.
    """
    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }

    content_with_author = f"{content}\n\nSolved by: {sender_username}"

    parent_path = PARENT_FOLDER
    create_folder_on_github(parent_path, headers)

    current_year = str(datetime.datetime.now().year)
    challenge_path = f"{parent_path}/{current_year}/{ctf}"
    create_folder_on_github(challenge_path, headers)

    writeup_path = f"{challenge_path}/{category}-{challenge_name}.md"
    response = requests.get(f"{GITHUB_API_URL}/{writeup_path}", headers=headers)

    if response.status_code == 200:
        # File exists, compare hash file
        existing_file = response.json()
        existing_content = base64.b64decode(existing_file["content"]).decode("utf-8")
        sha = existing_file["sha"]

        if existing_content.strip() == content_with_author.strip():
            # File exists, same hash, skip
            print(f"File {writeup_path} already exists and content is identical. Skipping.")
            return "exist"
        else:
            # File exists, but content has changed, update
            print(f"File {writeup_path} exists but content has changed. Updating...")
            update_file_on_github(writeup_path, content_with_author, sha, headers)
            return "updated"
    else:
        # File doesn't exist, create it
        print(f"File {writeup_path} does not exist. Creating...")
        upload_file_to_github(writeup_path, content_with_author, headers)
        return "created"


def create_folder_on_github(folder_path, headers):
    """
    Creates an empty folder on GitHub by creating a placeholder file.
    :param folder_path: Path to the folder.
    :param headers: Authorization headers for the GitHub API.
    """
    placeholder_file = f"{folder_path}/.gitkeep"
    data = {
        "message": f"Create folder: {folder_path}",
        "content": "",  # Empty content for .gitkeep
        "branch": "main"  # Replace with your branch name if different
    }
    response = requests.put(f"{GITHUB_API_URL}/{placeholder_file}", json=data, headers=headers)
    if response.status_code not in [201, 422]:  # 422 means the folder already exists
        print(f"Failed to create folder {folder_path}: {response.status_code} - {response.text}")

def upload_file_to_github(file_path, file_content, headers):
    """
    Uploads a file to GitHub.
    :param file_path: Path to the file (including folder structure).
    :param file_content: Content of the file.
    :param headers: Authorization headers for the GitHub API.
    """
    encoded_content = file_content.encode("utf-8")
    data = {
        "message": f"Add file: {file_path}",
        "content": base64.b64encode(encoded_content).decode("utf-8"),
        "branch": "main"  # Replace with your branch name if different
    }
    response = requests.put(f"{GITHUB_API_URL}/{file_path}", json=data, headers=headers)
    if response.status_code == 201:
        print(f"File uploaded successfully: {file_path}")
    else:
        print(f"Failed to upload file {file_path}: {response.status_code} - {response.text}")

def update_file_on_github(file_path, file_content, sha, headers):
    """
    Updates an existing file on GitHub.
    :param file_path: Path to the file (including folder structure).
    :param file_content: New content of the file (binary or text).
    :param sha: SHA of the existing file.
    :param headers: Authorization headers for the GitHub API.
    """
    # Encode the file content as Base64
    if isinstance(file_content, str):  # Text file
        encoded_content = base64.b64encode(file_content.encode("utf-8")).decode("utf-8")
    else:  # Binary file
        encoded_content = base64.b64encode(file_content).decode("utf-8")

    data = {
        "message": f"Update file: {file_path}",
        "content": encoded_content,
        "sha": sha,
        "branch": "main"  # Replace with your branch name if different
    }
    response = requests.put(f"{GITHUB_API_URL}/{file_path}", json=data, headers=headers)
    if response.status_code == 200:
        print(f"File updated successfully: {file_path}")
    else:
        print(f"Failed to update file {file_path}: {response.status_code} - {response.text}")