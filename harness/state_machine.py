"""State machine that mirrors session-start.sh logic in Python.

Determines the current harness state from .claude-state/ files and maps it to
the next agent that should run.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from harness.state_file_parser import StateFileParser


class HarnessState(Enum):
    NEEDS_REQUIREMENTS = "needs_requirements"
    NEEDS_PLANNING = "needs_planning"
    SPRINT_DRAFT_FIRST = "sprint_draft_first"
    SPRINT_DRAFT_AUTO = "sprint_draft_auto"
    SPRINT_APPROVED = "sprint_approved"
    NEEDS_EVALUATION = "needs_evaluation"
    EVAL_FAILED_RETRYABLE = "eval_failed_retry"
    EVAL_FAILED_BLOCKED = "eval_failed_blocked"
    NEEDS_REVIEW = "needs_review"
    NEEDS_RETROSPECTIVE = "needs_retro"
    NEXT_SPRINT = "next_sprint"
    ALL_COMPLETE = "all_complete"
    SUGGEST_IMPROVE = "suggest_improve"
    BLOCKED = "blocked"


_STATE_TO_AGENT: dict[HarnessState, str] = {
    HarnessState.NEEDS_REQUIREMENTS: "requirement-writer",
    HarnessState.NEEDS_PLANNING: "planner",
    HarnessState.SPRINT_APPROVED: "sprint-builder",
    HarnessState.SPRINT_DRAFT_AUTO: "sprint-builder",
    HarnessState.NEEDS_EVALUATION: "evaluator",
    HarnessState.EVAL_FAILED_RETRYABLE: "integration-fixer",
    HarnessState.NEEDS_REVIEW: "reviewer",
    HarnessState.NEEDS_RETROSPECTIVE: "retrospective",
    HarnessState.NEXT_SPRINT: "planner",
}


class StateMachine:
    """Determines harness state by inspecting .claude-state/ files."""

    def __init__(self, project_dir: str | Path) -> None:
        self.project_dir = Path(project_dir)
        self.state_dir = self.project_dir / ".claude-state"
        self.parser = StateFileParser(self.state_dir)

    def determine_state(self) -> HarnessState:
        """Inspect state files and return the current harness state."""
        req_path = self.project_dir / "docs" / "requirement.md"
        if self.parser.is_requirement_empty(req_path):
            return HarnessState.NEEDS_REQUIREMENTS

        contract = self.parser.parse_sprint_contract()

        if contract.status is None or contract.status == "none":
            return HarnessState.NEEDS_PLANNING

        if contract.status == "draft":
            if contract.sprint_number is None or contract.sprint_number <= 1:
                return HarnessState.SPRINT_DRAFT_FIRST
            return HarnessState.SPRINT_DRAFT_AUTO

        if contract.status == "approved":
            return HarnessState.SPRINT_APPROVED

        if contract.status == "implemented":
            return self._evaluate_post_implementation(contract.fix_attempt)

        return HarnessState.BLOCKED

    def _evaluate_post_implementation(self, fix_attempt: int) -> HarnessState:
        eval_report = self.parser.parse_evaluation_report()

        if eval_report.status == "none":
            return HarnessState.NEEDS_EVALUATION

        if eval_report.status == "fail":
            if fix_attempt >= 2:
                return HarnessState.EVAL_FAILED_BLOCKED
            return HarnessState.EVAL_FAILED_RETRYABLE

        if eval_report.status == "pass":
            return self._evaluate_post_evaluation()

        return HarnessState.BLOCKED

    def _evaluate_post_evaluation(self) -> HarnessState:
        review = self.parser.parse_review_notes()

        if review.status == "none":
            return HarnessState.NEEDS_REVIEW

        learnings = self.parser.parse_learnings()

        if learnings.status == "none":
            return HarnessState.NEEDS_RETROSPECTIVE

        progress = self.parser.parse_progress()

        if progress.remaining_sprints:
            return HarnessState.NEXT_SPRINT

        if learnings.improve_needed:
            return HarnessState.SUGGEST_IMPROVE

        return HarnessState.ALL_COMPLETE

    def get_next_agent(self, state: HarnessState) -> str | None:
        """Return the agent name to run for the given state, or None."""
        return _STATE_TO_AGENT.get(state)
