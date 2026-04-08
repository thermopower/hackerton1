"""CLI entry point — `python -m harness run` or `harness run`."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from harness.agent_runner import AgentRunner
from harness.config import load_config
from harness.event_bus import EventBus
from harness.state_machine import HarnessState, StateMachine


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="harness",
        description="Multi-model AI coding harness orchestrator",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="harness.config.yaml",
        help="Path to config file (default: harness.config.yaml)",
    )
    parser.add_argument(
        "-d",
        "--project-dir",
        default=".",
        help="Project root directory (default: current directory)",
    )

    sub = parser.add_subparsers(dest="command")

    # harness status
    sub.add_parser("status", help="Show current harness state")

    # harness run
    run_p = sub.add_parser("run", help="Run next agent based on current state")
    run_p.add_argument(
        "--loop",
        action="store_true",
        help="Keep running agents until a user-action state or completion",
    )

    # harness start
    sub.add_parser(
        "start", help="Force restart from requirement-writer"
    )

    # harness agent <name>
    agent_p = sub.add_parser("agent", help="Run a specific agent directly")
    agent_p.add_argument("name", help="Agent name (e.g. planner, evaluator)")
    agent_p.add_argument(
        "-m", "--message", default="", help="Message to pass to the agent"
    )

    return parser


async def _cmd_status(sm: StateMachine) -> int:
    state = sm.determine_state()
    agent = sm.get_next_agent(state)

    print(f"State:      {state.value}")
    if agent:
        print(f"Next agent: {agent}")
    else:
        print(f"Next agent: (none — {_state_description(state)})")
    return 0


def _state_description(state: HarnessState) -> str:
    descriptions = {
        HarnessState.ALL_COMPLETE: "all sprints complete",
        HarnessState.BLOCKED: "blocked — user intervention needed",
        HarnessState.EVAL_FAILED_BLOCKED: "evaluation failed 2+ times — user decision needed",
        HarnessState.SPRINT_DRAFT_FIRST: "first sprint draft — awaiting user approval",
        HarnessState.SUGGEST_IMPROVE: "complete — /improve recommended",
    }
    return descriptions.get(state, state.value)


def _is_auto_state(state: HarnessState) -> bool:
    """Return True if the state can proceed without user input."""
    return state in {
        HarnessState.NEEDS_REQUIREMENTS,
        HarnessState.NEEDS_PLANNING,
        HarnessState.SPRINT_DRAFT_AUTO,
        HarnessState.SPRINT_APPROVED,
        HarnessState.NEEDS_EVALUATION,
        HarnessState.EVAL_FAILED_RETRYABLE,
        HarnessState.NEEDS_REVIEW,
        HarnessState.NEEDS_RETROSPECTIVE,
        HarnessState.NEXT_SPRINT,
    }


async def _cmd_run(
    sm: StateMachine, runner: AgentRunner, loop: bool = False
) -> int:
    while True:
        state = sm.determine_state()
        agent = sm.get_next_agent(state)

        if agent is None:
            print(f"State: {state.value} — {_state_description(state)}")
            return 0

        print(f"State: {state.value} → running '{agent}'")
        result = await runner.run(agent)

        if not result.success:
            print(f"Agent '{agent}' failed: {result.error or 'unknown error'}")
            return 1

        if not loop or not _is_auto_state(sm.determine_state()):
            new_state = sm.determine_state()
            print(f"Done. New state: {new_state.value}")
            return 0


async def _cmd_agent(runner: AgentRunner, name: str, message: str) -> int:
    print(f"Running agent '{name}' directly...")
    result = await runner.run(name, message=message)
    if result.success:
        print(f"Agent '{name}' completed successfully.")
        return 0
    else:
        print(f"Agent '{name}' failed: {result.error or 'unknown error'}")
        return 1


async def _async_main(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    config = load_config(args.config)
    sm = StateMachine(project_dir)

    if args.command == "status":
        return await _cmd_status(sm)

    # Build event bus from config
    event_bus = EventBus()
    for ev in config.events:
        event_bus.register(
            event=ev.event,
            handler=ev.handler,
            matcher=ev.matcher,
            timeout=ev.timeout,
        )

    runner = AgentRunner(config, event_bus, str(project_dir))

    if args.command == "run":
        return await _cmd_run(sm, runner, loop=args.loop)
    elif args.command == "start":
        print("Force starting from requirement-writer...")
        return await _cmd_agent(runner, "requirement-writer", "")
    elif args.command == "agent":
        return await _cmd_agent(runner, args.name, args.message)

    # No command given — show status
    return await _cmd_status(sm)


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    _setup_logging(args.verbose)

    exit_code = asyncio.run(_async_main(args))
    sys.exit(exit_code)
