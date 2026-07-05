"""
Recorder — starter bot server.

What this file does, in plain terms:
1. Loads your three secrets from a .env file.
2. Sets up a Slack Bolt app (this is what actually talks to Slack).
3. Registers Slack listeners (message capture, action buttons, /why retrieval)
    via handlers/register_handlers.
4. Wraps it inside a FastAPI app, so we have a proper web server
    (with a /health endpoint) that we can build on later.
5. Runs Slack's "Socket Mode" connection in a background thread, so
    FastAPI and Slack can both be alive at the same time.
"""

import os
import threading
import logging
from fastapi import FastAPI
import uvicorn

from slack_bolt import App as SlackApp
from slack_bolt.adapter.socket_mode import SocketModeHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recorder")

from config import settings
from handlers import register_handlers

# ---- Step 2: create the Slack Bolt app ----
slack_app = SlackApp(
    token=settings.SLACK_BOT_TOKEN,
    signing_secret=settings.SLACK_SIGNING_SECRET,
)

# Register Slack listeners
register_handlers(slack_app)
# ---- Step 3: wrap everything in a FastAPI app ----
api = FastAPI(title="Recorder Bot")


@api.get("/health")
def health_check():
    """Simple endpoint to confirm the server process is up."""
    return {"status": "ok", "service": "recorder-bot"}


def start_slack_socket_mode():
    """
    This runs Slack's Socket Mode connection. It's a persistent,
    long-running connection, so it needs its own thread — otherwise
    it would block FastAPI from starting.
    """
    import time
    handler = SocketModeHandler(slack_app, settings.SLACK_APP_TOKEN)
    handler.connect()  # establishes the connection without registering signals
    while True:
        time.sleep(3600)  # blocks the thread to keep the handler in scope



@api.on_event("startup")
def on_startup():
    logger.info("Starting Slack Socket Mode connection in background thread...")
    thread = threading.Thread(target=start_slack_socket_mode, daemon=True)
    thread.start()


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000)