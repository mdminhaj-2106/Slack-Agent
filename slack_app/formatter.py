from slack_app.schemas import PointerRecord

def format_pointer_as_markdown(pointer: PointerRecord) -> str:
    """
    Formats a PointerRecord into a standardized, evidence-only markdown string
    suitable for appending to a Slack Canvas.
    
    Uses Canvas-specific user mention syntax: ![](@USER_ID)
    """
    user_mention = f"![](@{pointer.owner_id})"
    type_formatted = pointer.type.capitalize()
    
    # Example format:
    # • ![](@U12345) | *Decision* (Conf: 0.95) | Status: `logged` | Channel: C0123 | TS: 1234.5678 | Link: <https://slack.com/archives/...>
    return (
        f"• {user_mention} | *{type_formatted}* (Conf: {pointer.confidence:.2f}) | "
        f"Status: `{pointer.status}` | Channel: `{pointer.channel_id}` | TS: `{pointer.ts}` | "
        f"Link: <{pointer.permalink}>\n"
    )
