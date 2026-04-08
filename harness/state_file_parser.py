"""Parses .claude-state/ files to extract status fields for the state machine."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SprintContractInfo:
    status: str | None = None
    sprint_number: int | None = None
    fix_attempt: int = 0
    profile: str | None = None


@dataclass
class EvaluationReportInfo:
    status: str = "none"


@dataclass
class ReviewNotesInfo:
    status: str = "none"


@dataclass
class LearningsInfo:
    status: str = "none"
    improve_needed: bool | None = None


@dataclass
class ProgressInfo:
    remaining_sprints: bool = False


def _extract_field(text: str, field_name: str) -> str | None:
    """Extract a simple `field: value` from markdown/text content."""
    pattern = rf"^{re.escape(field_name)}:\s*(.+)$"
    match = re.search(pattern, text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


class StateFileParser:
    """Reads and parses .claude-state/ files."""

    def __init__(self, state_dir: str | Path) -> None:
        self.state_dir = Path(state_dir)

    def _read_file(self, filename: str) -> str | None:
        path = self.state_dir / filename
        if path.is_file():
            return path.read_text(encoding="utf-8")
        return None

    def parse_sprint_contract(self) -> SprintContractInfo:
        text = self._read_file("sprint-contract.md")
        if text is None:
            return SprintContractInfo()

        info = SprintContractInfo()
        info.status = _extract_field(text, "status")

        sprint_num = _extract_field(text, "sprint_number")
        if sprint_num is not None:
            try:
                info.sprint_number = int(sprint_num)
            except ValueError:
                pass

        fix_attempt = _extract_field(text, "fix_attempt")
        if fix_attempt is not None:
            try:
                info.fix_attempt = int(fix_attempt)
            except ValueError:
                pass

        info.profile = _extract_field(text, "profile")
        return info

    def parse_evaluation_report(self) -> EvaluationReportInfo:
        text = self._read_file("evaluation-report.md")
        if text is None:
            return EvaluationReportInfo()
        status = _extract_field(text, "status")
        return EvaluationReportInfo(status=status or "none")

    def parse_review_notes(self) -> ReviewNotesInfo:
        text = self._read_file("review-notes.md")
        if text is None:
            return ReviewNotesInfo()
        status = _extract_field(text, "status")
        return ReviewNotesInfo(status=status or "none")

    def parse_learnings(self) -> LearningsInfo:
        text = self._read_file("learnings.md")
        if text is None:
            return LearningsInfo()
        status = _extract_field(text, "status")
        improve = _extract_field(text, "improve_needed")
        improve_needed = None
        if improve is not None:
            improve_needed = improve.lower() == "true"
        return LearningsInfo(status=status or "none", improve_needed=improve_needed)

    def parse_progress(self) -> ProgressInfo:
        text = self._read_file("claude-progress.txt")
        if text is None:
            return ProgressInfo()
        remaining = _extract_field(text, "remaining_sprints")
        return ProgressInfo(
            remaining_sprints=(remaining is not None and remaining.lower() == "true")
        )

    def is_requirement_empty(self, req_path: Path) -> bool:
        """Check if requirement file is empty or contains only comments/whitespace."""
        if not req_path.is_file():
            return True
        text = req_path.read_text(encoding="utf-8")
        if not text.strip():
            return True
        # Filter out lines that are blank or start with #
        content_lines = [
            line
            for line in text.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        return len(content_lines) == 0
