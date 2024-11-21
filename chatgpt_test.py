import os
import csv
import pandas as pd
import requests

# Step 1: Load EMU Users List
def load_emu_users_list(file_path):
    return pd.read_excel(file_path)

def find_user_in_emu(mannequin_user, emu_users_df):
    # Check if the mannequin_user matches either the login or name column in EMU users
    matched_user = emu_users_df[
        (emu_users_df['login'] == mannequin_user) | (emu_users_df['name'] == mannequin_user)
    ]
    if not matched_user.empty:
        return matched_user.iloc[0].to_dict()  # Return the first matched record as a dictionary
    return None

# Step 2: Fetch Organization Members
def fetch_org_members(org_name, token):
    url = f"https://api.github.com/orgs/{org_name}/members"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()  # List of members
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
        return []

# Step 3: Fetch User Emails
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
        print(f"Error: {response.status_code}")
        print(response.json())
        return None

# Step 4: Read and Update User Mappings Template
def process_user_mappings(user_mappings_file, emu_users_file, org_name, token):
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
        mannequin_user = mapping["mannequin_user"]
        matched_emu_user = find_user_in_emu(mannequin_user, emu_users_df)
        
        if matched_emu_user:
            emu_email = matched_emu_user.get("email")
            for org_user, email in org_member_emails.items():
                if email == emu_email:
                    mapping["target-user"] = org_user
                    break

    print("Writing updates back to the user mappings file...")
    with open(user_mappings_file, mode='w', newline='') as file:
        fieldnames = ["mannequin_user", "mannequin_id", "target-user"]
        csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_writer.writerows(mappings)
    print("Process completed successfully!")

# Main Entry Point
if __name__ == "__main__":
    # Environment Variables
    EMU_USERS_FILE = os.getenv("EMU_USERS_FILE", "emu-users.xlsx")  # Excel file with EMU user data
    USER_MAPPINGS_FILE = os.getenv("USER_MAPPINGS_FILE", "user-mappings-template.csv")  # CSV file to update
    ORG_NAME = os.getenv("ORG_NAME", "your_org_name_here")  # GitHub organization name
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "your_github_token_here")  # Personal Access Token (PAT)

    process_user_mappings(
        user_mappings_file=USER_MAPPINGS_FILE,
        emu_users_file=EMU_USERS_FILE,
        org_name=ORG_NAME,
        token=GITHUB_TOKEN
    )
