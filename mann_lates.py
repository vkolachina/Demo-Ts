import pandas as pd
import os
import csv
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Function to read the Excel file
def read_excel_file(file_name):
    print(f"Reading the Excel file: {file_name}")
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"Excel file {file_name} not found")
    return pd.read_excel(file_name)

# Function to read the CSV file
def read_csv_file(file_name):
    print(f"Reading the CSV file: {file_name}")
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"CSV file {file_name} not found")
    with open(file_name, mode='r', newline='', encoding='utf-8') as file:
        return list(csv.DictReader(file))

# Function to update the CSV file
def update_csv_file(file_name, mappings):
    print(f"Writing updates back to the CSV file: {file_name}")
    with open(file_name, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ["mannequin-user", "mannequin-id", "target-user"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mappings)
    print("CSV file updated successfully")

# Function to process user mappings
def process_user_mappings(user_mappings_file, emu_users_df, org_name):
    print("Processing user mappings...")
    
    mappings = read_csv_file(user_mappings_file)
    org_suffix = org_name.split('-')[0]  # Extract base organization name (e.g., 'mgmri')

    for mapping in mappings:
        mannequin_user = mapping.get("mannequin-user")
        if not mannequin_user:
            print(f"Skipping row due to missing 'mannequin-user': {mapping}")
            continue

        # Find the user in the Excel sheet (matching mannequin-user with login or name)
        matched_user = emu_users_df[emu_users_df['login'] == mannequin_user]
        if matched_user.empty:
            print(f"No match found for mannequin-user: {mannequin_user}")
            continue

        # Assuming email-like data is in the 'saml_name_id' field
        email = matched_user.iloc[0]["saml_name_id"]

        # Extract the empirical part before the '@' and append '_org_suffix'
        empirical_part = email.split('@')[0]
        target_user = f"{empirical_part}_{org_suffix}"

        # Update the target-user column in the mapping
        mapping["target-user"] = target_user
        print(f"Updated target-user for {mannequin_user} to {target_user}")

    # Update the CSV file with the new target-user values
    update_csv_file(user_mappings_file, mappings)

# Main function to execute the process
def main():
    print("Executing migration script...")

    # Get parameters from environment variables
    emu_users_file = os.getenv("EMU_USERS_FILE")
    user_mappings_file = os.getenv("USER_MAPPINGS_FILE")
    org_name = os.getenv("ORG_NAME")

    if not emu_users_file or not user_mappings_file or not org_name:
        raise ValueError("Missing required parameters. Ensure all parameters are provided.")

    # Read the EMU users Excel file
    emu_users_df = read_excel_file(emu_users_file)

    # Check if the required columns are present in the Excel file
    required_columns = {'login', 'name', 'saml_name_id'}
    if not required_columns.issubset(emu_users_df.columns):
        raise ValueError(f"Excel file must contain the following columns: {required_columns}")

    # Process user mappings and update the CSV file
    process_user_mappings(user_mappings_file, emu_users_df, org_name)

if __name__ == "__main__":
    main()
