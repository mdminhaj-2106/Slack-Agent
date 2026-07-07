import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from ai.due_date import parse_due_datetime
from ai.nli import evaluate_commitment, NLIVerdict

class TestDueDatetimeParser(unittest.TestCase):
    def test_parse_due_datetime_none(self):
        # None should fallback to roughly now + 24h
        now_utc = datetime.now(timezone.utc)
        result = parse_due_datetime(None, fallback_hours=24)
        
        diff = result - now_utc
        self.assertAlmostEqual(diff.total_seconds(), 24 * 3600, delta=10)
        self.assertIsNotNone(result.tzinfo)

    def test_parse_due_datetime_tomorrow(self):
        now_utc = datetime.now(timezone.utc)
        result = parse_due_datetime("tomorrow", fallback_hours=24)
        
        diff = result - now_utc
        # "tomorrow" should parse to roughly 24h from now
        self.assertGreater(diff.total_seconds(), 0)
        self.assertLess(diff.total_seconds(), 36 * 3600)
        self.assertIsNotNone(result.tzinfo)

    def test_parse_due_datetime_past_hint(self):
        # A past hint should fallback to fallback_hours in future
        now_utc = datetime.now(timezone.utc)
        result = parse_due_datetime("yesterday", fallback_hours=12)
        
        diff = result - now_utc
        self.assertAlmostEqual(diff.total_seconds(), 12 * 3600, delta=10)

class TestNLIEvaluator(unittest.TestCase):
    def test_nli_kept_from_reaction(self):
        # If ✅ reaction is present, it should immediately return 'kept' (reaction_signal)
        evidence = {
            "thread_replies": [],
            "done_reactions": ["white_check_mark"]
        }
        res = evaluate_commitment(
            commitment_permalink="https://slack.com/...",
            commitment_text="I will set up the pipeline",
            evidence=evidence
        )
        self.assertEqual(res.verdict, "kept")
        self.assertEqual(res.reasoning_tag, "reaction_signal")

    def test_nli_insufficient_no_replies(self):
        # No replies or reactions -> insufficient_evidence
        evidence = {
            "thread_replies": [],
            "done_reactions": []
        }
        res = evaluate_commitment(
            commitment_permalink="https://slack.com/...",
            commitment_text="I will set up the pipeline",
            evidence=evidence
        )
        self.assertEqual(res.verdict, "insufficient_evidence")
        self.assertEqual(res.reasoning_tag, "no_signal")

    @patch("ai.nli.get_llm")
    def test_nli_kept_from_done_message(self, mock_get_llm):
        # Mock Gemini structured output to return kept
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_get_llm.return_value = mock_llm
        mock_llm.with_structured_output.return_value = mock_structured_llm
        
        expected_verdict = NLIVerdict(
            verdict="kept",
            reasoning_tag="done_message",
            explanation="User confirmed the task is completed in thread."
        )
        mock_structured_llm.invoke.return_value = expected_verdict
        
        evidence = {
            "thread_replies": [{"user": "U123", "text": "CI is green on main", "ts": "123.456"}],
            "done_reactions": []
        }
        res = evaluate_commitment(
            commitment_permalink="https://slack.com/...",
            commitment_text="I will set up the pipeline",
            evidence=evidence
        )
        self.assertEqual(res.verdict, "kept")
        self.assertEqual(res.reasoning_tag, "done_message")

    @patch("ai.nli.get_llm")
    def test_nli_superseded_from_cancel(self, mock_get_llm):
        # Mock Gemini structured output to return superseded
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_get_llm.return_value = mock_llm
        mock_llm.with_structured_output.return_value = mock_structured_llm
        
        expected_verdict = NLIVerdict(
            verdict="superseded",
            reasoning_tag="contradiction",
            explanation="The task was explicitly cancelled."
        )
        mock_structured_llm.invoke.return_value = expected_verdict
        
        evidence = {
            "thread_replies": [{"user": "U123", "text": "let's scratch this idea, cancelled", "ts": "123.456"}],
            "done_reactions": []
        }
        res = evaluate_commitment(
            commitment_permalink="https://slack.com/...",
            commitment_text="I will set up the pipeline",
            evidence=evidence
        )
        self.assertEqual(res.verdict, "superseded")
        self.assertEqual(res.reasoning_tag, "contradiction")

if __name__ == "__main__":
    unittest.main()
