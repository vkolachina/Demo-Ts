import requests
import pandas as pd
import os
from dotenv import load_dotenv
import csv

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
EMU_USERS_FILE = os.getenv("EMU_USERS_FILE")
USER_MAPPINGS_FILE = os.getenv("USER_MAPPINGS_FILE")
ORG_NAME = os.getenv("ORG_NAME")

# Function to find a user in the EMU users list based on GitHub handle
def find_user_in_emu(github_handle, emu_users_df):
    # Try to match mannequin-user with 'login' or 'name' columns in the EMU users DataFrame
    return emu_users_df[emu_users_df['login'] == github_handle].iloc[0] if not emu_users_df[emu_users_df['login'] == github_handle].empty else None

# Function to process the user mappings from the CSV file
def process_user_mappings(mappings, emu_users_df, org_name):
    print("Processing user mappings...")
    
    # Iterate through each mapping and check for matches
    for mapping in mappings:
        mannequin_user = mapping.get("mannequin-user")  # Get the mannequin-user from the CSV
        if not mannequin_user:
            print(f"Skipping row due to missing 'mannequin-user': {mapping}")
            continue

        # Find the matching EMU user
        matched_emu_user = find_user_in_emu(mannequin_user, emu_users_df)
        
        if matched_emu_user is not None:
            # Extract email from matched user
            emu_email = matched_emu_user.get("email")
            if emu_email:
                # Extract the empirical (before '@') part from the email and add the suffix 'mgmri'
                empirical_part = emu_email.split('@')[0]
                target_user = f"{empirical_part}_{org_name}"
                
                # Update the target-user field in the CSV mapping
                mapping["target-user"] = target_user
                print(f"Updated target-user for {mannequin_user}: {target_user}")
            else:
                print(f"No email found for EMU user: {mannequin_user}")
        else:
            print(f"No match found in EMU for mannequin-user: {mannequin_user}")

# Main function to execute the process
def main():
    print("Reading input files...")

    # Load the Excel file into a DataFrame
    print("Reading the Excel file")
    emu_users_df = pd.read_excel(EMU_USERS_FILE)

    # Validate required columns in the Excel file
    required_columns = {"login", "name", "email"}
    if not required_columns.issubset(emu_users_df.columns):
        raise ValueError(f"Excel file must contain the following columns: {required_columns}")

    # Load the CSV file into a list of dictionaries
    print("Reading the CSV file")
    mappings = []
    with open(USER_MAPPINGS_FILE, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            mappings.append(row)

    # Process the mappings
    process_user_mappings(mappings, emu_users_df, ORG_NAME)

    # Write the updated mappings back to the CSV
    print("Writing updates back to the CSV file")
    with open(USER_MAPPINGS_FILE, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ["mannequin-user", "mannequin-id", "target-user"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mappings)

    print("Process completed successfully!")

if __name__ == "__main__":
    main()
