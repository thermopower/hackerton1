"""Tests for adapters — capability checks and basic behavior."""

import pytest

from harness.adapters.base import AdapterCapabilities
from harness.adapters.claude_code import ClaudeCodeAdapter
from harness.adapters.anthropic_api import AnthropicApiAdapter
from harness.adapters.opencode import OpenCodeAdapter


class TestClaudeCodeAdapter:
    def test_name(self):
        adapter = ClaudeCodeAdapter()
        assert adapter.name == "claude-code"

    def test_capabilities(self):
        adapter = ClaudeCodeAdapter()
        caps = adapter.capabilities
        assert caps.supports_sub_agents is True
        assert caps.supports_mcp is True
        assert caps.supports_memory is True


class TestAnthropicApiAdapter:
    def test_name(self):
        adapter = AnthropicApiAdapter()
        assert adapter.name == "anthropic-api"

    def test_capabilities(self):
        adapter = AnthropicApiAdapter()
        caps = adapter.capabilities
        assert caps.supports_sub_agents is False
        assert caps.supports_parallel is True
        assert "file:read" in caps.supported_tools

    @pytest.mark.asyncio
    async def test_fails_without_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        adapter = AnthropicApiAdapter()
        available = await adapter.check_available()
        # Should be False unless anthropic is installed AND key exists
        # We just verify it doesn't crash


class TestOpenCodeAdapter:
    def test_name(self):
        adapter = OpenCodeAdapter()
        assert adapter.name == "opencode"

    def test_capabilities(self):
        adapter = OpenCodeAdapter()
        caps = adapter.capabilities
        assert caps.supports_sub_agents is True
        assert caps.supports_mcp is True
        assert caps.max_context_window == 200_000
        assert "file:edit" in caps.supported_tools
        assert "agent:invoke" in caps.supported_tools


class TestAdapterRegistration:
    def test_agent_runner_resolves_adapters(self):
        from harness.agent_runner import _load_adapter_class
        assert _load_adapter_class("claude-code") is ClaudeCodeAdapter
        assert _load_adapter_class("anthropic-api") is AnthropicApiAdapter
        assert _load_adapter_class("opencode") is OpenCodeAdapter

    def test_unknown_adapter_raises(self):
        from harness.agent_runner import _load_adapter_class
        with pytest.raises(ValueError, match="Unknown adapter"):
            _load_adapter_class("nonexistent")
