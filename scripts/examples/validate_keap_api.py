"""
Keap API Validation Script

This script validates that the Keap API is working as expected and
returns data in the expected format. It also helps identify any
API quirks or limitations that need to be accounted for.
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path to import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.api.client import KeapClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

async def validate_contacts_endpoint():
    """Validate the /contacts endpoint"""
    logger.info("Validating contacts endpoint...")
    
    client = KeapClient()
    
    try:
        # Basic query with minimal parameters
        logger.info("Testing basic contacts query...")
        params = {"page_size": 10}
        contacts = await client.query_contacts(params)
        
        logger.info(f"Retrieved {len(contacts)} contacts")
        
        if contacts:
            # Check the structure of a sample contact
            sample_contact = contacts[0]
            logger.info(f"Sample contact structure: {json.dumps(sample_contact, indent=2)}")
            
            # Validate required fields
            required_fields = ["id", "given_name", "family_name", "email_addresses"]
            missing_fields = [field for field in required_fields if field not in sample_contact]
            
            if missing_fields:
                logger.warning(f"Missing required fields in contact response: {missing_fields}")
            else:
                logger.info("All required fields present in contact response")
            
            # Check email address structure
            if "email_addresses" in sample_contact:
                email_addresses = sample_contact["email_addresses"]
                logger.info(f"Email addresses structure: {json.dumps(email_addresses, indent=2)}")
        
        # Test pagination
        logger.info("Testing pagination...")
        all_contacts = []
        
        for page in range(3):
            params = {"page": page, "page_size": 10}
            page_contacts = await client.query_contacts(params)
            
            if not page_contacts:
                break
                
            all_contacts.extend(page_contacts)
            logger.info(f"Retrieved page {page} with {len(page_contacts)} contacts")
        
        logger.info(f"Retrieved {len(all_contacts)} contacts across all pages")
        
        # Test with date filters
        logger.info("Testing date filters...")
        today = datetime.now().isoformat() + "Z" # Add Z to indicate UTC
        
        params = {
            "page_size": 10,
            "since": "2023-01-01T00:00:00Z", # Added Z to fix the date format
            "until": today
        }
        
        date_filtered_contacts = await client.query_contacts(params)
        logger.info(f"Retrieved {len(date_filtered_contacts)} contacts with date filters")
        
        # Test with optional fields
        logger.info("Testing optional fields...")
        params = {
            "page_size": 10,
            "optional_properties": "tag_ids,custom_fields"
        }
        
        optional_contacts = await client.query_contacts(params)
        
        if optional_contacts:
            # Check for tag_ids and custom_fields
            sample_contact = optional_contacts[0]
            has_tag_ids = "tag_ids" in sample_contact
            has_custom_fields = "custom_fields" in sample_contact
            
            logger.info(f"Has tag_ids: {has_tag_ids}, Has custom_fields: {has_custom_fields}")
            
            if has_tag_ids:
                logger.info(f"Tag IDs structure: {json.dumps(sample_contact['tag_ids'], indent=2)}")
                
            if has_custom_fields:
                logger.info(f"Custom fields structure: {json.dumps(sample_contact['custom_fields'], indent=2)}")
        
    except Exception as e:
        logger.error(f"Error validating contacts endpoint: {e}")
    finally:
        await client.close()

async def validate_tags_endpoint():
    """Validate the /tags endpoint"""
    logger.info("Validating tags endpoint...")
    
    client = KeapClient()
    
    try:
        # Get all tags
        logger.info("Testing get all tags...")
        all_tags = await client.get_all_tags(use_cache=False)
        
        logger.info(f"Retrieved {len(all_tags)} tags")
        
        if all_tags:
            # Check the structure of a sample tag
            sample_tag = all_tags[0]
            logger.info(f"Sample tag structure: {json.dumps(sample_tag, indent=2)}")
            
            # Validate required fields
            required_fields = ["id", "name"]
            missing_fields = [field for field in required_fields if field not in sample_tag]
            
            if missing_fields:
                logger.warning(f"Missing required fields in tag response: {missing_fields}")
            else:
                logger.info("All required fields present in tag response")
            
            # Check if we have at least one tag to use for further testing
            tag_id = str(sample_tag["id"])
            
            # Get a single tag by ID
            logger.info(f"Testing get tag by ID {tag_id}...")
            tag = await client.get_tag(tag_id)
            
            logger.info(f"Retrieved tag: {json.dumps(tag, indent=2)}")
            
            # Get contacts with this tag
            logger.info(f"Testing get contacts by tag ID {tag_id}...")
            tagged_contacts = await client.get_contacts_by_tag_id(tag_id)
            
            logger.info(f"Retrieved {len(tagged_contacts)} contacts with tag ID {tag_id}")
            
            if tagged_contacts:
                # Check the structure of a sample tagged contact
                sample_contact = tagged_contacts[0]
                logger.info(f"Sample tagged contact structure: {json.dumps(sample_contact, indent=2)}")
    
    except Exception as e:
        logger.error(f"Error validating tags endpoint: {e}")
    finally:
        await client.close()

async def validate_tag_application():
    """Validate tag application and removal"""
    logger.info("Validating tag application and removal...")
    
    client = KeapClient()
    
    try:
        # Get a test tag for validation
        all_tags = await client.get_all_tags(use_cache=False)
        
        if not all_tags:
            logger.error("No tags found for testing")
            return
            
        test_tag = all_tags[0]
        tag_id = str(test_tag["id"])
        
        logger.info(f"Using tag {test_tag['name']} (ID: {tag_id}) for testing")
        
        # Get some test contacts
        params = {"page_size": 2}
        test_contacts = await client.query_contacts(params)
        
        if not test_contacts:
            logger.error("No contacts found for testing")
            return
            
        contact_ids = [str(contact["id"]) for contact in test_contacts]
        logger.info(f"Using contacts with IDs: {contact_ids}")
        
        # Apply tag to contacts
        logger.info(f"Applying tag {tag_id} to contacts {contact_ids}...")
        apply_result = await client.apply_tag_to_contacts(tag_id, contact_ids)
        
        logger.info(f"Apply tag result: {json.dumps(apply_result, indent=2)}")
        
        # Wait a moment to ensure tag is applied
        logger.info("Waiting for tag application to process...")
        await asyncio.sleep(5)
        
        # Verify tag was applied by checking contacts
        tagged_contacts = await client.get_contacts_by_tag_id(tag_id)
        tagged_contact_ids = [str(contact["id"]) for contact in tagged_contacts]
        
        for contact_id in contact_ids:
            if contact_id in tagged_contact_ids:
                logger.info(f"Verified tag was applied to contact {contact_id}")
            else:
                logger.warning(f"Failed to verify tag application for contact {contact_id}")
        
        # Remove tag from contacts
        logger.info(f"Removing tag {tag_id} from contacts {contact_ids}...")
        remove_result = await client.remove_tag_from_contacts(tag_id, contact_ids)
        
        logger.info(f"Remove tag result: {json.dumps(remove_result, indent=2)}")
        
        # Wait a moment to ensure tag is removed
        logger.info("Waiting for tag removal to process...")
        await asyncio.sleep(5)
        
        # Verify tag was removed
        tagged_contacts = await client.get_contacts_by_tag_id(tag_id)
        tagged_contact_ids = [str(contact["id"]) for contact in tagged_contacts]
        
        for contact_id in contact_ids:
            if contact_id not in tagged_contact_ids:
                logger.info(f"Verified tag was removed from contact {contact_id}")
            else:
                logger.warning(f"Failed to verify tag removal for contact {contact_id}")
    
    except Exception as e:
        logger.error(f"Error validating tag application: {e}")
    finally:
        await client.close()

async def validate_custom_fields():
    """Validate custom fields data structure"""
    logger.info("Validating custom fields...")
    
    client = KeapClient()
    
    try:
        # Get contacts with custom fields
        params = {
            "page_size": 10,
            "optional_properties": "custom_fields"
        }
        
        contacts = await client.query_contacts(params)
        
        if not contacts:
            logger.error("No contacts found for testing")
            return
        
        # Find contacts with custom fields
        contacts_with_custom_fields = [c for c in contacts if "custom_fields" in c and c["custom_fields"]]
        
        if not contacts_with_custom_fields:
            logger.warning("No contacts with custom fields found")
            return
        
        logger.info(f"Found {len(contacts_with_custom_fields)} contacts with custom fields")
        
        # Check the structure of custom fields
        for i, contact in enumerate(contacts_with_custom_fields[:3]):  # Limit to 3 contacts
            logger.info(f"Contact {i+1} custom fields:")
            custom_fields = contact["custom_fields"]
            
            # Determine the structure of custom fields (array or object)
            if isinstance(custom_fields, list):
                logger.info("Custom fields are returned as an array")
                
                for cf in custom_fields:
                    logger.info(f"  Field ID: {cf.get('id')}, Name: {cf.get('name')}, Value: {cf.get('content')}")
            
            elif isinstance(custom_fields, dict):
                logger.info("Custom fields are returned as an object")
                
                for field_id, field_data in custom_fields.items():
                    logger.info(f"  Field ID: {field_id}, Name: {field_data.get('name')}, Value: {field_data.get('content')}")
            
            else:
                logger.warning(f"Unexpected custom fields format: {type(custom_fields)}")
    
    except Exception as e:
        logger.error(f"Error validating custom fields: {e}")
    finally:
        await client.close()

async def validate_rate_limits():
    """Validate API rate limits by making rapid requests"""
    logger.info("Validating API rate limits...")
    
    client = KeapClient()
    
    try:
        # Make multiple rapid requests to test rate limiting
        logger.info("Making 10 rapid requests to test rate limiting...")
        
        for i in range(10):
            params = {"page_size": 1}
            start_time = datetime.now()
            
            try:
                contacts = await client.query_contacts(params)
                elapsed = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"Request {i+1}: Got {len(contacts)} contacts in {elapsed:.2f}s")
            except Exception as e:
                logger.error(f"Request {i+1} failed: {e}")
        
        # Check the rate limit information
        logger.info(f"Rate limit remaining: {client.rate_limit_remaining}")
        logger.info(f"Rate limit resets at: {datetime.fromtimestamp(client.rate_limit_reset)}")
    
    except Exception as e:
        logger.error(f"Error validating rate limits: {e}")
    finally:
        await client.close()

async def validate_contact_operations():
    """Validate operations on individual contacts"""
    logger.info("Validating contact operations...")
    
    client = KeapClient()
    
    try:
        # Get a test contact to work with
        params = {"page_size": 1}
        contacts = await client.query_contacts(params)
        
        if not contacts:
            logger.error("No contacts found for testing")
            return
            
        contact_id = str(contacts[0]["id"])
        logger.info(f"Testing operations on contact ID: {contact_id}")
        
        # Test get_contact endpoint
        logger.info(f"Testing get_contact for ID: {contact_id}")
        contact_details = await client.get_contact(contact_id)
        
        logger.info(f"Retrieved contact details: {json.dumps(contact_details, indent=2)}")
        
        # Verify that the returned contact has the correct ID
        if contact_details.get("id") == contact_id:
            logger.info("Successfully verified contact ID in response")
        else:
            logger.warning(f"Contact ID mismatch: Expected {contact_id}, got {contact_details.get('id')}")
        
        # Check for additional fields that may be present when fetching a single contact
        # versus listing contacts
        single_contact_fields = set(contact_details.keys())
        list_contact_fields = set(contacts[0].keys())
        
        additional_fields = single_contact_fields - list_contact_fields
        if additional_fields:
            logger.info(f"Additional fields in single contact fetch: {additional_fields}")
        
        # Test retrieving with query parameters for specific fields
        logger.info("Testing get_contact with specific fields...")
        
        # For this test, we'd need to implement a get_contact method that accepts query parameters
        # This is a placeholder for that functionality
        
    except Exception as e:
        logger.error(f"Error validating contact operations: {e}")
    finally:
        await client.close()

async def validate_error_handling():
    """Validate API error responses and client error handling"""
    logger.info("Validating error handling...")
    
    client = KeapClient()
    
    try:
        # Test with invalid contact ID
        invalid_id = "999999999"
        logger.info(f"Testing get_contact with invalid ID: {invalid_id}")
        
        try:
            contact = await client.get_contact(invalid_id)
            logger.warning(f"Expected error for invalid contact ID, but got result: {contact}")
        except Exception as e:
            logger.info(f"Correctly caught error for invalid contact ID: {e}")
        
        # Test with invalid query parameters
        logger.info("Testing query_contacts with invalid parameters...")
        
        try:
            params = {"invalid_param": "value"}
            await client.query_contacts(params)
            logger.warning("Expected error for invalid parameters, but request succeeded")
        except Exception as e:
            logger.info(f"Correctly caught error for invalid parameters: {e}")
        
        # Test with malformed date format
        logger.info("Testing with malformed date format...")
        
        try:
            params = {
                "since": "not-a-date",
                "page_size": 10
            }
            await client.query_contacts(params)
            logger.warning("Expected error for invalid date format, but request succeeded")
        except Exception as e:
            logger.info(f"Correctly caught error for invalid date format: {e}")
            
    except Exception as e:
        logger.error(f"Error in error handling validation: {e}")
    finally:
        await client.close()

async def validate_pagination_limits():
    """Validate pagination limits and handling of large result sets"""
    logger.info("Validating pagination limits...")
    
    client = KeapClient()
    
    try:
        # Test with different page sizes
        page_sizes = [1, 10, 50, 100, 200, 250]
        
        for size in page_sizes:
            logger.info(f"Testing page_size={size}...")
            params = {"page_size": size}
            
            try:
                start_time = datetime.now()
                contacts = await client.query_contacts(params)
                elapsed = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"Retrieved {len(contacts)} contacts with page_size={size} in {elapsed:.2f}s")
                
                # Check if we got the expected number of results (may be less if not enough records)
                if len(contacts) == size:
                    logger.info(f"Got expected number of contacts ({size})")
                elif len(contacts) < size:
                    logger.info(f"Got fewer contacts ({len(contacts)}) than requested ({size})")
                else:
                    logger.warning(f"Got more contacts ({len(contacts)}) than requested ({size})")
                
            except Exception as e:
                logger.error(f"Error with page_size={size}: {e}")
        
        # Test retrieving a large number of contacts through multiple pages
        logger.info("Testing retrieval of a large result set...")
        
        params = {"page_size": 100}
        max_contacts = 300  # Adjust based on your needs
        
        start_time = datetime.now()
        all_contacts = []
        page = 0
        
        while len(all_contacts) < max_contacts:
            page_params = params.copy()
            page_params["page"] = page
            
            contacts = await client.query_contacts(page_params)
            
            if not contacts:
                break
                
            all_contacts.extend(contacts)
            logger.info(f"Retrieved page {page} with {len(contacts)} contacts, total: {len(all_contacts)}")
            
            page += 1
            
            # Add a small delay to avoid rate limiting
            await asyncio.sleep(1)
            
            # Stop if we've reached the desired number or hit the end of results
            if len(contacts) < params["page_size"]:
                break
                
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Retrieved a total of {len(all_contacts)} contacts in {elapsed:.2f}s")
        
    except Exception as e:
        logger.error(f"Error validating pagination limits: {e}")
    finally:
        await client.close()

async def validate_search_capabilities():
    """Validate search functionality in the API"""
    logger.info("Validating search capabilities...")
    
    client = KeapClient()
    
    try:
        # Test search by email domain
        logger.info("Testing search by email domain...")
        domains = ["gmail.com", "yahoo.com", "hotmail.com"]
        
        for domain in domains:
            params = {
                "page_size": 10,
                "email": f"*@{domain}"
            }
            
            try:
                contacts = await client.query_contacts(params)
                logger.info(f"Found {len(contacts)} contacts with email domain {domain}")
                
                if contacts:
                    # Verify the search worked correctly
                    sample_contact = contacts[0]
                    
                    if "email_addresses" in sample_contact:
                        email_addresses = sample_contact["email_addresses"]
                        if isinstance(email_addresses, list) and email_addresses:
                            email = email_addresses[0].get("email", "")
                            if domain in email:
                                logger.info(f"Verified email domain search worked: {email}")
                            else:
                                logger.warning(f"Email domain search may not work correctly: {email}")
            
            except Exception as e:
                logger.error(f"Error searching by email domain {domain}: {e}")
        
        # Test search by name
        logger.info("Testing search by name...")
        names = ["John", "Smith", "Mary"]
        
        for name in names:
            params = {
                "page_size": 10,
                "given_name": name
            }
            
            try:
                contacts = await client.query_contacts(params)
                logger.info(f"Found {len(contacts)} contacts with name '{name}'")
                
                if contacts:
                    # Verify the search worked correctly
                    sample_contact = contacts[0]
                    
                    if sample_contact.get("given_name") == name:
                        logger.info(f"Verified name search worked: {sample_contact.get('given_name')}")
                    else:
                        logger.warning(f"Name search may not work correctly: {sample_contact.get('given_name')}")
            
            except Exception as e:
                logger.error(f"Error searching by name {name}: {e}")
        
        # Test search by date range (for recently updated contacts)
        logger.info("Testing search by date range...")
        
        # Test with last 30 days
        thirty_days_ago = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - 
                           datetime.timedelta(days=30)).isoformat() + "Z"
        today = datetime.now().isoformat() + "Z"
        
        params = {
            "page_size": 10,
            "since": thirty_days_ago,
            "until": today
        }
        
        try:
            contacts = await client.query_contacts(params)
            logger.info(f"Found {len(contacts)} contacts updated in the last 30 days")
        except Exception as e:
            logger.error(f"Error searching by date range: {e}")
        
    except Exception as e:
        logger.error(f"Error validating search capabilities: {e}")
    finally:
        await client.close()

async def main():
    """Run all validation tests"""
    logger.info("Starting Keap API validation tests")
    
    tasks = [
        validate_contacts_endpoint(),
        validate_tags_endpoint(),
        validate_custom_fields(),
        validate_tag_application(),
        validate_rate_limits(),
        validate_contact_operations(),
        validate_error_handling(),
        validate_pagination_limits(),
        validate_search_capabilities()
    ]
    
    await asyncio.gather(*tasks)
    
    logger.info("Completed all validation tests")

if __name__ == "__main__":
    asyncio.run(main())
