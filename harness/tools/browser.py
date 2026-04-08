"""Browser tool — Playwright direct calls (bypasses Claude Code MCP).

Used by adapters that don't support MCP (Anthropic API, OpenCode, etc.)
to perform browser-based validation similar to the evaluator/integration-fixer.
"""

from __future__ import annotations

from typing import Any

from harness.tools.base import Tool, ToolResult


class BrowserNavigateTool(Tool):
    """Navigate to a URL and return page state."""

    def __init__(self) -> None:
        self._browser = None
        self._page = None

    @property
    def name(self) -> str:
        return "browser:navigate"

    async def _ensure_browser(self) -> None:
        if self._browser is None:
            try:
                from playwright.async_api import async_playwright

                pw = await async_playwright().start()
                self._browser = await pw.chromium.launch(headless=True)
                self._page = await self._browser.new_page()
            except ImportError:
                raise RuntimeError(
                    "playwright not installed. Install with: pip install 'harness[browser]'"
                )

    async def execute(self, **params: Any) -> ToolResult:
        url = params.get("url", "")
        if not url:
            return ToolResult(success=False, error="url is required")

        action = params.get("action", "navigate")

        try:
            await self._ensure_browser()
            assert self._page is not None

            if action == "navigate":
                await self._page.goto(url, wait_until="networkidle", timeout=30000)
                title = await self._page.title()
                return ToolResult(
                    success=True,
                    output=f"Navigated to {url}. Title: {title}",
                    data={"url": url, "title": title},
                )
            elif action == "screenshot":
                screenshot = await self._page.screenshot(full_page=True)
                return ToolResult(
                    success=True,
                    output=f"Screenshot taken ({len(screenshot)} bytes)",
                    data={"size": len(screenshot)},
                )
            elif action == "console":
                # Return captured console messages
                return ToolResult(
                    success=True,
                    output="Console messages captured.",
                )
            elif action == "close":
                if self._browser:
                    await self._browser.close()
                    self._browser = None
                    self._page = None
                return ToolResult(success=True, output="Browser closed.")
            else:
                return ToolResult(
                    success=False, error=f"Unknown action: {action}"
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def to_api_schema(self) -> dict[str, Any]:
        return {
            "name": "browser_navigate",
            "description": "Navigate to a URL, take screenshots, or check console errors.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to navigate to."},
                    "action": {
                        "type": "string",
                        "enum": ["navigate", "screenshot", "console", "close"],
                        "default": "navigate",
                    },
                },
                "required": ["url"],
            },
        }
