"""Tests for state_file_parser — parses .claude-state/ files."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from harness.state_file_parser import StateFileParser


@pytest.fixture
def state_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestParseSprintContract:
    def test_returns_none_status_for_initial_contract(self, state_dir: Path):
        contract = state_dir / "sprint-contract.md"
        contract.write_text("# Sprint Contract\n\nstatus: none\nfix_attempt: 0\n")
        parser = StateFileParser(state_dir)
        result = parser.parse_sprint_contract()
        assert result.status == "none"
        assert result.fix_attempt == 0
        assert result.sprint_number is None

    def test_parses_draft_with_sprint_number(self, state_dir: Path):
        contract = state_dir / "sprint-contract.md"
        contract.write_text(
            "status: draft\nsprint_number: 2\nfix_attempt: 0\nprofile: nextjs\n"
        )
        parser = StateFileParser(state_dir)
        result = parser.parse_sprint_contract()
        assert result.status == "draft"
        assert result.sprint_number == 2
        assert result.profile == "nextjs"

    def test_parses_implemented_with_fix_attempt(self, state_dir: Path):
        contract = state_dir / "sprint-contract.md"
        contract.write_text("status: implemented\nfix_attempt: 2\nsprint_number: 1\n")
        parser = StateFileParser(state_dir)
        result = parser.parse_sprint_contract()
        assert result.status == "implemented"
        assert result.fix_attempt == 2

    def test_returns_defaults_when_file_missing(self, state_dir: Path):
        parser = StateFileParser(state_dir)
        result = parser.parse_sprint_contract()
        assert result.status is None
        assert result.fix_attempt == 0


class TestParseEvaluationReport:
    def test_parses_status(self, state_dir: Path):
        report = state_dir / "evaluation-report.md"
        report.write_text("status: pass\n")
        parser = StateFileParser(state_dir)
        assert parser.parse_evaluation_report().status == "pass"

    def test_parses_fail_status(self, state_dir: Path):
        report = state_dir / "evaluation-report.md"
        report.write_text("status: fail\n\n## Blocker\n- build error\n- type error\n")
        parser = StateFileParser(state_dir)
        result = parser.parse_evaluation_report()
        assert result.status == "fail"

    def test_returns_none_when_missing(self, state_dir: Path):
        parser = StateFileParser(state_dir)
        assert parser.parse_evaluation_report().status == "none"


class TestParseReviewNotes:
    def test_parses_reviewed(self, state_dir: Path):
        notes = state_dir / "review-notes.md"
        notes.write_text("status: reviewed\n")
        parser = StateFileParser(state_dir)
        assert parser.parse_review_notes().status == "reviewed"

    def test_returns_none_when_missing(self, state_dir: Path):
        parser = StateFileParser(state_dir)
        assert parser.parse_review_notes().status == "none"


class TestParseLearnings:
    def test_parses_active_with_improve_needed(self, state_dir: Path):
        learnings = state_dir / "learnings.md"
        learnings.write_text("status: active\nimprove_needed: true\n")
        parser = StateFileParser(state_dir)
        result = parser.parse_learnings()
        assert result.status == "active"
        assert result.improve_needed is True

    def test_parses_false_improve_needed(self, state_dir: Path):
        learnings = state_dir / "learnings.md"
        learnings.write_text("status: active\nimprove_needed: false\n")
        parser = StateFileParser(state_dir)
        result = parser.parse_learnings()
        assert result.improve_needed is False


class TestParseProgress:
    def test_parses_remaining_sprints(self, state_dir: Path):
        progress = state_dir / "claude-progress.txt"
        progress.write_text("## 상태\nremaining_sprints: true\n")
        parser = StateFileParser(state_dir)
        result = parser.parse_progress()
        assert result.remaining_sprints is True

    def test_defaults_remaining_sprints_false(self, state_dir: Path):
        progress = state_dir / "claude-progress.txt"
        progress.write_text("## 상태\nsome content\n")
        parser = StateFileParser(state_dir)
        result = parser.parse_progress()
        assert result.remaining_sprints is False


class TestIsRequirementEmpty:
    def test_empty_file(self, state_dir: Path):
        req = state_dir / "requirement.md"
        req.write_text("")
        parser = StateFileParser(state_dir)
        assert parser.is_requirement_empty(req) is True

    def test_only_comments_and_whitespace(self, state_dir: Path):
        req = state_dir / "requirement.md"
        req.write_text("# Title\n\n# Section\n\n")
        parser = StateFileParser(state_dir)
        assert parser.is_requirement_empty(req) is True

    def test_has_content(self, state_dir: Path):
        req = state_dir / "requirement.md"
        req.write_text("# Title\n\nThis is a real requirement.\n")
        parser = StateFileParser(state_dir)
        assert parser.is_requirement_empty(req) is False

    def test_missing_file(self, state_dir: Path):
        parser = StateFileParser(state_dir)
        assert parser.is_requirement_empty(state_dir / "nonexistent.md") is True
