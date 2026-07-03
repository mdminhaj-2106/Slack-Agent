import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_app.schemas import PointerRecord
from slack_app.formatter import format_pointer_as_markdown

logger = logging.getLogger("recorder.slack.canvas")

def write_pointer_to_canvas(client: WebClient, canvas_id: str, pointer: PointerRecord) -> bool:
    """
    Appends a formatted PointerRecord markdown entry to the target Slack Canvas.
    Enforces the 'evidence-only' rule: rejects writes containing raw text outside the schema.
    """
    # 1. Enforce strict safety boundary check
    if any(char in pointer.type for char in ["\n", "\r"]) or len(pointer.type) > 50:
        logger.error("Security violation: pointer type contains invalid structure.")
        return False
        
    # 2. Format the pointer as markdown list item using the formatter module
    markdown_content = format_pointer_as_markdown(pointer)
    
    # 3. Call canvases.edit Web API method to append content
    try:
        logger.info(f"Writing pointer {pointer.ts} to canvas {canvas_id}...")
        response = client.canvases_edit(
            canvas_id=canvas_id,
            changes=[
                {
                    "operation": "insert_at_end",
                    "document_content": {
                        "type": "markdown",
                        "markdown": markdown_content
                    }
                }
            ]
        )
        if response.get("ok"):
            logger.info("Successfully appended pointer to canvas.")
            return True
        else:
            logger.error(f"Failed to append to canvas: {response.get('error')}")
            return False
            
    except SlackApiError as e:
        logger.error(f"Slack API Error in write_pointer_to_canvas: {e.response.get('error', e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in write_pointer_to_canvas: {e}")
        return False
