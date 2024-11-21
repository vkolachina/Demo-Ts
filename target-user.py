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

# Main task: Process the CSV file and update target-user
def process_csv_and_update(csv_file, org_name, token):
    # Step 1: Fetch organization members
    print(f"Fetching members of the organization: {org_name}")
    members = fetch_org_members(org_name, token)

    # Step 2: Create a mapping of email to username
    print("Fetching emails for organization members...")
    email_to_username = {}
    for member in members:
        username = member['login']
        email = fetch_user_email(username, token)
        if email:
            email_to_username[email] = username  # Map email to username

    # Step 3: Process the CSV file
    print(f"Processing the CSV file: {csv_file}")
    updated_rows = []
    with open(csv_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            mannequin_user = row['mannequin-user']  # GitHub handle
            mannequin_id = row['mannequin-id']  # Email or ID to be kept as is
            target_user = row.get('target-user', '')  # Ensure target-user is handled

            # Check if mannequin-id matches any email in the organization
            if mannequin_id in email_to_username:
                target_user = email_to_username[mannequin_id]  # Get corresponding username
                print(f"Match found: {mannequin_id} -> {target_user}")
            else:
                print(f"No match found for: {mannequin_id}")

            # Update the row with the target-user
            row['target-user'] = target_user
            updated_rows.append(row)

    # Step 4: Write the updated data back to the same CSV file
    print(f"Updating the CSV file: {csv_file}")
    with open(csv_file, 'w', newline='', encoding='utf-8') as outfile:
        fieldnames = ['mannequin-user', 'mannequin-id', 'target-user']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

    print(f"CSV update completed. File saved as '{csv_file}'.")

# Example usage
org_name = os.getenv("ORG_NAME")  # Fetch organization name from environment variable
token = os.getenv("GITHUB_TOKEN")  # Fetch GitHub token from environment variable
csv_file = "user-mappings-template.csv"  # Fixed CSV file name

# Validate environment variables and run the script
if not org_name or not token:
    print("Please set the environment variables ORG_NAME and GITHUB_TOKEN.")
else:
    process_csv_and_update(csv_file, org_name, token)
