import json
import logging
import threading
from datetime import datetime, timezone, timedelta
from config import settings
from slack_bolt import App
from slack_sdk import WebClient
from slack_app.schemas import PointerRecord
from ai.due_date import parse_due_datetime
from ai.nli import evaluate_commitment
from slack_app.evidence import gather_evidence
from slack_app.canvas_updater import update_pointer_status
from slack_app.blocks import (
    get_nudge_blocks,
    get_nudge_completed_blocks,
    get_nudge_snoozed_blocks
)

logger = logging.getLogger("recorder.handlers.verifier")

def schedule_verification(client: WebClient, pointer: PointerRecord):
    """
    Schedules a verification check for the commitment pointer.
    If pointer status is 'snoozed', schedules for snooze duration.
    Otherwise, parses the due_date_hint.
    """
    # ponytail: in-memory threading.Timer only, lost on process restart —
    # nothing reconstructs pending verifications from the Canvas on startup.
    # Fine for the hackathon demo; add Canvas-scan-on-boot if uptime matters.
    now_utc = datetime.now(timezone.utc)
    
    if pointer.status == "snoozed":
        # Snooze duration: 30 seconds for test/snooze-test, otherwise 24 hours
        if pointer.due_date_hint in ["test", "snooze-test"]:
            delay_seconds = 30.0
        else:
            delay_seconds = 24.0 * 3600.0
        due_dt = now_utc + timedelta(seconds=delay_seconds)
    else:
        due_dt = parse_due_datetime(pointer.due_date_hint)
        # For testing, if due_date_hint is "test", make the initial check fast (30 seconds)
        if pointer.due_date_hint == "test":
            delay_seconds = 30.0
            due_dt = now_utc + timedelta(seconds=delay_seconds)
        else:
            delay_seconds = (due_dt - now_utc).total_seconds()
            if delay_seconds < 0:
                delay_seconds = 5.0  # Run almost immediately if past due
                
    logger.info(f"Scheduling verification check for commitment {pointer.ts} (status: {pointer.status}) "
                f"in {delay_seconds:.1f}s (due: {due_dt})")
                
    timer = threading.Timer(
        interval=delay_seconds,
        function=run_verification,
        args=(client, pointer)
    )
    timer.daemon = True
    timer.start()

def run_verification(client: WebClient, pointer: PointerRecord):
    """
    Executes the verification pipeline: fetches evidence, evaluates via NLI,
    and updates the Canvas/sends nudges.
    """
    canvas_id = settings.SLACK_CANVAS_ID
    if not canvas_id:
        logger.error("SLACK_CANVAS_ID not configured. Cannot verify commitment.")
        return
        
    logger.info(f"Starting verification pipeline for commitment: {pointer.ts}")
    
    # 1. Fetch live evidence
    evidence = gather_evidence(client, pointer.channel_id, pointer.ts)
    commitment_text = evidence.get("commitment_text", "unretrieved commitment text")
    
    # 2. Run NLI entailment check
    verdict_res = evaluate_commitment(pointer.permalink, commitment_text, evidence)
    
    # 3. Process outcomes based on NLI verdict
    if verdict_res.verdict == "kept":
        logger.info(f"NLI Entailment: commitment {pointer.ts} was KEPT. Updating Canvas...")
        update_pointer_status(client, canvas_id, pointer, "kept")
        return
        
    if verdict_res.verdict == "superseded":
        logger.info(f"NLI Entailment: commitment {pointer.ts} was SUPERSEDED. Updating Canvas...")
        update_pointer_status(client, canvas_id, pointer, "superseded")
        return

    # Verdict is 'insufficient_evidence'
    if pointer.status == "snoozed":
        # Snooze expired, still no evidence. Mark overdue.
        logger.info(f"Snooze expired with no evidence for commitment {pointer.ts}. Marking OVERDUE.")
        update_pointer_status(client, canvas_id, pointer, "overdue")
        
        # Send a final private DM notification to owner
        try:
            client.chat_postMessage(
                channel=pointer.owner_id,
                text=f"⏳ Your commitment has expired and is now marked as *Overdue* on the Canvas:\n<{pointer.permalink}|View original commitment>"
            )
        except Exception as e:
            logger.error(f"Failed to post overdue DM nudge: {e}")
            
    else:
        # First verification check, no evidence found. Send private nudge DM.
        logger.info(f"No evidence found for commitment {pointer.ts}. Dispatching private DM nudge...")
        
        # Serialize the pointer record for nudge buttons payload value
        metadata_str = json.dumps(pointer.model_dump())
        blocks = get_nudge_blocks(pointer.owner_id, pointer.permalink, metadata_str)
        
        try:
            client.chat_postMessage(
                channel=pointer.owner_id,
                blocks=blocks,
                text="Follow-up on your logged commitment."
            )
            logger.info(f"Nudge DM sent successfully to user {pointer.owner_id}")
        except Exception as e:
            logger.error(f"Failed to send nudge DM: {e}")

