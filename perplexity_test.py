import csv
import requests
import openpyxl

# Environment variables (replace with actual values)
GITHUB_TOKEN = "your_github_token"
ORG_NAME = "mgmrri"
GHEC_EXCEL = "path_to_ghec_excel_file.xlsx"
CSV_FILE = "user-mappings-template.csv"

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

def read_ghec_excel(file_path):
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active
    ghec_users = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        ghec_users.append({"login": row[0], "name": row[1]})
    return ghec_users

def process_mannequins(csv_file, ghec_users):
    emu_members = fetch_org_members(ORG_NAME, GITHUB_TOKEN)
    updated_rows = []

    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            mannequin_user = row['mannequin_user']
            mannequin_id = row['mannequin_id']
            
            # Check if mannequin_user matches in GHEC users list
            ghec_match = next((user for user in ghec_users if user['login'] == mannequin_user or user['name'] == mannequin_user), None)
            
            if ghec_match:
                # Fetch email for the mannequin user
                email = fetch_user_email(mannequin_user, GITHUB_TOKEN)
                
                if email:
                    # Check if email matches any EMU member
                    emu_match = next((member for member in emu_members if fetch_user_email(member['login'], GITHUB_TOKEN) == email), None)
                    
                    if emu_match:
                        row['target_user'] = emu_match['login']
                    else:
                        print(f"No EMU match found for {mannequin_user}")
                else:
                    print(f"No email found for {mannequin_user}")
            else:
                print(f"No GHEC match found for {mannequin_user}")
            
            updated_rows.append(row)

    # Write updated data back to CSV
    with open(csv_file, 'w', newline='') as file:
        fieldnames = ['mannequin_user', 'mannequin_id', 'target_user']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

def main():
    ghec_users = read_ghec_excel(GHEC_EXCEL)
    process_mannequins(CSV_FILE, ghec_users)
    print(f"Organization name: {ORG_NAME}")
    print("CSV file updated with target users.")

if __name__ == "__main__":
    main()
