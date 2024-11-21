import os
import csv
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
ORG_NAME = os.getenv('ORG_NAME')
GHEC_CSV = os.getenv('GHEC_CSV')

def fetch_org_members(org_name, token):
    url = f"https://api.github.com/orgs/{org_name}/members"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching org members: {response.status_code}")
        return []

def fetch_user_email(username, token):
    url = f"https://api.github.com/users/{username}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        return user_data.get("email")
    else:
        print(f"Error fetching user email: {response.status_code}")
        return None

def get_emu_users():
    emu_users = {}
    members = fetch_org_members(ORG_NAME, GITHUB_TOKEN)
    for member in members:
        username = member["login"]
        email = fetch_user_email(username, GITHUB_TOKEN)
        if email:
            emu_users[email] = username
    return emu_users

def process_ghec_csv(ghec_csv, emu_users):
    updated_rows = []
    with open(ghec_csv, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            mannequin_user = row['mannequin_user']
            mannequin_email = fetch_user_email(mannequin_user, GITHUB_TOKEN)
            if mannequin_email and mannequin_email in emu_users:
                row['target_user'] = emu_users[mannequin_email]
            else:
                row['target_user'] = ''
            updated_rows.append(row)
    
    # Write updated data back to CSV
    with open(ghec_csv, 'w', newline='') as file:
        fieldnames = ['mannequin_user', 'mannequin_id', 'target_user']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

def main():
    emu_users = get_emu_users()
    process_ghec_csv(GHEC_CSV, emu_users)
    print("CSV file updated with target users.")

if __name__ == "__main__":
    main()
