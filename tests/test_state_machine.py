"""Tests for state_machine — determines harness state from .claude-state/ files."""

import tempfile
from pathlib import Path

import pytest

from harness.state_machine import HarnessState, StateMachine


@pytest.fixture
def project_dir():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / ".claude-state").mkdir()
        (p / "docs").mkdir()
        yield p


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestDetermineState:
    def test_needs_requirements_when_no_file(self, project_dir: Path):
        sm = StateMachine(project_dir)
        assert sm.determine_state() == HarnessState.NEEDS_REQUIREMENTS

    def test_needs_requirements_when_empty(self, project_dir: Path):
        _write(project_dir / "docs" / "requirement.md", "# Title\n\n")
        sm = StateMachine(project_dir)
        assert sm.determine_state() == HarnessState.NEEDS_REQUIREMENTS

    def test_needs_planning_when_no_contract(self, project_dir: Path):
        _write(project_dir / "docs" / "requirement.md", "Build a todo app\n")
        sm = StateMachine(project_dir)
        assert sm.determine_state() == HarnessState.NEEDS_PLANNING

    def test_needs_planning_when_status_none(self, project_dir: Path):
        _write(project_dir / "docs" / "requirement.md", "Build a todo app\n")
        _write(project_dir / ".claude-state" / "sprint-contract.md", "status: none\n")
        sm = StateMachine(project_dir)
        assert sm.determine_state() == HarnessState.NEEDS_PLANNING

    def test_sprint_draft_first(self, project_dir: Path):
        _write(project_dir / "docs" / "requirement.md", "Build a todo app\n")
        _write(
            project_dir / ".claude-state" / "sprint-contract.md",
            "status: draft\nsprint_number: 1\n",
        )
        sm = StateMachine(project_dir)
        assert sm.determine_state() == HarnessState.SPRINT_DRAFT_FIRST

    def test_sprint_draft_auto_for_second_sprint(self, project_dir: Path):
        _write(project_dir / "docs" / "requirement.md", "Build a todo app\n")
        _write(
            project_dir / ".claude-state" / "sprint-contract.md",
            "status: draft\nsprint_number: 3\n",
        )
        sm = StateMachine(project_dir)
        assert sm.determine_state() == HarnessState.SPRINT_DRAFT_AUTO

    def test_sprint_approved(self, project_dir: Path):
        _write(project_dir / "docs" / "requirement.md", "Build a todo app\n")
        _write(
            project_dir / ".claude-state" / "sprint-contract.md",
            "status: approved\nsprint_number: 1\n",
        )
        sm = StateMachine(project_dir)
        assert sm.determine_state() == HarnessState.SPRINT_APPROVED

    def test_needs_evaluation(self, project_dir: Path):
        _write(project_dir / "docs" / "requirement.md", "Build a todo app\n")
        _write(
            project_dir / ".claude-state" / "sprint-contract.md",
            "status: implemented\n",
        )
        _write(project_dir / ".claude-state" / "evaluation-report.md", "status: none\n")
        sm = StateMachine(project_dir)
        assert sm.determine_state() == HarnessState.NEEDS_EVALUATION

    def test_eval_failed_retryable(self, project_dir: Path):
        _write(project_dir / "docs" / "requirement.md", "Build a todo app\n")
        _write(
            project_dir / ".claude-state" / "sprint-contract.md",
            "status: implemented\nfix_attempt: 1\n",
        )
        _write(project_dir / ".claude-state" / "evaluation-report.md", "status: fail\n")
        sm = StateMachine(project_dir)
        assert sm.determine_state() == HarnessState.EVAL_FAILED_RETRYABLE

    def test_eval_failed_blocked(self, project_dir: Path):
        _write(project_dir / "docs" / "requirement.md", "Build a todo app\n")
        _write(
            project_dir / ".claude-state" / "sprint-contract.md",
            "status: implemented\nfix_attempt: 2\n",
        )
        _write(project_dir / ".claude-state" / "evaluation-report.md", "status: fail\n")
        sm = StateMachine(project_dir)
        assert sm.determine_state() == HarnessState.EVAL_FAILED_BLOCKED

    def test_needs_review(self, project_dir: Path):
        _write(project_dir / "docs" / "requirement.md", "Build a todo app\n")
        _write(
            project_dir / ".claude-state" / "sprint-contract.md",
            "status: implemented\n",
        )
        _write(project_dir / ".claude-state" / "evaluation-report.md", "status: pass\n")
        _write(project_dir / ".claude-state" / "review-notes.md", "status: none\n")
        sm = StateMachine(project_dir)
        assert sm.determine_state() == HarnessState.NEEDS_REVIEW

    def test_needs_retrospective(self, project_dir: Path):
        _write(project_dir / "docs" / "requirement.md", "Build a todo app\n")
        _write(
            project_dir / ".claude-state" / "sprint-contract.md",
            "status: implemented\n",
        )
        _write(project_dir / ".claude-state" / "evaluation-report.md", "status: pass\n")
        _write(
            project_dir / ".claude-state" / "review-notes.md", "status: reviewed\n"
        )
        _write(project_dir / ".claude-state" / "learnings.md", "status: none\n")
        sm = StateMachine(project_dir)
        assert sm.determine_state() == HarnessState.NEEDS_RETROSPECTIVE

    def test_next_sprint(self, project_dir: Path):
        _write(project_dir / "docs" / "requirement.md", "Build a todo app\n")
        _write(
            project_dir / ".claude-state" / "sprint-contract.md",
            "status: implemented\n",
        )
        _write(project_dir / ".claude-state" / "evaluation-report.md", "status: pass\n")
        _write(
            project_dir / ".claude-state" / "review-notes.md", "status: reviewed\n"
        )
        _write(project_dir / ".claude-state" / "learnings.md", "status: active\n")
        _write(
            project_dir / ".claude-state" / "claude-progress.txt",
            "remaining_sprints: true\n",
        )
        sm = StateMachine(project_dir)
        assert sm.determine_state() == HarnessState.NEXT_SPRINT

    def test_suggest_improve(self, project_dir: Path):
        _write(project_dir / "docs" / "requirement.md", "Build a todo app\n")
        _write(
            project_dir / ".claude-state" / "sprint-contract.md",
            "status: implemented\n",
        )
        _write(project_dir / ".claude-state" / "evaluation-report.md", "status: pass\n")
        _write(
            project_dir / ".claude-state" / "review-notes.md", "status: reviewed\n"
        )
        _write(
            project_dir / ".claude-state" / "learnings.md",
            "status: active\nimprove_needed: true\n",
        )
        _write(
            project_dir / ".claude-state" / "claude-progress.txt",
            "remaining_sprints: false\n",
        )
        sm = StateMachine(project_dir)
        assert sm.determine_state() == HarnessState.SUGGEST_IMPROVE

    def test_all_complete(self, project_dir: Path):
        _write(project_dir / "docs" / "requirement.md", "Build a todo app\n")
        _write(
            project_dir / ".claude-state" / "sprint-contract.md",
            "status: implemented\n",
        )
        _write(project_dir / ".claude-state" / "evaluation-report.md", "status: pass\n")
        _write(
            project_dir / ".claude-state" / "review-notes.md", "status: reviewed\n"
        )
        _write(
            project_dir / ".claude-state" / "learnings.md",
            "status: active\nimprove_needed: false\n",
        )
        _write(
            project_dir / ".claude-state" / "claude-progress.txt",
            "remaining_sprints: false\n",
        )
        sm = StateMachine(project_dir)
        assert sm.determine_state() == HarnessState.ALL_COMPLETE


