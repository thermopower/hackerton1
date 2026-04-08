"""Tests for event_bus — event system replacing Claude Code hooks."""

import asyncio

import pytest

from harness.event_bus import EventBus


@pytest.fixture
def bus():
    return EventBus()


class TestEventBus:
    @pytest.mark.asyncio
    async def test_calls_matching_handler(self, bus: EventBus):
        called_with = {}

        async def handler(agent_name, context):
            called_with["agent"] = agent_name
            called_with["context"] = context

        bus.register("agent:after-stop", handler, matcher="sprint-builder")
        await bus.emit("agent:after-stop", "sprint-builder")
        assert called_with["agent"] == "sprint-builder"

    @pytest.mark.asyncio
    async def test_skips_non_matching_handler(self, bus: EventBus):
        called = False

        async def handler(agent_name, context):
            nonlocal called
            called = True

        bus.register("agent:after-stop", handler, matcher="sprint-builder")
        await bus.emit("agent:after-stop", "evaluator")
        assert not called

    @pytest.mark.asyncio
    async def test_regex_matcher(self, bus: EventBus):
        calls = []

        async def handler(agent_name, context):
            calls.append(agent_name)

        bus.register("agent:after-stop", handler, matcher="evaluator|retrospective")
        await bus.emit("agent:after-stop", "evaluator")
        await bus.emit("agent:after-stop", "retrospective")
        await bus.emit("agent:after-stop", "reviewer")
        assert calls == ["evaluator", "retrospective"]

    @pytest.mark.asyncio
    async def test_no_matcher_matches_all(self, bus: EventBus):
        calls = []

        async def handler(agent_name, context):
            calls.append(agent_name)

        bus.register("agent:before-start", handler)
        await bus.emit("agent:before-start", "planner")
        await bus.emit("agent:before-start", "evaluator")
        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_different_events_dont_interfere(self, bus: EventBus):
        calls = []

        async def h1(agent_name, context):
            calls.append("before")

        async def h2(agent_name, context):
            calls.append("after")

        bus.register("agent:before-start", h1)
        bus.register("agent:after-stop", h2)
        await bus.emit("agent:before-start", "x")
        assert calls == ["before"]
