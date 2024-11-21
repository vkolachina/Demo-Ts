import os
import sys
import csv
import logging
import requests
import time
from github import Github

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables and constants
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
ORG_NAME = os.getenv('ORG_NAME')
CSV_FILE = os.getenv('CSV_FILE')

if not GITHUB_TOKEN:
    logging.error("GITHUB_TOKEN not found. Please set the GITHUB_TOKEN environment variable.")
    sys.exit(1)

if not CSV_FILE:
    logging.error("CSV_FILE not found. Please set the CSV_FILE environment variable.")
    sys.exit(1)

GITHUB_API_URL = "https://api.github.com"
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
                return get_user_id(identifier.split('@')[0])  # Try with the part before @
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

def validate_csv(csv_file):
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV file not found: {csv_file}")
    
    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        header = next(csv_reader, None)
        if header != ['mannequin_username', 'mannequin_id', 'role', 'target']:
            raise ValueError("CSV file does not have the correct header format")

def process_mannequins(csv_file):
    with open(csv_file, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            mannequin_username = row['mannequin_username']
            identifier = row['mannequin_id']  # This can now be email or username
            role = row['role']
            target = row['target']

            try:
                validate_input(identifier, target, role)
                github_role = determine_role(role)
                add_user_to_target(identifier, target, github_role)
            except ValueError as e:
                logging.error(f"Invalid input: {row}. Error: {str(e)}")
            except Exception as e:
                logging.error(f"Unexpected error processing: {row}. Error: {str(e)}")

def main():
    try:
        validate_csv(CSV_FILE)
        
        # Fetch organization members and their emails
        members = fetch_org_members(ORG_NAME, GITHUB_TOKEN)
        for member in members:
            username = member["login"]
            email = fetch_user_email(username, GITHUB_TOKEN)
            if email:
                print(f"Username: {username}, Email: {email}")
        
        # Process mannequins from CSV
        process_mannequins(CSV_FILE)

    except (FileNotFoundError, ValueError) as e:
        logging.error(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
