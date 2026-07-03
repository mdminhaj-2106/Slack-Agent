from typing import Optional
from pydantic import BaseModel, Field

class PointerRecord(BaseModel):
    """
    PointerRecord defines the schema for a captured decision or commitment.
    This stores only pointers/metadata and strictly excludes raw message content.
    """
    channel_id: str = Field(description="Slack channel ID where the message originated")
    ts: str = Field(description="Slack message timestamp")
    permalink: str = Field(description="Permalink to the Slack message")
    type: str = Field(description="Type of pointer: 'decision' or 'commitment'")
    owner_id: str = Field(description="Slack User ID of the decision maker or commitment owner")
    confidence: float = Field(description="Confidence score of classification")
    status: str = Field(default="logged", description="Status: 'logged' (for decisions) or 'open' (for commitments)")
