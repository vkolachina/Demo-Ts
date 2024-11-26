import pandas as pd
import os
from dotenv import load_dotenv
import csv

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
EMU_USERS_FILE = os.getenv("EMU_USERS_FILE")
USER_MAPPINGS_FILE = os.getenv("USER_MAPPINGS_FILE")
ORG_SUFFIX = "mgmri"  # The suffix for the organization

# Function to process user mappings
def process_user_mappings(user_mappings_file, emu_users_df, org_suffix):
    print("Reading user mappings template")

    # Read the CSV file with user mappings
    mappings = []
    with open(user_mappings_file, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            mappings.append(row)

    print("Processing user mappings")
    
    # Iterate through each mapping
    for mapping in mappings:
        mannequin_user = mapping.get("mannequin-user")
        if not mannequin_user:
            print(f"Skipping row due to missing 'mannequin-user': {mapping}")
            continue

        # Match the mannequin-user with EMU users' email
        matched_user = emu_users_df[emu_users_df["login"] == mannequin_user]
        if not matched_user.empty:
            email = matched_user.iloc[0]["email"]  # Assuming 'email' column exists
            empirical_part = email.split("@")[0]  # Extract empirical from email
            target_user = f"{empirical_part}@{org_suffix}"  # Append suffix to form target-user
            mapping["target-user"] = target_user
            print(f"Updated target-user for {mannequin_user}: {target_user}")
        else:
            print(f"No match found in EMU for {mannequin_user}")
            mapping["target-user"] = None

    # Write the updated mappings back to the CSV file
    print("Writing updates back to the user mappings file")
    with open(user_mappings_file, mode="w", newline="", encoding="utf-8") as file:
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

    # Process the user mappings
    process_user_mappings(USER_MAPPINGS_FILE, emu_users_df, ORG_SUFFIX)

if __name__ == "__main__":
    main()
