from aiapp.knowledge.base import Hit
from aiapp.knowledge.citations import verify_citations

HITS = [
    Hit("refund-policy#0", "refund-policy", 1, "Eligibility", 0, 10, "Unopened items can be refunded within 14 days of delivery. Opened items qualify for store credit only.", 0.9),
    Hit("shipping#3", "shipping", 1, "International", 0, 10, "International shipping adds 3 to 7 business days.", 0.5),
]


def test_good_citations_pass() -> None:
    answer = "Unopened items can be refunded within 14 days of delivery [refund-policy@v1#0]. International shipping adds 3 to 7 business days [shipping@v1#3]."
    report = verify_citations(answer, HITS)
    assert report.ok and report.cited == ["refund-policy@v1#0", "shipping@v1#3"]


def test_made_up_and_unsupported_citations_are_flagged() -> None:
    answer = "Refunds are processed within 24 hours [shipping@v1#3]. Unopened items can be refunded within 14 days [warranty@v1#9]."
    report = verify_citations(answer, HITS)
    assert not report.ok
    assert any("does not support" in p for p in report.problems)
    assert any("never retrieved" in p for p in report.problems)


def test_sources_without_any_citation_is_a_problem_and_no_sources_is_fine() -> None:
    assert not verify_citations("Sure, 14 days.", HITS).ok
    assert verify_citations("Hello!", []).ok


def test_accepts_a_plain_mapping_as_rebuilt_from_tool_results() -> None:
    report = verify_citations("Free over 50 [shipping@v1#0].", {"shipping@v1#0": "Standard delivery is free for orders over 50."})
    assert report.ok
