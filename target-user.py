import csv
import os
import requests

# Code A: Fetch GitHub organization members
def fetch_org_members(org_name, token):
    url = f"https://api.github.com/orgs/{org_name}/members"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()  # Return the list of members
    else:
        print(f"Error fetching members: {response.status_code}")
        print(response.json())
        return []

# Code B: Fetch email by GitHub username
def fetch_user_email(username, token):
    url = f"https://api.github.com/users/{username}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        return user_data.get("email")  # Return email
    else:
        print(f"Error fetching email for {username}: {response.status_code}")
        print(response.json())
        return None

# Process the CSV file to update target-user
def process_csv_and_update(csv_file, org_name, token):
    # Step 1: Fetch organization members
    print(f"Fetching members of the organization: {org_name}")
    members = fetch_org_members(org_name, token)

    # Step 2: Create a mapping of usernames to emails
    print("Fetching emails for organization members...")
    username_to_email = {}
    for member in members:
        username = member['login']
        email = fetch_user_email(username, token)
        if email:
            username_to_email[username] = email  # Map username to email

    # Step 3: Process the CSV file
    print(f"Processing the CSV file: {csv_file}")
    updated_rows = []
    with open(csv_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            mannequin_user = row['mannequin-user']  # GitHub handle
            mannequin_id = row['mannequin-id']
            target_user = row.get('target-user', '')  # Default to empty if not present

            # Match the mannequin-user with the username in the organization
            if mannequin_user in username_to_email:
                target_user = mannequin_user  # If match is found, use the same username
                print(f"Match found: {mannequin_user} -> {target_user}")
            else:
                print(f"No match found for: {mannequin_user}")

            # Update the row with the target-user
            row['target-user'] = target_user
            updated_rows.append(row)

    # Step 4: Write the updated data back to the CSV file
    print(f"Updating the CSV file: {csv_file}")
    with open(csv_file, 'w', newline='', encoding='utf-8') as outfile:
        fieldnames = ['mannequin-user', 'mannequin-id', 'target-user']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

    print(f"CSV update completed. File saved as '{csv_file}'.")

# Example usage
def main():
    # Define environment variables or replace with hardcoded values
    org_name = os.getenv("ORG_NAME", "mgmrri")  # Replace with your organization name
    token = os.getenv("GITHUB_TOKEN", "your_github_token_here")  # Replace with your GitHub token
    csv_file = "user-mappings-template.csv"  # Fixed file name as per the requirement

    # Validate environment variables
    if not org_name or not token:
        print("Please set the environment variables ORG_NAME and GITHUB_TOKEN.")
        return

    # Run the process
    process_csv_and_update(csv_file, org_name, token)

if __name__ == "__main__":
    main()
