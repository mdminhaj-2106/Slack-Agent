import json
import logging
import threading
from slack_bolt import App
from ai.classifier import classify_text
from slack_app.blocks import get_ephemeral_confirm_blocks

logger = logging.getLogger("recorder.handlers.events")

def process_message_async(client, event):
    """
    Asynchronously processes the message: gets permalink, runs classification,
    and posts ephemeral prompt if classification confidence is high.
    """
    user_id = event.get("user")
    text = event.get("text", "")
    ts = event.get("ts")
    channel_id = event.get("channel")
    thread_ts = event.get("thread_ts")
    # ponytail: Slack drops ephemeral messages threaded onto a ts with zero real
    # replies, so only thread when a reply thread already exists; otherwise post
    # as a plain (non-threaded) ephemeral, which does render.

    if not user_id or not text or not ts or not channel_id:
        return

    # 1. Fetch message permalink
    try:
        permalink_res = client.chat_getPermalink(channel=channel_id, message_ts=ts)
        if not permalink_res.get("ok"):
            logger.error("Failed to get message permalink")
            return
        permalink = permalink_res.get("permalink")
    except Exception as e:
        logger.error(f"Error fetching permalink: {e}")
        return

    # 2. Run LangGraph classification
    res = classify_text(text, user_id)
    if not res:
        logger.warning(f"No classification returned for text: {text[:30]}...")
        return
        
    logger.info(f"Message TS {ts} classified as '{res.category}' with confidence {res.confidence:.2f}")

    # 3. If high-confidence match, prompt the user ephemerally
    if res.category in ["decision", "commitment"] and res.confidence >= 0.8:
        # Create metadata payload to pass to action handler
        metadata = {
            "channel_id": channel_id,
            "ts": ts,
            "permalink": permalink,
            "type": res.category,
            "owner_id": res.owner_id or user_id,
            "confidence": res.confidence,
            "status": "open" if res.category == "commitment" else "logged"
        }
        metadata_str = json.dumps(metadata)
        
        blocks = get_ephemeral_confirm_blocks(
            user_id=user_id,
            category=res.category,
            payload_value=metadata_str
        )
        
        try:
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                blocks=blocks,
                thread_ts=thread_ts,
                text=f"Detected a potential {res.category}. Click Log to save it."
            )
            logger.info(f"Dispatched ephemeral confirmation to user {user_id} in channel {channel_id}")
        except Exception as e:
            logger.error(f"Error posting ephemeral prompt: {e}")


def register_event_handlers(slack_app: App):
    """
    Registers the message event handler.
    """
    @slack_app.event("message")
    def handle_message(event, client):
        # Ignore messages sent by bots, integration users, or other system events
        if event.get("bot_id") or event.get("subtype") is not None:
            return
            
        # Ignore empty messages
        if not event.get("text"):
            return

        logger.info(f"Intercepted new message from user {event.get('user')}")
        
        # Offload execution to a daemon background thread to return control quickly
        thread = threading.Thread(
            target=process_message_async,
            args=(client, event),
            daemon=True
        )
        thread.start()
