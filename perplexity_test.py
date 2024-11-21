import os
import sys
import csv
import logging
import requests
import openpyxl
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
ORG_NAME = os.getenv('ORG_NAME')
GHEC_CSV = os.getenv('GHEC_CSV')
EMU_EXCEL = os.getenv('EMU_EXCEL')

GITHUB_API_URL = "https://api.github.com"

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

def read_ghec_csv(file_path):
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        return list(reader)

def read_emu_excel(file_path):
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active
    emu_users = []
    headers = [cell.value for cell in sheet[1]]
    for row in sheet.iter_rows(min_row=2, values_only=True):
        emu_users.append(dict(zip(headers, row)))
    return emu_users

def process_mannequins(ghec_csv, emu_users):
    ghec_data = read_ghec_csv(ghec_csv)
    updated_data = []

    for mannequin in ghec_data:
        mannequin_username = mannequin['mannequin-user']
        mannequin_id = mannequin['mannequin-id']
        
        email = fetch_user_email(mannequin_username, GITHUB_TOKEN)
        if email:
            target_user = next((user for user in emu_users if user['saml_name_id'] == email), None)
            if target_user:
                mannequin['target-user'] = target_user['login']
                logging.info(f"Found target user: {target_user['login']} for mannequin: {mannequin_username}")
            else:
                logging.warning(f"No target user found for mannequin: {mannequin_username}")
        else:
            logging.warning(f"No email found for mannequin: {mannequin_username}")
        
        updated_data.append(mannequin)

    # Write updated data back to CSV
    with open(ghec_csv, 'w', newline='') as file:
        fieldnames = ['mannequin-user', 'mannequin-id', 'target-user']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_data)

def main():
    if not all([GITHUB_TOKEN, ORG_NAME, GHEC_CSV, EMU_EXCEL]):
        logging.error("Missing required environment variables. Please check your .env file.")
        sys.exit(1)

    try:
        emu_users = read_emu_excel(EMU_EXCEL)
        process_mannequins(GHEC_CSV, emu_users)
        logging.info("CSV file updated with target users.")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