def process_done_async(client: WebClient, respond, user_id: str, action_value: str):
    """
    Worker thread that marks the commitment as kept in Canvas and updates the nudge UI.
    """
    canvas_id = settings.SLACK_CANVAS_ID
    if not canvas_id:
        respond(text="❌ Error: Canvas ID not configured.")
        return

    try:
        metadata = json.loads(action_value)
        pointer = PointerRecord(**metadata)
    except Exception as e:
        logger.error(f"Failed to parse pointer metadata in nudge action: {e}")
        respond(text="❌ Error: Invalid action payload.")
        return

    # Update Canvas status to kept
    success = update_pointer_status(client, canvas_id, pointer, "kept")
    if success:
        respond(blocks=get_nudge_completed_blocks(), replace_original=True)
    else:
        respond(text="❌ Error: Failed to update Canvas status.")

def process_snooze_async(client: WebClient, respond, user_id: str, action_value: str):
    """
    Worker thread that marks the pointer as snoozed in Canvas and schedules next verification.
    """
    canvas_id = settings.SLACK_CANVAS_ID
    if not canvas_id:
        respond(text="❌ Error: Canvas ID not configured.")
        return

    try:
        metadata = json.loads(action_value)
        pointer = PointerRecord(**metadata)
    except Exception as e:
        logger.error(f"Failed to parse pointer metadata in snooze action: {e}")
        respond(text="❌ Error: Invalid action payload.")
        return

    # Update status to 'snoozed' in Canvas
    success = update_pointer_status(client, canvas_id, pointer, "snoozed")
    if success:
        # Schedule the snoozed check in background
        schedule_verification(client, pointer)
        respond(blocks=get_nudge_snoozed_blocks(), replace_original=True)
    else:
        respond(text="❌ Error: Failed to update Canvas status.")

def register_verifier_handlers(slack_app: App):
    """
    Registers Bolt action handlers for the private nudge buttons.
    """
    @slack_app.action("commitment_done")
    def handle_done(ack, body, action, client, respond):
        # Acknowledge immediately
        ack()
        user_id = body.get("user", {}).get("id")
        action_value = action.get("value")
        
        logger.info(f"User {user_id} clicked ✓ Done on nudge follow-up.")
        
        thread = threading.Thread(
            target=process_done_async,
            args=(client, respond, user_id, action_value),
            daemon=True
        )
        thread.start()

    @slack_app.action("commitment_snooze")
    def handle_snooze(ack, body, action, client, respond):
        # Acknowledge immediately
        ack()
        user_id = body.get("user", {}).get("id")
        action_value = action.get("value")
        
        logger.info(f"User {user_id} clicked ↺ Snooze on nudge follow-up.")
        
        thread = threading.Thread(
            target=process_snooze_async,
            args=(client, respond, user_id, action_value),
            daemon=True
        )
        thread.start()
