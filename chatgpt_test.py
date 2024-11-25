import requests
import pandas as pd
import os
from dotenv import load_dotenv
import csv

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ORG_NAME = os.getenv("ORG_NAME")
EMU_USERS_FILE = os.getenv("EMU_USERS_FILE")
USER_MAPPINGS_FILE = os.getenv("USER_MAPPINGS_FILE")

# Function to fetch organization members
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
        print(f"Error: {response.status_code}")
        print(response.json())
        return []

# Function to fetch user email from GitHub
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

# Function to find a user in the EMU users list based on GitHub handle
def find_user_in_emu(github_handle, emu_users_df):
    return emu_users_df[emu_users_df['login'] == github_handle].iloc[0] if not emu_users_df[emu_users_df['login'] == github_handle].empty else None

# Function to process the user mappings from the CSV file
def process_user_mappings(user_mappings_file, emu_users_df, org_member_emails, token):
    print("Reading user mappings template")
    
    # Read the CSV file with user mappings
    mappings = []
    with open(user_mappings_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            mappings.append(row)

    print("Processing user mappings")
    
    # Iterate through each mapping and check for matches
    for mapping in mappings:
        mannequin_user = mapping.get("mannequin-user")  # Updated to match new header
        if not mannequin_user:
            print(f"Skipping row due to missing 'mannequin-user': {mapping}")
            continue

        # Find the matching EMU user
        matched_emu_user = find_user_in_emu(mannequin_user, emu_users_df)
        
        if not matched_emu_user.empty:
            # Only print the login ID or name and the SAML Name ID when a match is found
            emu_email = matched_emu_user.get("email")
            emu_saml_name_id = matched_emu_user.get("saml_name_id")  # Assuming this is the field you're referring to
            
            # Print the relevant user information
            print(f"Found match in EMU for {mannequin_user}: {matched_emu_user['login']} / {matched_emu_user['name']} (SAML ID: {emu_saml_name_id})")

            # Now match this with GitHub organization member email
            for org_user, email in org_member_emails.items():
                if email == emu_email:
                    # Print the matched GitHub user
                    print(f"Matched GitHub user {org_user} with email {email}")
                    mapping["target-user"] = org_user
                    break
            else:
                # No match found with GitHub organization members
                print(f"No matching email in GitHub org for {emu_email}")
        else:
            # No match found in EMU
            print(f"No match found in EMU for {mannequin_user}")

    # Write the updated mappings back to the CSV file
    print("Writing updates back to the user mappings file")
    with open(user_mappings_file, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ["mannequin-user", "mannequin-id", "target-user"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(mappings)

    print("Process completed successfully")

# Main function to execute the process
def main():
    print("Loading EMU users list")
    
    # Load the EMU users Excel file
    emu_users_df = pd.read_excel(EMU_USERS_FILE)

    print("Fetching organization members")
    org_members = fetch_org_members(ORG_NAME, GITHUB_TOKEN)
    org_member_emails = {}
    
    # Create a dictionary with GitHub usernames as keys and email addresses as values
    for org_member in org_members:
        email = fetch_user_email(org_member["login"], GITHUB_TOKEN)
        if email:
            org_member_emails[org_member["login"]] = email

    # Process the user mappings
    process_user_mappings(USER_MAPPINGS_FILE, emu_users_df, org_member_emails, GITHUB_TOKEN)

if __name__ == "__main__":
    main()