class TestGetNextAgent:
    def test_maps_states_to_agents(self, project_dir: Path):
        sm = StateMachine(project_dir)
        assert sm.get_next_agent(HarnessState.NEEDS_REQUIREMENTS) == "requirement-writer"
        assert sm.get_next_agent(HarnessState.NEEDS_PLANNING) == "planner"
        assert sm.get_next_agent(HarnessState.SPRINT_APPROVED) == "sprint-builder"
        assert sm.get_next_agent(HarnessState.NEEDS_EVALUATION) == "evaluator"
        assert sm.get_next_agent(HarnessState.EVAL_FAILED_RETRYABLE) == "integration-fixer"
        assert sm.get_next_agent(HarnessState.NEEDS_REVIEW) == "reviewer"
        assert sm.get_next_agent(HarnessState.NEEDS_RETROSPECTIVE) == "retrospective"
        assert sm.get_next_agent(HarnessState.NEXT_SPRINT) == "planner"

    def test_returns_none_for_terminal_states(self, project_dir: Path):
        sm = StateMachine(project_dir)
        assert sm.get_next_agent(HarnessState.ALL_COMPLETE) is None
        assert sm.get_next_agent(HarnessState.BLOCKED) is None
        assert sm.get_next_agent(HarnessState.EVAL_FAILED_BLOCKED) is None

    def test_returns_none_for_user_action_states(self, project_dir: Path):
        sm = StateMachine(project_dir)
        assert sm.get_next_agent(HarnessState.SPRINT_DRAFT_FIRST) is None
        assert sm.get_next_agent(HarnessState.SUGGEST_IMPROVE) is None
