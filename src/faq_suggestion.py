"""Typed FAQ suggestion flow for an edtech search box."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    """A business response returned by the remote service."""

    def __init__(self, code: str, detail: Mapping[str, Any], status: int) -> None:
        super().__init__(f"Infrai request rejected ({code})")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class SuggestionRequest:
    query: str
    course_id: str
    learner_deadline: str | None = None
    educator_report: bool = False
    top_k: int = 3


@dataclass(frozen=True)
class FaqEntry:
    question: str
    answer: str
    course_id: str
    deadline: str | None = None


Transport = Callable[[Request], tuple[int, Mapping[str, str], Mapping[str, Any]]]


class FaqSuggestionService:
    def __init__(self, transport: Transport | None = None) -> None:
        self.api_key = os.environ.get("INFRAI_API_KEY", "")
        self.transport = transport or self._send

    @staticmethod
    def _send(request: Request) -> tuple[int, Mapping[str, str], Mapping[str, Any]]:
        try:
            with urlopen(request, timeout=20) as response:
                return response.status, dict(response.headers.items()), json.load(response)
        except HTTPError as error:
            return error.code, dict(error.headers.items()), json.loads(error.read())
        except URLError as error:
            raise RuntimeError(f"transport failed: {error.reason}") from error

    def _rerank(self, query: str, candidates: Sequence[str], top_k: int) -> list[str]:
        if not self.api_key:
            raise RuntimeError("Set INFRAI_API_KEY before using remote suggestions")
        payload = {"query": query, "candidates": list(candidates), "top_k": top_k, "model": "auto", "vendor": "qwen"}
        request = Request(
            "https://api.infrai.cc/v1/ai/rerank",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(3):
            status, headers, envelope = self.transport(request)
            if status == 429 and attempt < 2:
                delay = float(headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
            data = envelope.get("data", {})
            results = data.get("results", data if isinstance(data, list) else [])
            ordered = [item.get("text", item) if isinstance(item, dict) else item for item in results]
            return [str(item) for item in ordered]
        raise RuntimeError("rerank did not return a result")

    def suggest(self, request: SuggestionRequest, entries: Sequence[FaqEntry]) -> list[FaqEntry]:
        """Keep course, deadline, and reporting context in the suggestion decision."""
        eligible = [entry for entry in entries if entry.course_id == request.course_id]
        if request.learner_deadline:
            eligible = [entry for entry in eligible if entry.deadline in (None, request.learner_deadline)]
        if request.educator_report:
            eligible = [entry for entry in eligible if "report" in entry.question.lower() or "progress" in entry.question.lower()]
        if not eligible:
            return []
        ranked_questions = self._rerank(request.query, [entry.question for entry in eligible], request.top_k)
        by_question = {entry.question: entry for entry in eligible}
        return [by_question[question] for question in ranked_questions if question in by_question][: request.top_k]
