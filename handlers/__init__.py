from slack_bolt import App
from handlers.events import register_event_handlers
from handlers.actions import register_action_handlers
from handlers.retrieval import register_retrieval_handlers

def register_handlers(slack_app: App):
    """
    Orchestrates listener registrations for both events and action payloads
    on the global Bolt App.
    """
    register_event_handlers(slack_app)
    register_action_handlers(slack_app)
    register_retrieval_handlers(slack_app)
