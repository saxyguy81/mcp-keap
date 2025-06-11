#!/usr/bin/env python
"""
Check the Keap API directly to search for recent contacts
"""

import requests
import configparser
from pathlib import Path
from tabulate import tabulate

def get_api_key():
    """Get the API key from the keapsync config"""
    config_path = Path('/Users/smhanan/CascadeProjects/keapsync/config/config.ini')
    if not config_path.exists():
        print(f"Config file not found at {config_path}")
        return None
        
    config = configparser.ConfigParser()
    config.read(config_path)
    
    if 'keap' not in config or 'api_key' not in config['keap']:
        print("API key not found in config")
        return None
        
    return config['keap']['api_key']

def search_contacts():
    """Search for contacts using the Keap API directly"""
    api_key = get_api_key()
    if not api_key:
        print("Cannot proceed without API key")
        return
        
    print(f"Using API key: {api_key[:10]}...")
    
    # Keap API endpoint
    base_url = "https://api.infusionsoft.com/crm/rest/v2"
    endpoint = "/contacts"
    url = f"{base_url}{endpoint}"
    
    # Set up request headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    print("Searching for all contacts with first name 'scott'")
    
    # Query parameters - search for first name
    params = {
        "order": "id",
        "fields": "id,given_name,family_name,email_addresses,create_time,update_time",
        "optional_properties": "tag_ids",
        "given_name": "scott",  # Search by first name
        "page_size": 100
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        contacts = data.get('contacts', [])
        
        print(f"Found {len(contacts)} contacts with first name 'scott'")
        
        # Sort by update time (newest first)
        contacts.sort(key=lambda x: x.get('update_time', ''), reverse=True)
        
        # Create table for first 10 contacts
        display_contacts = contacts[:10]
        
        if display_contacts:
            # Create table data
            table_data = []
            for contact in display_contacts:
                # Extract first email if available
                email = ""
                if contact.get("email_addresses") and len(contact["email_addresses"]) > 0:
                    email = contact["email_addresses"][0].get("email", "")
                    
                table_data.append([
                    contact.get("id"),
                    f"{contact.get('given_name', '')} {contact.get('family_name', '')}".strip(),
                    email,
                    contact.get("create_time"),
                    contact.get("update_time")
                ])
            
            # Print table
            print(tabulate(
                table_data,
                headers=["ID", "Name", "Email", "Created Date", "Updated Date"],
                tablefmt="pretty"
            ))
            
        # Check for Scott in names or smhanan in email
        scott_contacts = []
        for contact in contacts:
            first_name = contact.get('given_name', '').lower() if contact.get('given_name') else ''
            last_name = contact.get('family_name', '').lower() if contact.get('family_name') else ''
            full_name = f"{first_name} {last_name}".strip()
            
            # Check emails for smhanan
            emails = contact.get('email_addresses', [])
            email_match = False
            for email_obj in emails:
                email = email_obj.get('email', '').lower()
                if 'smhanan' in email:
                    email_match = True
                    break
            
            if 'scott' in full_name or email_match:
                scott_contacts.append(contact)
                
        print(f"\nFound {len(scott_contacts)} contacts with 'Scott' in name or 'smhanan' in email")
        
        if scott_contacts:
            # Create table data
            table_data = []
            for contact in scott_contacts:
                # Extract first email if available
                email = ""
                if contact.get("email_addresses") and len(contact["email_addresses"]) > 0:
                    email = contact["email_addresses"][0].get("email", "")
                    
                table_data.append([
                    contact.get("id"),
                    f"{contact.get('given_name', '')} {contact.get('family_name', '')}".strip(),
                    email,
                    contact.get("create_time"),
                    contact.get("update_time")
                ])
            
            # Print table
            print(tabulate(
                table_data,
                headers=["ID", "Name", "Email", "Created Date", "Updated Date"],
                tablefmt="pretty"
            ))
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    search_contacts()
