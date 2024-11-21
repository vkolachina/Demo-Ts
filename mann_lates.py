import os
import csv
import logging
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
ORG_NAME = os.getenv('ORG_NAME')
CSV_FILE = os.getenv('CSV_FILE')

GITHUB_API_URL = "https://api.github.com"

def fetch_user_email(username):
    url = f"{GITHUB_API_URL}/users/{username}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        return user_data.get("email")
    else:
        logging.error(f"Error fetching user email: {response.status_code}")
        return None

def process_mannequins(csv_file):
    with open(csv_file, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            mannequin_username = row['mannequin_user']
            mannequin_id = row['mannequin_id']
            target_user = row['target_user']

            # Fetch email for mannequin user (optional, if needed)
            email = fetch_user_email(mannequin_username)
            if email:
                logging.info(f"Mannequin: {mannequin_username}, Email: {email}")

            # Process target user for reclaiming mannequin
            if target_user:
                logging.info(f"Processing target user: {target_user} for mannequin: {mannequin_username}")
                # Implement further actions like reclaiming mannequin using target_user
                reclaim_mannequin(mannequin_username, target_user)
            else:
                logging.warning(f"No target user specified for mannequin: {mannequin_username}")

def reclaim_mannequin(mannequin_username, target_user):
    # Placeholder function - implement your logic here to reclaim mannequins
    # This might involve API calls or other operations specific to your setup
    logging.info(f"Reclaiming mannequin {mannequin_username} for target user {target_user}")

def main():
    if not GITHUB_TOKEN:
        logging.error("GITHUB_TOKEN not found. Please set it in the .env file.")
        return
    
    if not CSV_FILE:
        logging.error("CSV_FILE not found. Please set it in the .env file.")
        return

    try:
        process_mannequins(CSV_FILE)
    except FileNotFoundError as e:
        logging.error(str(e))
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
