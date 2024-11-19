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

def reclaim_mannequin(mannequin_id, target_user):
    url = f"{GITHUB_API_URL}/enterprises/{ORG_NAME}/mannequins/{mannequin_id}/reclaim"
    data = {
        "target_user_id": target_user,
        "skip_invitation": True
    }
    try:
        make_request(url, method='post', data=data)
        logging.info(f"Successfully reclaimed mannequin {mannequin_id} for user {target_user}")
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
        if header != ['mannequin_username', 'mannequin_id', 'target-user']:
            raise ValueError("CSV file does not have the correct header format")

def process_mannequins(csv_file):
    org_members = {member['login']: member for member in get_org_members(ORG_NAME)}

    with open(csv_file, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            mannequin_username = row['mannequin_username']
            mannequin_id = row['mannequin_id']
            target_user = row['target-user']

            if mannequin_username in org_members:
                mannequin_email = get_user_email(mannequin_username)
                target_user_email = get_user_email(target_user)
                
                if mannequin_email and target_user_email:
                    success = reclaim_mannequin(mannequin_id, target_user)
                    if success:
                        logging.info(f"Successfully reclaimed mannequin {mannequin_id} ({mannequin_username}) for user {target_user}")
                    else:
                        logging.error(f"Failed to reclaim mannequin {mannequin_id} ({mannequin_username})")
                else:
                    logging.warning(f"Could not fetch email for mannequin {mannequin_username} or target user {target_user}")
            else:
                logging.warning(f"Mannequin {mannequin_username} not found in organization members")

def main():
    try:
        validate_csv(CSV_FILE)
        process_mannequins(CSV_FILE)
    except (FileNotFoundError, ValueError) as e:
        logging.error(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
