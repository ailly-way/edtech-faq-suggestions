from src.faq_suggestion import FaqEntry, FaqSuggestionService, SuggestionRequest


def test_reporting_request_keeps_course_and_deadline_context() -> None:
    calls = []

    def fake_transport(request):
        calls.append(request)
        return 200, {}, {"ok": True, "data": {"results": [{"text": "How can an educator review learner progress?"}]}}

    entries = [
        FaqEntry("How can an educator review learner progress?", "Use the report.", "python-101"),
        FaqEntry("How do I submit the week 3 assignment?", "Select Submit.", "python-101", "2026-11-02"),
        FaqEntry("How can an educator review learner progress?", "Other course.", "history-101"),
    ]
    result = FaqSuggestionService(fake_transport).suggest(
        SuggestionRequest("progress report", "python-101", "2026-11-02", True), entries
    )
    assert [item.answer for item in result] == ["Use the report."]
    assert calls[0].method == "POST"
