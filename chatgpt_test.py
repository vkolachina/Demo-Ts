import pandas as pd
import csv
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ORG_NAME = os.getenv("ORG_NAME")
EMU_USERS_FILE = os.getenv("EMU_USERS_FILE")
USER_MAPPINGS_FILE = os.getenv("USER_MAPPINGS_FILE")

# Function to read the input files
def read_input_files():
    print("Reading input files...")
    # Load the EMU users Excel file
    emu_users_df = pd.read_excel(EMU_USERS_FILE)

    # Verify required columns are present in the EMU Excel sheet
    required_columns = {'login', 'name', 'saml_name_id'}
    if not required_columns.issubset(emu_users_df.columns):
        raise ValueError(f"Excel file must contain the following columns: {required_columns}")

    print("Reading the Excel file")
    return emu_users_df

# Function to process the user mappings from the CSV file
def process_user_mappings(user_mappings_file, emu_users_df, org_name):
    print("Processing user mappings")

    # Read the CSV file with user mappings
    mappings = []
    with open(user_mappings_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            mappings.append(row)

    # Iterate through each mapping and match the mannequin-user
    for mapping in mappings:
        mannequin_user = mapping.get("mannequin-user")
        if not mannequin_user:
            print(f"Skipping row due to missing 'mannequin-user': {mapping}")
            continue

        # Find the matching user from the EMU data (matching login or name)
        matched_user = emu_users_df[(emu_users_df['login'] == mannequin_user) | 
                                     (emu_users_df['name'] == mannequin_user)]
        
        if not matched_user.empty:
            # Assuming the email-like identifier is in 'saml_name_id'
            email = matched_user.iloc[0]["saml_name_id"]  # Extract email-like value from saml_name_id

            # Extract the empirical part of the email before the "@" symbol (if present)
            empirical = email.split('@')[0] if '@' in email else email
            
            # Correct the target-user format by appending the suffix "_mgmri"
            target_user = f"{empirical}_{org_name}"

            # Update target-user in the CSV mapping
            mapping["target-user"] = target_user
            print(f"Updated target-user for {mannequin_user}: {target_user}")
        else:
            print(f"No match found for mannequin-user: {mannequin_user}")

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
    # Read the input files and load data
    emu_users_df = read_input_files()

    # Process the user mappings and update target-user
    process_user_mappings(USER_MAPPINGS_FILE, emu_users_df, ORG_NAME)

if __name__ == "__main__":
    main()
