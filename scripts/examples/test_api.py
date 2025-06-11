import requests

# Base URL for our server
BASE_URL = "http://localhost:5001/api"


def test_search_contacts():
    """Test searching for contacts with first name 'scott'"""
    params = {"first_name": "scott", "first_name_match": "exact"}

    print("Searching for contacts with first name 'scott'...")
    response = requests.get(f"{BASE_URL}/contacts", params=params)

    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data['status']}")
        print(f"Found {data['contact_count']} contacts")

        # Print the first few contacts
        for i, contact in enumerate(data["contacts"][:5]):
            print(f"\nContact {i + 1}:")
            print(f"  ID: {contact['id']}")
            print(
                f"  Name: {contact.get('given_name', '')} {contact.get('family_name', '')}"
            )

            # Print emails if available
            emails = contact.get("email_addresses", [])
            if emails:
                print(f"  Email: {emails[0].get('email', 'N/A')}")

            # Print creation date if available
            if "create_time" in contact:
                print(f"  Created: {contact['create_time']}")

        # If there are more contacts, just note that
        if data["contact_count"] > 5:
            print(f"\n... and {data['contact_count'] - 5} more contacts")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    test_search_contacts()
