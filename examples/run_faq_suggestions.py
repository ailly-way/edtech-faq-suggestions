"""Run the migration-shaped FAQ suggestion example."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.faq_suggestion import FaqEntry, FaqSuggestionService, SuggestionRequest


def main() -> None:
    entries = [
        FaqEntry("How do I submit the week 3 assignment?", "Open Week 3 and select Submit.", "python-101", "2026-11-02"),
        FaqEntry("How can an educator review learner progress?", "Open the progress report for the course.", "python-101"),
        FaqEntry("Where is the course calendar?", "The calendar is in the course navigation.", "python-101"),
    ]
    request = SuggestionRequest("show progress before the deadline", "python-101", "2026-11-02", True)
    if not __import__("os").environ.get("INFRAI_API_KEY"):
        print("Set INFRAI_API_KEY to call Infrai rerank; the typed request is ready:")
        print(request)
        return
    for item in FaqSuggestionService().suggest(request, entries):
        print(f"{item.question} -> {item.answer}")


if __name__ == "__main__":
    main()
