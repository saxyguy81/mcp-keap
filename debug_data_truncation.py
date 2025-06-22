"""
Debug script to investigate the data truncation issue step by step.
"""

import asyncio
from mcp.server.fastmcp import Context
from src.mcp.tools_collections import list_contacts, get_collection_details

async def debug_data_issue():
    """Debug the data truncation issue step by step."""
    context = Context()
    
    print("🔍 Step 1: Create a small collection")
    result = await list_contacts(context, limit=5)
    print(f"Collection created: {result['collection_id']} with {result['count']} contacts")
    
    if result['count'] == 0:
        print("❌ No contacts found - stopping debug")
        return
    
    print("\n🔍 Step 2: Check collection manager directly")
    from src.cache.collections import get_collection_manager
    collection_manager = get_collection_manager()
    
    # Check if collection exists
    print(f"Collection exists in manager: {collection_manager.collection_exists(result['collection_id'])}")
    
    if not collection_manager.collection_exists(result['collection_id']):
        print("❌ Collection doesn't exist in manager")
        return
    
    # Get target IDs directly
    target_ids = collection_manager.get_contact_ids(result['collection_id'])
    print(f"Target IDs from collection manager: {list(target_ids) if target_ids else None}")
    print(f"Target IDs type: {type(target_ids)}")
    print(f"Target IDs length: {len(target_ids) if target_ids else 0}")
    
    if not target_ids:
        print("❌ No contact IDs found in collection manager")
        return
    
    print("\n🔍 Step 3: Get collection details (this should work)")
    details_result = await get_collection_details(context, result['collection_id'])
    print(f"Details result count: {details_result.get('count', 0)}")
    print(f"Details result contacts: {len(details_result.get('contacts', []))}")
    
    if details_result.get('count', 0) == 0:
        print("❌ get_collection_details returned 0 contacts - this is the bug!")
        
        # Let's debug the individual steps
        print("\n🔍 Step 4: Debug individual steps")
        
        # Check what the collection manager has
        from src.cache.collections import get_collection_manager
        collection_manager = get_collection_manager()
        
        # Check if collection exists
        print(f"Collection exists in manager: {collection_manager.collection_exists(result['collection_id'])}")
        
        # Get collection info
        if collection_manager.collection_exists(result['collection_id']):
            collection_info = collection_manager.get_collection_info(result['collection_id'])
            print(f"Collection info: {collection_info}")
            
            # Get target IDs directly
            target_ids = collection_manager.get_contact_ids(result['collection_id'])
            print(f"Target IDs from collection manager: {target_ids}")
            print(f"Target IDs type: {type(target_ids)}")
            print(f"Target IDs length: {len(target_ids) if target_ids else 0}")
            
            if target_ids:
                print(f"First few target IDs: {list(target_ids)[:5]}")
                print(f"Target ID types: {[type(id) for id in list(target_ids)[:3]]}")
    else:
        print("✅ get_collection_details is working!")
        
        # Show sample results
        contacts = details_result.get('contacts', [])
        if contacts:
            print(f"Sample contact IDs: {[c.get('id') for c in contacts[:3]]}")
            print(f"Sample contact ID types: {[type(c.get('id')) for c in contacts[:3]]}")

if __name__ == "__main__":
    asyncio.run(debug_data_issue())