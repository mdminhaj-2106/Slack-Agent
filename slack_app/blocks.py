def get_ephemeral_confirm_blocks(user_id: str, category: str, payload_value: str) -> list[dict]:
    """
    Generates Block Kit blocks for the ephemeral confirmation prompt.
    Uses standard Slack message markdown formatting.
    """
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"👋 Hey <@{user_id}>, I detected a potential *{category.capitalize()}* in your message. Would you like to log this in the team Canvas?"
            }
        },
        {
            "type": "actions",
            "block_id": "recorder_confirm_actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "confirm_log",
                    "text": {
                        "type": "plain_text",
                        "text": "✓ Log"
                    },
                    "style": "primary",
                    "value": payload_value
                },
                {
                    "type": "button",
                    "action_id": "dismiss_log",
                    "text": {
                        "type": "plain_text",
                        "text": "✗ Dismiss"
                    },
                    "style": "danger",
                    "value": payload_value
                }
            ]
        }
    ]

def get_logged_success_blocks(user_id: str, category: str) -> list[dict]:
    """
    Generates Block Kit blocks replacing the interactive buttons with a success message.
    """
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"✅ *Logged!* The {category} has been successfully saved to the Canvas."
            }
        }
    ]

def get_dismissed_blocks() -> list[dict]:
    """
    Generates Block Kit blocks replacing the prompt with a dismissal message.
    """
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🔕 *Dismissed.* This was not logged."
            }
        }
    ]

def get_nudge_blocks(owner_id: str, commitment_permalink: str, payload_value: str) -> list[dict]:
    """
    Generates Block Kit blocks for the private DM follow-up nudge.
    """
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"👋 Hey <@{owner_id}>, I couldn't find evidence of your commitment in the thread. Did you finish this?\n<{commitment_permalink}|View original commitment>"
            }
        },
        {
            "type": "actions",
            "block_id": "recorder_nudge_actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "commitment_done",
                    "text": {
                        "type": "plain_text",
                        "text": "✓ Done"
                    },
                    "style": "primary",
                    "value": payload_value
                },
                {
                    "type": "button",
                    "action_id": "commitment_snooze",
                    "text": {
                        "type": "plain_text",
                        "text": "↺ Snooze 24h"
                    },
                    "value": payload_value
                }
            ]
        }
    ]

def get_nudge_completed_blocks() -> list[dict]:
    """
    Blocks replacing the nudge prompt when user marks it as done.
    """
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "✅ *Great job!* I've marked this commitment as kept in the Canvas."
            }
        }
    ]

def get_nudge_snoozed_blocks() -> list[dict]:
    """
    Blocks replacing the nudge prompt when user snoozes it.
    """
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "⏳ *Snoozed.* I will follow up again in 24 hours."
            }
        }
    ]

