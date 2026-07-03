from typing import Optional
from pydantic import BaseModel, Field

class ClassificationResult(BaseModel):
    """
    Schema representing the structured classification output.
    """
    category: str = Field(description="Must be 'decision', 'commitment', or 'none'")
    confidence: float = Field(description="Confidence score of this classification from 0.0 to 1.0")
    owner_id: Optional[str] = Field(default=None, description="The Slack User ID of the decision maker or commitment owner (e.g. U12345)")
    due_date_hint: Optional[str] = Field(default=None, description="Optional text describing when a commitment is due (e.g. 'by Friday')")
