import os
import sys
import csv
import logging
import requests
import time
from github import Github
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
ORG_NAME = os.getenv('ORG_NAME')
GHEC_CSV = os.getenv('GHEC_CSV')

GITHUB_API_URL = "https://api.github.com"

# Initialize the GitHub API client
g = Github(GITHUB_TOKEN)

def fetch_org_members(org_name, token):
    url = f"{GITHUB_API_URL}/orgs/{org_name}/members"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Error fetching org members: {response.status_code}")
        return []

def fetch_user_email(username, token):
    url = f"{GITHUB_API_URL}/users/{username}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        return user_data.get("email")
    else:
        logging.error(f"Error fetching user email: {response.status_code}")
        return None

def make_request(url, method='get', data=None, max_retries=3):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    for attempt in range(max_retries):
        try:
            if method == 'get':
                response = requests.get(url, headers=headers)
            elif method == 'post':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'put':
                response = requests.put(url, headers=headers, json=data)
            
            if response.status_code == 403 and 'rate limit' in response.text.lower():
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                sleep_time = max(reset_time - time.time(), 0) + 1
                logging.warning(f"Rate limit hit. Sleeping for {sleep_time} seconds.")
                time.sleep(sleep_time)
                continue
            
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                logging.error(f"Request failed after {max_retries} attempts. Error: {str(e)}")
                raise
            logging.warning(f"Request failed. Retrying... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)

def get_user_id(identifier):
    if '@' in identifier:
        url = f"{GITHUB_API_URL}/search/users?q={identifier}"
        try:
            response = make_request(url)
            users = response.json().get('items', [])
            if users:
                return users[0]['id']
            else:
                logging.warning(f"No user found with email: {identifier}. Trying as username.")
                return get_user_id(identifier.split('@')[0])
        except requests.RequestException as e:
            logging.error(f"Failed to get user ID for email {identifier}. Error: {str(e)}")
            return None
    else:
        url = f"{GITHUB_API_URL}/users/{identifier}"
        try:
            response = make_request(url)
            return response.json()['id']
        except requests.RequestException as e:
            logging.error(f"Failed to get user ID for username {identifier}. Error: {str(e)}")
            return None

def read_csv(file_path):
    with open(file_path, 'r') as file:
        return list(csv.DictReader(file))

def fetch_emu_users():
    # Implement the API call to fetch EMU users here
    # This is a placeholder function
    url = f"{GITHUB_API_URL}/orgs/{ORG_NAME}/members"
    try:
        response = make_request(url)
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch EMU users. Error: {str(e)}")
        return []

def find_target_user(email, emu_users):
    return next((user for user in emu_users if user.get('email') == email), None)

def reclaim_mannequin(mannequin_username, target_username):
    # Implement the logic to reclaim the mannequin here
    logging.info(f"Reclaiming mannequin {mannequin_username} for target user {target_username}")

def process_mannequins(ghec_csv):
    ghec_users = read_csv(ghec_csv)
    emu_users = fetch_emu_users()
    
    for mannequin in ghec_users:
        mannequin_username = mannequin['mannequin-user']
        mannequin_id = mannequin['mannequin-id']
        
        email = fetch_user_email(mannequin_username, GITHUB_TOKEN)
        if email:
            target_user = find_target_user(email, emu_users)
            if target_user:
                logging.info(f"Found target user: {target_user['login']} for mannequin: {mannequin_username}")
                reclaim_mannequin(mannequin_username, target_user['login'])
            else:
                logging.warning(f"No target user found for mannequin: {mannequin_username}")
        else:
            logging.warning(f"No email found for mannequin: {mannequin_username}")

def main():
    if not all([GITHUB_TOKEN, ORG_NAME, GHEC_CSV]):
        logging.error("Missing required environment variables. Please check your .env file.")
        sys.exit(1)

    try:
        process_mannequins(GHEC_CSV)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
