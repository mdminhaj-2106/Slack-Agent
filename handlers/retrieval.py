import logging
import re
import threading
from slack_bolt import App

logger = logging.getLogger("recorder.handlers.retrieval")

USAGE_HINT = (
    'Mention me with a question containing "why" (e.g. `@Recorder why did we pick Postgres?`) '
    "to search evidence."
)


def extract_why_query(text: str) -> str | None:
    """
    Strips the bot mention tag from the event text and returns the remaining
    stripped text if it contains "why" (case-insensitive), else None.
    """
    stripped = re.sub(r"<@[^>]+>", "", text).strip()
    if "why" in stripped.lower():
        return stripped
    return None


def run_search_and_reply(client, say, action_token, query, thread_ts):
    """
    Background-thread target: calls assistant.search.context with the given
    action_token, then posts a permalinks-only reply in-thread.
    """
    if not action_token:
        logger.error("Missing action_token on app_mention event; cannot call assistant.search.context.")
        say(text="Can't search right now — try mentioning me again.", thread_ts=thread_ts)
        return

    try:
        response = client.api_call(
            "assistant.search.context",
            json={
                "query": query,
                "action_token": action_token,
                "channel_types": ["public_channel", "private_channel"],
                "limit": 10,
                "sort": "score",
            },
        )
    except Exception as e:
        logger.error(f"assistant.search.context call failed: {e}")
        say(text="Can't search right now — try mentioning me again.", thread_ts=thread_ts)
        return

    if not response.get("ok"):
        logger.error(f"assistant.search.context returned not ok: {response}")
        say(text="Can't search right now — try mentioning me again.", thread_ts=thread_ts)
        return

    # Never read `content` (raw message snippet) — permalink/author/channel only.
    messages = response.get("results", {}).get("messages", [])
    if not messages:
        say(text=f"No matching evidence found for '{query}' yet.", thread_ts=thread_ts)
        return

    lines = [f'Here\'s what I found on "{query}":']
    for i, msg in enumerate(messages[:5], start=1):
        lines.append(
            f"{i}. {msg.get('permalink')} — via @{msg.get('author_name')} in #{msg.get('channel_name')}"
        )

    say(text="\n".join(lines), thread_ts=thread_ts)


def register_retrieval_handlers(slack_app: App):
    """
    Registers the app_mention listener that owns /why retrieval. Sole owner of
    app_mention — the old hardcoded "hello" handler in main.py is removed.
    """
    @slack_app.event("app_mention")
    def handle_mention(event, say, client):
        thread_ts = event.get("thread_ts") or event.get("ts")
        query = extract_why_query(event.get("text", ""))

        if query is None:
            say(text=USAGE_HINT, thread_ts=thread_ts)
            return

        thread = threading.Thread(
            target=run_search_and_reply,
            args=(client, say, event.get("action_token"), query, thread_ts),
            daemon=True,
        )
        thread.start()
