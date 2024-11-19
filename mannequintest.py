import os
import sys
import csv
import logging
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
GITHUB_API_URL = "https://api.github.com"
TOKEN = os.getenv('GITHUB_TOKEN')
CSV_FILE = os.getenv('CSV_FILE')
ORG_NAME = os.getenv('ORG_NAME')

if not all([TOKEN, CSV_FILE, ORG_NAME]):
    logging.error("Missing required environment variables. Please set GITHUB_TOKEN, CSV_FILE, and ORG_NAME.")
    sys.exit(1)

def make_request(url, method='get', data=None, max_retries=3):
    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, headers=headers, json=data)
            if response.status_code == 403 and 'rate limit' in response.text.lower():
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                sleep_time = max(reset_time - time.time(), 0) + 1
                logging.warning(f"Rate limit hit. Sleeping for {sleep_time} seconds.")
                time.sleep(sleep_time)
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                logging.error(f"Request failed after {max_retries} attempts. Error: {str(e)}")
                raise
            logging.warning(f"Request failed. Retrying... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)  # Exponential backoff

def get_org_members(org_name):
    url = f"{GITHUB_API_URL}/orgs/{org_name}/members"
    return make_request(url)

def get_user_email(username):
    url = f"{GITHUB_API_URL}/users/{username}"
    user_data = make_request(url)
    return user_data.get('email')

def get_emu_users():
    # This function should be implemented to fetch users from your EMU system
    # For now, we'll return an empty list
    return []

def reclaim_mannequin(mannequin_id, target_user_id):
    url = f"{GITHUB_API_URL}/enterprises/{os.getenv('GITHUB_ENTERPRISE_NAME')}/mannequins/{mannequin_id}/reclaim"
    data = {
        "target_user_id": target_user_id,
        "skip_invitation": True
    }
    try:
        make_request(url, method='post', data=data)
        logging.info(f"Successfully reclaimed mannequin {mannequin_id} for user {target_user_id}")
        return True
    except requests.RequestException as e:
        logging.error(f"Failed to reclaim mannequin {mannequin_id}: {str(e)}")
        return False

def validate_csv(csv_file):
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV file not found: {csv_file}")
    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        header = next(csv_reader, None)
        if header != ['mannequin_username', 'mannequin_id']:
            raise ValueError("CSV file does not have the correct header format")

def process_mannequins(csv_file):
    org_members = {member['login']: member for member in get_org_members(ORG_NAME)}
    emu_users = get_emu_users()

    with open(csv_file, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            mannequin_username = row['mannequin_username']
            mannequin_id = row['mannequin_id']

            if mannequin_username in org_members:
                email = get_user_email(mannequin_username)
                if email:
                    emu_user = next((user for user in emu_users if user['email'] == email), None)
                    if emu_user:
                        target_user_id = emu_user['id']
                        success = reclaim_mannequin(mannequin_id, target_user_id)
                        if success:
                            logging.info(f"Successfully reclaimed mannequin {mannequin_id} for user {target_user_id}")
                        else:
                            logging.error(f"Failed to reclaim mannequin {mannequin_id}")
                    else:
                        logging.warning(f"No matching EMU user found for {mannequin_username}")
                else:
                    logging.warning(f"No email found for GitHub user {mannequin_username}")
            else:
                logging.warning(f"GitHub handle {mannequin_username} not found in organization members")

def main():
    try:
        validate_csv(CSV_FILE)
        process_mannequins(CSV_FILE)
    except (FileNotFoundError, ValueError) as e:
        logging.error(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
