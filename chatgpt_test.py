import pandas as pd
import csv

# Constants
CSV_FILE = "user-mappings-template.csv"  # Input CSV file
EXCEL_FILE = "emu_users.xlsx"  # Input Excel file
ORG_SUFFIX = "mgmri"  # Organization suffix to append

def process_user_mappings(csv_file, excel_file, org_suffix):
    """
    Process the CSV and Excel files to update the 'target-user' column in the CSV file.

    Args:
        csv_file (str): Path to the user-mappings-template.csv file.
        excel_file (str): Path to the Excel file with user data.
        org_suffix (str): Organization suffix to append to the empirical part of the email.
    """
    print("Reading input files...")

    # Load CSV file
    with open(csv_file, mode="r", encoding="utf-8") as file:
        mappings = list(csv.DictReader(file))

    # Load Excel file into a DataFrame
    emu_users_df = pd.read_excel(excel_file)

    print(f"Columns in Excel file: {emu_users_df.columns.tolist()}")

    # Ensure necessary columns are present in the Excel file
    required_columns = {"login", "name", "email"}
    if not required_columns.issubset(emu_users_df.columns):
        raise ValueError(
            f"Excel file must contain the following columns: {required_columns}"
        )

    print("Processing user mappings...")

    # Update each row in the CSV mappings
    for mapping in mappings:
        mannequin_user = mapping.get("mannequin-user")
        if not mannequin_user:
            print(f"Skipping row due to missing 'mannequin-user': {mapping}")
            continue

        # Find matching row(s) in the Excel file based on 'login' or 'name'
        matched_user = emu_users_df[
            (emu_users_df["login"] == mannequin_user)
            | (emu_users_df["name"] == mannequin_user)
        ]

        if not matched_user.empty:
            # Retrieve the email of the first matched user
            email = matched_user.iloc[0]["email"]

            # Extract the empirical part of the email and append the organization suffix
            empirical = email.split("@")[0]
            target_user = f"{empirical}_{org_suffix}"

            # Update the 'target-user' field
            mapping["target-user"] = target_user
            print(f"Updated target-user for {mannequin_user}: {target_user}")
        else:
            # No match found in the Excel file
            print(f"No match found in Excel file for {mannequin_user}")
            mapping["target-user"] = None

    # Write the updated data back to the CSV file
    print("Writing updated data to CSV file...")
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        fieldnames = ["mannequin-user", "mannequin-id", "target-user"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mappings)

    print("Processing completed successfully.")

def main():
    """
    Main function to execute the script.
    """
    try:
        process_user_mappings(CSV_FILE, EXCEL_FILE, ORG_SUFFIX)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
