"""
Recorder — starter bot server.

What this file does, in plain terms:
1. Loads your three secrets from a .env file.
2. Sets up a Slack Bolt app (this is what actually talks to Slack).
3. Adds ONE listener: when someone @mentions Recorder, it replies "hello".
    This is just to prove the whole chain works before we add real logic.
4. Wraps it inside a FastAPI app, so we have a proper web server
    (with a /health endpoint) that we can build on later.
5. Runs Slack's "Socket Mode" connection in a background thread, so
    FastAPI and Slack can both be alive at the same time.
"""

import os
import threading
import logging

from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn

from slack_bolt import App as SlackApp
from slack_bolt.adapter.socket_mode import SocketModeHandler

# ---- Step 1: load secrets from .env ----
load_dotenv()

BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

if not BOT_TOKEN or not APP_TOKEN:
    raise RuntimeError(
        "Missing SLACK_BOT_TOKEN or SLACK_APP_TOKEN. "
        "Copy .env.example to .env and fill in your real values."
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recorder")

# ---- Step 2: create the Slack Bolt app ----
slack_app = SlackApp(
    token=BOT_TOKEN,
    signing_secret=SIGNING_SECRET,
)


# ---- Step 3: our first listener — just prove the bot is alive ----
@slack_app.event("app_mention")
def handle_mention(event, say):
    """
    This function runs every time someone @mentions Recorder anywhere
    it's been added. Right now it just says hello back in the same thread.
    Later, this is where decision/commitment detection will plug in.
    """
    user = event.get("user")
    text = event.get("text", "")
    thread_ts = event.get("ts")  # replying in-thread, not as a new message

    logger.info(f"Got a mention from {user}: {text}")

    say(
        text=f"👋 Hey <@{user}>, I heard you. (Recorder is alive and listening.)",
        thread_ts=thread_ts,
    )


# ---- Step 4: wrap everything in a FastAPI app ----
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
    handler = SocketModeHandler(slack_app, APP_TOKEN)
    handler.start()  # this blocks forever, listening for Slack events


@api.on_event("startup")
def on_startup():
    logger.info("Starting Slack Socket Mode connection in background thread...")
    thread = threading.Thread(target=start_slack_socket_mode, daemon=True)
    thread.start()


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000)