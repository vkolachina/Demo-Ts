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
