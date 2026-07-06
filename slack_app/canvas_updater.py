import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_app.schemas import PointerRecord
from slack_app.formatter import format_pointer_as_markdown

logger = logging.getLogger("recorder.slack_app.canvas_updater")

def update_pointer_status(client: WebClient, canvas_id: str, pointer: PointerRecord, new_status: str) -> bool:
    """
    Looks up the Canvas section containing the pointer's timestamp and replaces
    its content in-place with the updated status.
    """
    # 1. Update the status in the pointer object
    pointer.status = new_status
    
    # 2. Rebuild the expected markdown line using the formatter
    new_markdown = format_pointer_as_markdown(pointer)
    
    # 3. Find the section containing the pointer's timestamp
    try:
        logger.info(f"Looking up section for pointer {pointer.ts} on canvas {canvas_id}...")
        lookup_res = client.api_call(
            "canvases.sections.lookup",
            json={
                "canvas_id": canvas_id,
                "criteria": {
                    "contains_text": pointer.ts
                }
            }
        )
        
        if not lookup_res.get("ok"):
            logger.error(f"Canvas section lookup failed: {lookup_res.get('error')}")
            return False
            
        sections = lookup_res.get("sections", [])
        if not sections:
            logger.warning(f"No Canvas section found containing pointer timestamp {pointer.ts}. "
                           f"It may have been manually deleted from the Canvas.")
            return False
            
        # Get the first matching section
        section_id = sections[0].get("id")
        logger.info(f"Found Canvas section ID: {section_id} for pointer {pointer.ts}")
        
        # 4. Call canvases.edit with operation 'replace'
        logger.info(f"Replacing section {section_id} with updated status: {new_status}")
        edit_res = client.api_call(
            "canvases.edit",
            json={
                "canvas_id": canvas_id,
                "changes": [
                    {
                        "operation": "replace",
                        "section_id": section_id,
                        "document_content": {
                            "type": "markdown",
                            "markdown": new_markdown
                        }
                    }
                ]
            }
        )
        
        if edit_res.get("ok"):
            logger.info(f"Successfully updated Canvas pointer status to '{new_status}' in-place.")
            return True
        else:
            logger.error(f"Failed to replace Canvas section: {edit_res.get('error')}")
            return False
            
    except SlackApiError as e:
        logger.error(f"Slack API error in update_pointer_status: {e.response.data}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating Canvas pointer: {e}")
        return False
