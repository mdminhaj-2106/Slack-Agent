import os
from dotenv import load_dotenv

# Load env variables from .env on module import
load_dotenv()

class Settings:
    """
    Settings class that loads and validates environment variables.
    Replaces direct os.environ usage throughout the application.
    """
    def __init__(self):
        self.SLACK_BOT_TOKEN: str = os.environ.get("SLACK_BOT_TOKEN", "")
        self.SLACK_APP_TOKEN: str = os.environ.get("SLACK_APP_TOKEN", "")
        self.SLACK_SIGNING_SECRET: str = os.environ.get("SLACK_SIGNING_SECRET", "")
        self.GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
        self.SLACK_CANVAS_ID: str = os.environ.get("SLACK_CANVAS_ID", "")

    def validate(self):
        """
        Validates critical configuration parameters required to start the bot.
        """
        if not self.SLACK_BOT_TOKEN or not self.SLACK_APP_TOKEN:
            raise RuntimeError(
                "Missing SLACK_BOT_TOKEN or SLACK_APP_TOKEN. "
                "Copy .env.example to .env and fill in your real values."
            )

# Instantiate a global settings object for import across the codebase
settings = Settings()
settings.validate()
