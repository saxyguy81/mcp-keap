"""
Form-Based Contact Filtering Tools

Provides specialized tools for finding contacts based on form submissions,
using tag-based tracking and date filtering approaches.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from mcp.server.fastmcp import Context
from src.mcp.tools_collections import (
    list_contacts,
    get_collection_details,
    get_tags,
    collection_intersect,
    collection_union,
    get_api_client
)

logger = logging.getLogger(__name__)


async def find_form_submissions(
    context: Context,
    form_keywords: List[str],
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    limit: int = 100,
    include_details: bool = True
) -> Dict[str, Any]:
    """Find contacts who likely submitted forms based on tags and dates.
    
    Args:
        context: MCP context
        form_keywords: Keywords to search for in tag names (e.g., ["VSN", "registration"])
        date_start: Start date for filtering (ISO format: "2025-06-10T00:00:00Z")
        date_end: End date for filtering (ISO format: "2025-06-10T23:59:59Z")
        limit: Maximum contacts to return
        include_details: Whether to include full contact details
        
    Returns:
        Dict with form submission results
        
    Examples:
        # Find VSN registrations around 6/10/25
        find_form_submissions(
            context,
            form_keywords=["VSN", "registration"],
            date_start="2025-06-09T00:00:00Z",
            date_end="2025-06-12T23:59:59Z"
        )
    """
    try:
        results = {
            "success": True,
            "form_keywords": form_keywords,
            "date_range": f"{date_start} to {date_end}" if date_start and date_end else "All time",
            "contacts_found": 0,
            "relevant_tags": [],
            "contacts": []
        }
        
        # 1. Find relevant tags based on keywords
        relevant_tag_ids = []
        
        for keyword in form_keywords:
            try:
                tag_search = await get_tags(
                    context,
                    filters=[{"field": "name", "operator": "contains", "value": keyword}],
                    limit=50
                )
                
                for tag in tag_search.get("tags", []):
                    tag_info = {
                        "id": tag.get("id"),
                        "name": tag.get("name"),
                        "keyword_match": keyword
                    }
                    results["relevant_tags"].append(tag_info)
                    relevant_tag_ids.append(tag.get("id"))
                    
            except Exception as e:
                logger.warning(f"Error searching tags for keyword '{keyword}': {e}")
        
        if not relevant_tag_ids:
            results["message"] = "No relevant tags found for the specified keywords"
            return results
        
        # 2. Build filters for contact search
        filters = []
        
        # Add date filters if specified
        if date_start:
            filters.append({
                "field": "date_created",
                "operator": "after",
                "value": date_start
            })
        
        if date_end:
            filters.append({
                "field": "date_created", 
                "operator": "before",
                "value": date_end
            })
        
        # 3. Search for contacts in date range
        date_collection_id = None
        if filters:
            date_result = await list_contacts(
                context,
                filters=filters,
                limit=limit * 2  # Get more to account for intersection
            )
            date_collection_id = date_result["collection_id"]
            logger.info(f"Found {date_result['count']} contacts in date range")
        
        # 4. Search for contacts with relevant tags
        tag_collections = []
        
        # Split tag IDs into smaller groups to avoid API limits
        tag_batch_size = 10
        for i in range(0, len(relevant_tag_ids), tag_batch_size):
            batch_tag_ids = relevant_tag_ids[i:i + tag_batch_size]
            
            try:
                tag_result = await list_contacts(
                    context,
                    filters=[{"field": "tag_id", "operator": "in", "value": batch_tag_ids}],
                    limit=limit * 2
                )
                
                if tag_result["count"] > 0:
                    tag_collections.append(tag_result["collection_id"])
                    logger.info(f"Tag batch {i//tag_batch_size + 1}: {tag_result['count']} contacts")
                    
            except Exception as e:
                logger.warning(f"Error searching contacts for tag batch {batch_tag_ids}: {e}")
        
        # 5. Find intersection of date and tag filters
        final_collection_id = None
        
        if date_collection_id and tag_collections:
            # Combine all tag collections first
            if len(tag_collections) > 1:
                tag_union = await collection_union(context, tag_collections)
                combined_tag_collection = tag_union["collection_id"]
            else:
                combined_tag_collection = tag_collections[0]
            
            # Intersect date and tag collections
            intersection = await collection_intersect(
                context, 
                [date_collection_id, combined_tag_collection]
            )
            final_collection_id = intersection["collection_id"]
            results["contacts_found"] = intersection["count"]
            
        elif date_collection_id:
            # Only date filtering
            final_collection_id = date_collection_id
            results["contacts_found"] = date_result["count"]
            
        elif tag_collections:
            # Only tag filtering
            if len(tag_collections) > 1:
                tag_union = await collection_union(context, tag_collections)
                final_collection_id = tag_union["collection_id"]
                results["contacts_found"] = tag_union["count"]
            else:
                # Single tag collection
                api_client = get_api_client()
                try:
                    # Get count from the collection
                    details = await get_collection_details(
                        context, 
                        tag_collections[0], 
                        count_only=True
                    )
                    results["contacts_found"] = details["count"]
                    final_collection_id = tag_collections[0]
                except Exception as e:
                    logger.warning(f"Error getting tag collection count: {e}")
                    results["contacts_found"] = 0
        
        # 6. Get contact details if requested
        if include_details and final_collection_id and results["contacts_found"] > 0:
            try:
                details = await get_collection_details(
                    context,
                    final_collection_id,
                    fields=[
                        "id", "given_name", "family_name", "email", 
                        "date_created", "last_updated", "tag_ids"
                    ],
                    limit=min(limit, results["contacts_found"])
                )
                
                contacts_with_tags = []
                for contact in details.get("contacts", []):
                    # Add matching tag names to contact info
                    contact_tag_ids = contact.get("tag_ids", [])
                    matching_tags = [
                        tag["name"] for tag in results["relevant_tags"]
                        if tag["id"] in contact_tag_ids
                    ]
                    
                    contact_info = {
                        "id": contact.get("id"),
                        "name": f"{contact.get('given_name', '')} {contact.get('family_name', '')}".strip(),
                        "email": contact.get("email"),
                        "date_created": contact.get("date_created"),
                        "matching_form_tags": matching_tags
                    }
                    contacts_with_tags.append(contact_info)
                
                results["contacts"] = contacts_with_tags
                
            except Exception as e:
                logger.error(f"Error getting contact details: {e}")
                results["detail_error"] = str(e)
        
        results["collection_id"] = final_collection_id
        return results
        
    except Exception as e:
        logger.error(f"Error in find_form_submissions: {e}")
        return {
            "success": False,
            "error": str(e),
            "form_keywords": form_keywords
        }


async def find_contact_by_email_and_form(
    context: Context,
    email: str,
    form_keywords: Optional[List[str]] = None,
    date_tolerance_days: int = 7
) -> Dict[str, Any]:
    """Find a specific contact by email and verify form submission activity.
    
    Args:
        context: MCP context
        email: Contact email address
        form_keywords: Keywords to check in associated tags
        date_tolerance_days: Days around contact creation to check for form activity
        
    Returns:
        Dict with contact info and form submission analysis
    """
    try:
        # 1. Find the contact by email
        contact_result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "equals", "value": email}],
            limit=5
        )
        
        if contact_result["count"] == 0:
            return {
                "success": False,
                "message": f"No contact found with email: {email}",
                "email": email
            }
        
        # 2. Get contact details
        contact_details = await get_collection_details(
            context,
            contact_result["collection_id"],
            fields=[
                "id", "given_name", "family_name", "email", 
                "date_created", "last_updated", "tag_ids"
            ]
        )
        
        contact = contact_details["contacts"][0]
        contact_tag_ids = contact.get("tag_ids", [])
        
        result = {
            "success": True,
            "contact": {
                "id": contact.get("id"),
                "name": f"{contact.get('given_name', '')} {contact.get('family_name', '')}".strip(),
                "email": contact.get("email"),
                "date_created": contact.get("date_created"),
                "tag_count": len(contact_tag_ids)
            },
            "form_analysis": {
                "total_tags": len(contact_tag_ids),
                "form_related_tags": [],
                "potential_form_submissions": []
            }
        }
        
        # 3. Analyze tags for form-related activity
        if contact_tag_ids and form_keywords:
            # Get all tags to analyze which ones match form keywords
            all_tags = await get_tags(context, limit=1000)
            
            tag_lookup = {tag["id"]: tag["name"] for tag in all_tags.get("tags", [])}
            
            form_related_tags = []
            for tag_id in contact_tag_ids:
                tag_name = tag_lookup.get(tag_id, f"Unknown Tag {tag_id}")
                
                # Check if tag name contains any form keywords
                for keyword in form_keywords:
                    if keyword.lower() in tag_name.lower():
                        form_related_tags.append({
                            "tag_id": tag_id,
                            "tag_name": tag_name,
                            "keyword_match": keyword
                        })
                        break
            
            result["form_analysis"]["form_related_tags"] = form_related_tags
            
            # 4. Look for other contacts with similar form activity around same time
            if contact.get("date_created"):
                contact_date = datetime.fromisoformat(contact["date_created"].replace("Z", "+00:00"))
                start_date = (contact_date - timedelta(days=date_tolerance_days)).isoformat()
                end_date = (contact_date + timedelta(days=date_tolerance_days)).isoformat()
                
                similar_submissions = await find_form_submissions(
                    context,
                    form_keywords=form_keywords,
                    date_start=start_date,
                    date_end=end_date,
                    limit=20,
                    include_details=False
                )
                
                result["form_analysis"]["similar_timeframe_submissions"] = similar_submissions.get("contacts_found", 0)
                result["form_analysis"]["relevant_tags_in_timeframe"] = len(similar_submissions.get("relevant_tags", []))
        
        return result
        
    except Exception as e:
        logger.error(f"Error in find_contact_by_email_and_form: {e}")
        return {
            "success": False,
            "error": str(e),
            "email": email
        }