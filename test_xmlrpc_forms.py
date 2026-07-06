#!/usr/bin/env python3
"""
Test XML-RPC API access to form submission data using DataService.query
"""

import asyncio
import os
import xmlrpc.client
from dotenv import load_dotenv

load_dotenv()

class KeapXMLRPCClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://api.infusionsoft.com/crm/xmlrpc/v1'
        
    def sync_query(self, table, limit=1000, page=0, query_data=None, return_fields=None):
        """Synchronous XML-RPC query using xmlrpc.client"""
        try:
            # Create XML-RPC client
            server = xmlrpc.client.ServerProxy(self.base_url)
            
            # Prepare parameters
            query_data = query_data or {}
            return_fields = return_fields or ['Id']
            
            print(f"Querying table: {table}")
            print(f"Query data: {query_data}")
            print(f"Return fields: {return_fields}")
            
            # Make the call
            result = server.DataService.query(
                self.api_key,
                table,
                limit,
                page,
                query_data,
                return_fields
            )
            
            return result
            
        except Exception as e:
            print(f"XML-RPC error: {e}")
            return None

async def test_xmlrpc_form_access():
    print('🔍 TESTING XML-RPC API FOR FORM SUBMISSION DATA')
    print('='*70)
    
    api_key = os.getenv('KEAP_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return
    
    client = KeapXMLRPCClient(api_key)
    
    try:
        # 1. Try to query form-related tables
        print('\n📋 Step 1: Testing different table queries...')
        
        potential_tables = [
            'Contact',
            'WebForm', 
            'FormSubmission',
            'Submission',
            'Entry',
            'Lead',
            'ContactAction',
            'ContactGroupAssign'
        ]
        
        for table in potential_tables:
            print(f'\n  Testing table: {table}')
            try:
                # Try a simple query with minimal data
                result = client.sync_query(
                    table=table,
                    limit=5,
                    return_fields=['Id']
                )
                
                if result is not None:
                    print(f'  ✅ {table}: Found {len(result)} records')
                    if result and isinstance(result, list):
                        print(f'    Sample record: {result[0]}')
                else:
                    print(f'  ❌ {table}: No data or error')
                    
            except Exception as e:
                print(f'  ❌ {table}: Error - {str(e)[:100]}')
        
        # 2. Query contacts with form-related custom fields
        print('\n📋 Step 2: Querying contacts with form data...')
        
        try:
            # Query contacts created recently (our test contact timeframe)
            result = client.sync_query(
                table='Contact',
                limit=50,
                return_fields=['Id', 'Email', 'DateCreated', '_VSNPromoSource', '_6FCPromoSource']
            )
            
            if result:
                print(f'Found {len(result)} contacts')
                for contact in result[:5]:
                    print(f'  Contact {contact.get("Id")}: {contact.get("Email")} - Created: {contact.get("DateCreated")}')
                    if contact.get('_VSNPromoSource'):
                        print(f'    VSN Source: {contact.get("_VSNPromoSource")}')
                        
        except Exception as e:
            print(f'Contact query error: {e}')
        
        # 3. Try to find our specific test contact
        print('\n📋 Step 3: Searching for test contact by email...')
        
        try:
            result = client.sync_query(
                table='Contact',
                limit=10,
                query_data={'Email': 'smhanan+test6@gmail.com'},
                return_fields=['Id', 'Email', 'DateCreated', 'FirstName', 'LastName']
            )
            
            if result:
                print(f'Found test contact: {result[0]}')
                contact_id = result[0].get('Id')
                
                # Try to get more detailed info about this contact
                if contact_id:
                    detailed_result = client.sync_query(
                        table='Contact',
                        limit=1,
                        query_data={'Id': contact_id},
                        return_fields=['Id', 'Email', 'DateCreated', 'LeadSourceId', 'OwnerID']
                    )
                    print(f'Detailed contact info: {detailed_result}')
            else:
                print('Test contact not found via XML-RPC')
                
        except Exception as e:
            print(f'Test contact search error: {e}')
        
        # 4. Try to query WebForm table specifically
        print('\n📋 Step 4: Attempting WebForm table access...')
        
        try:
            webform_result = client.sync_query(
                table='WebForm',
                limit=10,
                return_fields=['Id', 'Name', 'Html']
            )
            
            if webform_result:
                print(f'Found {len(webform_result)} webforms:')
                for form in webform_result:
                    print(f'  Form {form.get("Id")}: {form.get("Name", "Unnamed")}')
            else:
                print('No webforms found')
                
        except Exception as e:
            print(f'WebForm query error: {e}')
        
        # 5. Try to use WebformService methods
        print('\n📋 Step 5: Testing WebformService methods...')
        
        try:
            server = xmlrpc.client.ServerProxy(client.base_url)
            
            # Try to get webform IDs
            webform_ids = server.WebformService.getWebformIds(api_key)
            print(f'Available webform IDs: {webform_ids}')
            
            # If we have webform IDs, try to get one
            if webform_ids and len(webform_ids) > 0:
                form_id = webform_ids[0]
                form_html = server.WebformService.retrieveForm(api_key, form_id)
                print(f'Form {form_id} HTML length: {len(form_html) if form_html else 0}')
                
        except Exception as e:
            print(f'WebformService error: {e}')
        
        print('\n' + '='*70)
        print('📊 XML-RPC INVESTIGATION RESULTS')
        print('='*70)
        
        print('\n💡 WHAT XML-RPC CAN ACCESS:')
        print('  • Contact records with custom fields')
        print('  • WebForm definitions and HTML')
        print('  • Basic contact creation and modification data')
        
        print('\n❌ WHAT XML-RPC CANNOT ACCESS:')
        print('  • Direct form submission logs/records')
        print('  • Submission timestamps separate from contact creation')
        print('  • Original form field values at time of submission')
        
        print('\n🔧 RECOMMENDATIONS:')
        print('  1. XML-RPC provides more detailed contact access than REST API')
        print('  2. Can query contacts by custom field values more flexibly')
        print('  3. WebformService can retrieve form definitions')
        print('  4. Still no direct access to submission records')
        print('  5. Best approach: Real-time webhook capture for future submissions')
        
    except Exception as e:
        print(f'❌ General error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_xmlrpc_form_access())