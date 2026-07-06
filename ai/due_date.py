import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import dateparser

logger = logging.getLogger("recorder.ai.due_date")

def parse_due_datetime(hint: Optional[str], fallback_hours: int = 24) -> datetime:
    """
    Converts a free-text due hint ("by Friday", "tomorrow EOD") to a timezone-aware datetime.
    Falls back to now + fallback_hours if dateparser cannot parse the hint or if it is None.
    If the parsed datetime is in the past, it falls back to the future fallback (to prevent immediate firing).
    """
    now_utc = datetime.now(timezone.utc)
    fallback_dt = now_utc + timedelta(hours=fallback_hours)
    
    if not hint:
        logger.info(f"No due date hint provided. Using fallback of +{fallback_hours}h: {fallback_dt}")
        return fallback_dt

    try:
        # Parse hint preferring future dates and timezone-aware
        parsed_dt = dateparser.parse(
            hint,
            settings={
                "PREFER_DATES_FROM": "future",
                "RETURN_AS_TIMEZONE_AWARE": True,
                "TIMEZONE": "UTC"
            }
        )
        if parsed_dt:
            # Ensure it is timezone-aware in UTC
            if parsed_dt.tzinfo is None:
                parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
            else:
                parsed_dt = parsed_dt.astimezone(timezone.utc)
            
            # If the parsed date is in the past relative to now, push to fallback
            if parsed_dt <= now_utc:
                logger.warning(f"Parsed datetime {parsed_dt} is in the past. Using fallback: {fallback_dt}")
                return fallback_dt
                
            logger.info(f"Parsed due date hint '{hint}' successfully to: {parsed_dt}")
            return parsed_dt
            
    except Exception as e:
        logger.error(f"Error parsing due date hint '{hint}': {e}")
        
    logger.info(f"Failed to parse hint '{hint}'. Using fallback: {fallback_dt}")
    return fallback_dt
