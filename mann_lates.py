import pandas as pd
import os
import re
import csv
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Function to parse parameters from the comment body
def parse_comment(comment_body):
    """Parse parameters from the comment body."""
    emu_users_file = re.search(r'--emu-users-file=(\S+)', comment_body)
    user_mappings_file = re.search(r'--user-mappings-file=(\S+)', comment_body)
    org_name = re.search(r'--org-name=(\S+)', comment_body)

    return {
        "EMU_USERS_FILE": emu_users_file.group(1) if emu_users_file else None,
        "USER_MAPPINGS_FILE": user_mappings_file.group(1) if user_mappings_file else None,
        "ORG_NAME": org_name.group(1) if org_name else None,
    }

# Function to read the Excel file
def read_excel_file(file_path):
    print("Reading the Excel file")
    return pd.read_excel(file_path)

# Function to read the CSV file
def read_csv_file(file_path):
    print("Reading the CSV file")
    with open(file_path, mode='r', newline='', encoding='utf-8') as file:
        return list(csv.DictReader(file))

# Function to update the CSV file
def update_csv_file(file_path, mappings):
    print("Writing updates back to the CSV file")
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ["mannequin-user", "mannequin-id", "target-user"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mappings)
    print("CSV file updated successfully")

# Function to process user mappings
def process_user_mappings(user_mappings_file, emu_users_df, org_suffix):
    print("Processing user mappings")

    mappings = read_csv_file(user_mappings_file)
    for mapping in mappings:
        mannequin_user = mapping.get("mannequin-user")
        if not mannequin_user:
            print(f"Skipping row due to missing 'mannequin-user': {mapping}")
            continue

        # Match the user in the Excel file
        matched_user = emu_users_df[emu_users_df['login'] == mannequin_user]
        if matched_user.empty:
            print(f"No match found for mannequin-user: {mannequin_user}")
            continue

        # Extract email-like value from 'saml_name_id'
        email = matched_user.iloc[0]["saml_name_id"]
        empirical_part = email.split('@')[0]
        target_user = f"{empirical_part}_{org_suffix}"

        mapping["target-user"] = target_user
        print(f"Updated target-user for {mannequin_user} to {target_user}")

    # Update the CSV file with new target-user values
    update_csv_file(user_mappings_file, mappings)

# Main function
def main():
    print("Executing migration script...")

    # Get the COMMENT_BODY environment variable
    comment_body = os.getenv("COMMENT_BODY")
    if not comment_body:
        raise ValueError("COMMENT_BODY environment variable is missing")

    # Parse the parameters
    parsed_params = parse_comment(comment_body)
    emu_users_file = parsed_params["EMU_USERS_FILE"]
    user_mappings_file = parsed_params["USER_MAPPINGS_FILE"]
    org_name = parsed_params["ORG_NAME"]

    if not (emu_users_file and user_mappings_file and org_name):
        raise ValueError("Missing required parameters in the comment")

    print(f"EMU_USERS_FILE: {emu_users_file}")
    print(f"USER_MAPPINGS_FILE: {user_mappings_file}")
    print(f"ORG_NAME: {org_name}")

    # Read Excel file
    emu_users_df = read_excel_file(emu_users_file)
    required_columns = {'login', 'name', 'saml_name_id'}
    if not required_columns.issubset(emu_users_df.columns):
        raise ValueError(f"Excel file must contain the following columns: {required_columns}")

    # Extract base organization name (e.g., 'mgmri' from 'mgmri-dge')
    org_suffix = org_name.split('-')[0]

    # Process mappings
    process_user_mappings(user_mappings_file, emu_users_df, org_suffix)

if __name__ == "__main__":
    main()
