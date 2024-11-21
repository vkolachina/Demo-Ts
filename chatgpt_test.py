import os
import csv
import pandas as pd
import requests

# Step 1: Load GHEC Users List
def load_ghec_users_list(file_path):
    return pd.read_excel(file_path)

def find_user_in_ghec(mannequin_user, ghec_users_df):
    matched_user = ghec_users_df[
        (ghec_users_df['login'] == mannequin_user) | (ghec_users_df['name'] == mannequin_user)
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

# Step 4: Read User Mappings Template
def read_user_mappings_template(file_path):
    mappings = []
    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            mappings.append(row)
    return mappings

# Step 5: Process User Mappings and Update CSV
def process_user_mappings(
    user_mappings_file, ghec_users_file, org_name, token, output_file
):
    print("Loading GHEC users list...")
    ghec_users_df = load_ghec_users_list(ghec_users_file)
    print("Reading user mappings template...")
    user_mappings = read_user_mappings_template(user_mappings_file)
    print("Fetching organization members...")
    org_members = fetch_org_members(org_name, token)
    
    print("Fetching email addresses of organization members...")
    org_member_emails = {
        member["login"]: fetch_user_email(member["login"], token)
        for member in org_members
    }

    print("Processing user mappings...")
    updated_mappings = []
    
    for mapping in user_mappings:
        mannequin_user = mapping["mannequin_user"]
        matched_ghec_user = find_user_in_ghec(mannequin_user, ghec_users_df)
        
        if matched_ghec_user:
            ghec_email = matched_ghec_user.get("email")
            for org_user, email in org_member_emails.items():
                if email == ghec_email:
                    mapping["target-user"] = org_user
                    break
        updated_mappings.append(mapping)
    
    print("Writing updated mappings to output CSV...")
    with open(output_file, mode='w', newline='') as file:
        fieldnames = ["mannequin_user", "mannequin_id", "target-user"]
        csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_writer.writerows(updated_mappings)
    print("Process completed successfully!")

# Main Entry Point
if __name__ == "__main__":
    # Environment Variables
    GHEC_USERS_FILE = os.getenv("GHEC_USERS_FILE", "ghec-users.xlsx")
    USER_MAPPINGS_FILE = os.getenv("USER_MAPPINGS_FILE", "user-mappings-template.csv")
    OUTPUT_FILE = os.getenv("OUTPUT_FILE", "updated-user-mappings.csv")
    ORG_NAME = os.getenv("ORG_NAME", "your_org_name_here")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "your_github_token_here")

    process_user_mappings(
        user_mappings_file=USER_MAPPINGS_FILE,
        ghec_users_file=GHEC_USERS_FILE,
        org_name=ORG_NAME,
        token=GITHUB_TOKEN,
        output_file=OUTPUT_FILE
    )
