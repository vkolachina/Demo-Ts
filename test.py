import os
import requests
from github import Github


GITHUB_TOKEN = ""
ORG_NAME = ""

# Initialize the GitHub API client
g = Github(GITHUB_TOKEN)


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

def main():
    members = fetch_org_members(ORG_NAME, GITHUB_TOKEN)
    for member in members:
        username = member["login"]
        email = fetch_user_email(username, GITHUB_TOKEN)
        if email:
            print(f"Username: {username}, Email: {email}")
        else:
            print(f"Username: {username}, Email: Not Public")

if __name__ == "__main__":
    main()
