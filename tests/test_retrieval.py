from handlers.retrieval import extract_why_query


def test_extract_why_query():
    assert extract_why_query("<@U123> why did we pick Postgres?") == "why did we pick Postgres?"
    assert extract_why_query("<@U123> hello there") is None
    assert extract_why_query("<@U123> WHY is this blocked") == "WHY is this blocked"


if __name__ == "__main__":
    test_extract_why_query()
    print("OK")
