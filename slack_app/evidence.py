import logging
from typing import Dict, Set
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger("recorder.slack_app.evidence")

DONE_EMOJI_SET: Set[str] = {"white_check_mark", "heavy_check_mark", "done", "✅", "check"}

def gather_evidence(client: WebClient, channel_id: str, commitment_ts: str) -> Dict:
    """
    Fetches post-commitment replies and original message reactions from Slack.
    Excludes bot messages. Returns a dictionary containing evidence list.
    """
    evidence = {
        "commitment_text": "",
        "thread_replies": [],
        "done_reactions": []
    }

    # 1. Fetch Reactions on the original commitment message
    try:
        logger.info(f"Fetching reactions for message {commitment_ts} in channel {channel_id}")
        reactions_res = client.reactions_get(channel=channel_id, timestamp=commitment_ts)
        if reactions_res.get("ok"):
            message = reactions_res.get("message", {})
            reactions = message.get("reactions", [])
            for r in reactions:
                name = r.get("name")
                if name in DONE_EMOJI_SET:
                    evidence["done_reactions"].append(name)
                    
    except SlackApiError as e:
        logger.error(f"Slack API error fetching reactions: {e.response.get('error', e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching reactions: {e}")

    # 2. Fetch Thread Replies
    try:
        logger.info(f"Fetching replies for thread {commitment_ts} in channel {channel_id}")
        replies_res = client.conversations_replies(
            channel=channel_id,
            ts=commitment_ts,
            oldest=commitment_ts,
            limit=100
        )
        if replies_res.get("ok"):
            messages = replies_res.get("messages", [])
            for msg in messages:
                ts = msg.get("ts")
                # Filter out the original commitment message itself
                if ts == commitment_ts:
                    evidence["commitment_text"] = msg.get("text", "")
                    continue
                # Filter out bot messages
                if msg.get("bot_id") or msg.get("subtype") == "bot_message":
                    continue
                    
                evidence["thread_replies"].append({
                    "user": msg.get("user", "unknown_user"),
                    "text": msg.get("text", ""),
                    "ts": ts
                })
                
    except SlackApiError as e:
        # If thread replies are disabled/not found or rate limited
        logger.error(f"Slack API error fetching replies: {e.response.get('error', e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching replies: {e}")

    logger.info(f"Evidence gathered for commitment {commitment_ts}: "
                f"{len(evidence['thread_replies'])} replies, "
                f"{len(evidence['done_reactions'])} done reactions.")
    return evidence
