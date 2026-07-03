from typing import Optional, TypedDict
from ai.schemas import ClassificationResult

class ClassifierState(TypedDict):
    """
    GraphState representing the state dictionary passing through the classifier workflow.
    """
    message_text: str
    sender_id: str
    result: Optional[ClassificationResult]
