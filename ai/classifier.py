import logging
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from ai.llm import get_llm
from ai.state import ClassifierState
from ai.schemas import ClassificationResult

logger = logging.getLogger("recorder.ai.classifier")

# Prompt definition
SYSTEM_PROMPT = """
You are a decision and commitment classifier for a developer Slack team.
Analyze the provided message text and classify it into one of the following categories:
1. 'decision': A decision made by the team. Look for explicit phrases like "we decided to", "let's go with", "we will use", "agreed on", "final call".
2. 'commitment': A promise or task a specific person commits to do. Look for expressions like "I will do X", "I'll handle X", "<@U12345> will take care of X", "I commit to".
3. 'none': Generic conversation, greetings, questions, bug reports, and regular chatter.

Instructions for fields:
- category: Set to 'decision', 'commitment', or 'none'.
- confidence: Estimate your confidence score from 0.0 to 1.0.
- owner_id:
  - For commitments, identify who is committing. If it is a self-commitment ("I will do X"), set it to the provided sender_id.
  - If the text mentions another user (e.g. "<@U87654321> will take care of it"), extract that user's ID: "U87654321".
  - For decisions, default to the sender_id.
- due_date_hint: Extract any deadline or timeline cue (e.g. "by Friday", "tomorrow", "before EOD").
"""

def classify_message_node(state: ClassifierState) -> dict:
    """
    Graph node that invokes the Gemini model via the centralized LLM initializer.
    """
    try:
        # 1. Fetch unified LLM instance
        llm = get_llm(temperature=0.0)
        structured_llm = llm.with_structured_output(ClassificationResult)
        
        # 2. Build template prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "Sender Slack User ID: {sender_id}\nMessage text: {message_text}")
        ])
        
        # 3. Invoke LLM and extract response
        chain = prompt | structured_llm
        result = chain.invoke({
            "sender_id": state["sender_id"],
            "message_text": state["message_text"]
        })
        
        return {"result": result}
    except Exception as e:
        logger.error(f"Error during LLM classification node execution: {e}")
        return {"result": ClassificationResult(category="none", confidence=0.0)}

# Compile the LangGraph
workflow = StateGraph(ClassifierState)
workflow.add_node("classify", classify_message_node)
workflow.add_edge(START, "classify")
workflow.add_edge("classify", END)
classifier_graph = workflow.compile()

def classify_text(text: str, sender_id: str) -> Optional[ClassificationResult]:
    """
    Exposes the compiled StateGraph classification workflow.
    """
    try:
        inputs = {
            "message_text": text,
            "sender_id": sender_id,
            "result": None
        }
        outputs = classifier_graph.invoke(inputs)
        return outputs.get("result")
    except Exception as e:
        logger.error(f"Failed to execute classifier state graph: {e}")
        return None
