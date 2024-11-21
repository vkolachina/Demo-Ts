import os
import csv
import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Step 1: Load EMU Users List
def load_emu_users_list(file_path):
    """Load EMU user data from an Excel file."""
    return pd.read_excel(file_path)

def find_user_in_emu(mannequin_user, emu_users_df):
    """
    Find a user in the EMU users list by matching the mannequin_user
    with either the 'login' or 'name' column.
    """
    matched_user = emu_users_df[
        (emu_users_df['login'] == mannequin_user) | (emu_users_df['name'] == mannequin_user)
    ]
    if not matched_user.empty:
        return matched_user.iloc[0].to_dict()  # Return the first matched record as a dictionary
    return None

# Step 2: Fetch Organization Members
def fetch_org_members(org_name, token):
    """Fetch all members of a GitHub organization."""
    url = f"https://api.github.com/orgs/{org_name}/members"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()  # List of members
    else:
        print(f"Error fetching organization members: {response.status_code}")
        print(response.json())
        return []

# Step 3: Fetch User Emails
def fetch_user_email(username, token):
    """Fetch the email of a GitHub user."""
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
        print(f"Error fetching email for user {username}: {response.status_code}")
        print(response.json())
        return None

# Step 4: Read and Update User Mappings Template
def process_user_mappings(user_mappings_file, emu_users_file, org_name, token):
    """
    Read the user-mappings-template.csv file, find matches in the EMU users list,
    and update the 'target-user' field in the same file.
    """
    print("Loading EMU users list...")
    emu_users_df = load_emu_users_list(emu_users_file)

    print("Reading user mappings template...")
    with open(user_mappings_file, mode='r') as file:
        csv_reader = csv.DictReader(file)
        mappings = list(csv_reader)  # Convert CSV data to a list of dictionaries

    print("Fetching organization members...")
    org_members = fetch_org_members(org_name, token)
    
    print("Fetching email addresses of organization members...")
    org_member_emails = {
        member["login"]: fetch_user_email(member["login"], token)
        for member in org_members
    }

    print("Processing user mappings...")
    for mapping in mappings:
        mannequin_user = mapping.get("mannequin-user")  # Updated to match new header
        if not mannequin_user:
            print(f"Skipping row due to missing 'mannequin-user': {mapping}")
            continue

        matched_emu_user = find_user_in_emu(mannequin_user, emu_users_df)
        if matched_emu_user:
            emu_email = matched_emu_user.get("email")
            for org_user, email in org_member_emails.items():
                if email == emu_email:
                    mapping["target-user"] = org_user
                    break

    print("Writing updates back to the user mappings file...")
    with open(user_mappings_file, mode='w', newline='') as file:
        fieldnames = ["mannequin-user", "mannequin-id", "target-user"]  # Updated to match new headers
        csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_writer.writerows(mappings)
    print("Process completed successfully!")

# Main Entry Point
if __name__ == "__main__":
    # Load variables from .env file
    EMU_USERS_FILE = os.getenv("EMU_USERS_FILE")  # Path to the Excel file with EMU user data
    USER_MAPPINGS_FILE = os.getenv("USER_MAPPINGS_FILE")  # Path to the CSV file to update
    ORG_NAME = os.getenv("ORG_NAME")  # GitHub organization name
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # GitHub Personal Access Token (PAT)

    # Validate required environment variables
    if not EMU_USERS_FILE or not USER_MAPPINGS_FILE or not ORG_NAME or not GITHUB_TOKEN:
        print("Error: Missing required environment variables.")
        print("Ensure EMU_USERS_FILE, USER_MAPPINGS_FILE, ORG_NAME, and GITHUB_TOKEN are set in the .env file.")
        exit(1)

    # Process the user mappings
    process_user_mappings(
        user_mappings_file=USER_MAPPINGS_FILE,
        emu_users_file=EMU_USERS_FILE,
        org_name=ORG_NAME,
        token=GITHUB_TOKEN
    )
