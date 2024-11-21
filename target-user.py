import csv
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file (optional, if you are using a .env file)
load_dotenv()

# Code A: Fetch GitHub organization members
def fetch_org_members(org_name, token):
    url = f"https://api.github.com/orgs/{org_name}/members"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()  # Return the list of members
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
        return []

# Code B: Fetch email by GitHub username
def fetch_user_email(username, token):
    url = f"https://api.github.com/users/{username}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        return user_data.get("email")  # Return email
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
        return None

# Task to process the CSV and match emails
def process_csv_and_reclaim_users(csv_file, org_name, token):
    # Fetch members from the GitHub organization
    members = fetch_org_members(org_name, token)
    
    # Prepare a list of emails for the members
    user_email_mapping = {}
    for member in members:
        username = member['login']
        email = fetch_user_email(username, token)
        if email:
            user_email_mapping[email] = username  # Store the email and GitHub handle

    # Process the CSV file and update the target-user column
    updated_rows = []
    with open(csv_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            mannequin_user = row['mannequin-user']
            mannequin_email = row['mannequin-id']  # You may also check 'mannequin-id' or other columns for email
            
            # Check if the mannequin's email matches any in the GitHub member list
            if mannequin_email in user_email_mapping:
                target_user = user_email_mapping[mannequin_email]
                row['target-user'] = target_user  # Reclaim the mannequin by setting the target-user
            updated_rows.append(row)

    # Write updated rows back to the same CSV file
    with open(csv_file, 'w', newline='', encoding='utf-8') as outfile:
        fieldnames = ['mannequin-user', 'mannequin-id', 'target-user']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)
    
    print(f"CSV has been updated and saved as '{csv_file}'.")

# Example usage (now pulling values from environment variables)
org_name = os.getenv("ORG_NAME")  # Fetch organization name from environment variable
token = os.getenv("GITHUB_TOKEN")  # Fetch GitHub token from environment variable
csv_file = os.getenv("CSV_FILE")  # Fetch CSV file name from environment variable

# Validate that the environment variables are set
if not org_name or not token or not csv_file:
    print("Please set the environment variables ORG_NAME, GITHUB_TOKEN, and CSV_FILE.")
else:
    process_csv_and_reclaim_users(csv_file, org_name, token)
