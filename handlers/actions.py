import json
import logging
import threading
from config import settings
from slack_bolt import App
from slack_app.schemas import PointerRecord
from slack_app.canvas import write_pointer_to_canvas
from slack_app.blocks import get_logged_success_blocks, get_dismissed_blocks

logger = logging.getLogger("recorder.handlers.actions")

def process_confirm_async(client, respond, user_id: str, action_value: str):
    """
    Background worker that parses metadata, calls the Canvas write function,
    and uses the response_url via respond() to update the ephemeral prompt.
    """
    if not action_value:
        logger.error("Missing payload metadata in confirm button value.")
        respond(text="❌ Error: Missing metadata payload.")
        return

    try:
        metadata = json.loads(action_value)
    except Exception as e:
        logger.error(f"Failed to parse metadata JSON: {e}")
        respond(text="❌ Error: Invalid metadata format.")
        return

    # 1. Check if SLACK_CANVAS_ID is configured in settings
    canvas_id = settings.SLACK_CANVAS_ID
    if not canvas_id:
        logger.error("SLACK_CANVAS_ID is missing from settings.")
        respond(text="❌ Error: Canvas ID not configured. Set `SLACK_CANVAS_ID` in your `.env`.")
        return

    # 2. Instantiate PointerRecord schema model
    try:
        pointer = PointerRecord(**metadata)
    except Exception as e:
        logger.error(f"Failed schema validation for PointerRecord: {e}")
        respond(text="❌ Error: Schema validation failed.")
        return

    # 3. Write pointer entry to Slack Canvas
    success = write_pointer_to_canvas(client, canvas_id, pointer)
    
    # 4. Return user feedback via response_url
    if success:
        logger.info(f"Successfully wrote pointer to Canvas. Updating ephemeral UI...")
        success_blocks = get_logged_success_blocks(user_id, pointer.type)
        respond(blocks=success_blocks, replace_original=True)
        # Schedule verification for commitment type pointers
        if pointer.type == "commitment":
            from handlers.verifier import schedule_verification
            schedule_verification(client, pointer)
    else:
        logger.error("Failed to append pointer entry to Canvas.")
        respond(text="❌ Error: Canvas write failed. Please check app permissions.")



def register_action_handlers(slack_app: App):
    """
    Registers Bolt interactive action listeners for button clicks.
    """
    @slack_app.action("confirm_log")
    def handle_confirm(ack, body, action, client, respond):
        # 1. Acknowledge interactive payload immediately (<3 seconds)
        ack()
        
        user_id = body.get("user", {}).get("id")
        action_value = action.get("value")
        
        logger.info(f"User {user_id} clicked ✓ Log. Processing canvas update...")
        
        # 2. Offload heavier Canvas API writes to a background thread
        thread = threading.Thread(
            target=process_confirm_async,
            args=(client, respond, user_id, action_value),
            daemon=True
        )
        thread.start()

    @slack_app.action("dismiss_log")
    def handle_dismiss(ack, respond):
        # 1. Acknowledge interactive payload immediately
        ack()
        
        logger.info("User clicked ✗ Dismiss. Updating ephemeral UI...")
        
        # 2. Update the prompt to show dismissed status (runs quickly, no background thread needed)
        try:
            respond(blocks=get_dismissed_blocks(), replace_original=True)
        except Exception as e:
            logger.error(f"Error dismissing ephemeral prompt: {e}")
