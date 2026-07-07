import logging
from typing import List, Dict
from pydantic import BaseModel, Field
from ai.llm import get_llm

logger = logging.getLogger("recorder.ai.nli")

class NLIVerdict(BaseModel):
    """
    Structured outcome of the commitment entailment verification check.
    """
    verdict: str = Field(
        description="One of: 'kept' (completed), 'superseded' (canceled/replaced), or 'insufficient_evidence'"
    )
    reasoning_tag: str = Field(
        description="One of: 'done_message', 'reaction_signal', 'contradiction', or 'no_signal'"
    )
    explanation: str = Field(
        description="Brief sentence explaining why this verdict was chosen based on the evidence."
    )

SYSTEM_PROMPT = """
You are a commitment verifier for an engineering team.
Given a specific original commitment statement and a set of later message replies and emoji reactions from the same thread,
evaluate whether the commitment has been fulfilled.

Classify the commitment into one of the following verdicts:
1. 'kept': The evidence (later messages or reactions) clearly indicates the task was completed (e.g. "done", "fixed", "merged", "shipped", "deployed", or checkmark reactions).
2. 'superseded': A later message explicitly indicates the commitment was cancelled, rejected, or replaced (e.g. "don't do this anymore", "we changed plans", "cancelled").
3. 'insufficient_evidence': There is no clear signal of completion or cancellation in the provided thread replies or reactions.

Rules:
- A checkmark reaction (e.g., 'white_check_mark', '✅') on the original message is a strong 'kept' signal (reaction_signal) unless contradicted in the thread replies.
- Do not infer completion from casual chatter. Be conservative. If in doubt, return 'insufficient_evidence'.
- reasoning_tag mapping:
  - 'done_message' if a reply message signals completion.
  - 'reaction_signal' if an emoji reaction signals completion.
  - 'contradiction' if a reply message contradicts/cancels the commitment.
  - 'no_signal' if there is no evidence.
"""

def evaluate_commitment(commitment_permalink: str, commitment_text: str, evidence: Dict) -> NLIVerdict:
    """
    Uses Gemini structured output to run Natural Language Inference (NLI) on the evidence
    against the original commitment text. Never persists raw text.
    """
    # 1. Quick check: if checkmark reaction exists, we can shortcut to 'kept' with 'reaction_signal'
    done_reactions = evidence.get("done_reactions", [])
    if done_reactions:
        logger.info(f"Verified via direct emoji reaction signal: {done_reactions}")
        return NLIVerdict(
            verdict="kept",
            reasoning_tag="reaction_signal",
            explanation=f"Owner marked completion with reactions: {', '.join(done_reactions)}"
        )

    thread_replies = evidence.get("thread_replies", [])
    if not thread_replies:
        logger.info("No thread replies or reaction evidence. Defaulting to insufficient_evidence.")
        return NLIVerdict(
            verdict="insufficient_evidence",
            reasoning_tag="no_signal",
            explanation="No replies or reactions were posted to verify completion."
        )

    # 2. Invoke Gemini LLM for semantic evaluation
    try:
        llm = get_llm(temperature=0.0)
        structured_llm = llm.with_structured_output(NLIVerdict)
        
        # Format the replies for LLM consumption
        evidence_text = "\n".join([
            f"- @{msg['user']}: {msg['text']}" for msg in thread_replies
        ])
        
        prompt = f"""
Commitment Permalink: {commitment_permalink}
Stated Commitment: "{commitment_text}"

Later Thread Replies (Evidence):
{evidence_text}
"""
        logger.info(f"Invoking NLI evaluation for commitment: '{commitment_text[:40]}...'")
        result = structured_llm.invoke([
            ("system", SYSTEM_PROMPT),
            ("human", prompt)
        ])
        
        logger.info(f"Gemini NLI evaluation returned verdict: {result.verdict} ({result.reasoning_tag})")
        return result
        
    except Exception as e:
        logger.error(f"Error during NLI evaluation execution: {e}")
        return NLIVerdict(
            verdict="insufficient_evidence",
            reasoning_tag="no_signal",
            explanation="Failed to evaluate evidence due to internal LLM execution error."
        )
