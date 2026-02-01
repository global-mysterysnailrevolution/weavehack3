from __future__ import annotations

import base64
import os
import sys
import tempfile
from dataclasses import dataclass
from typing import Any

import weave
from browserbase import Browserbase
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright


@dataclass
class Observation:
    url: str
    screenshot_path: str | None = None
    screenshot_base64: str | None = None
    dom_snapshot: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class Action:
    type: str
    payload: dict[str, Any]


class WebDriver:
    """Interface for browser actions/observations using Browserbase."""

    def __init__(self) -> None:
        self.current_url = "about:blank"
        self._initialized = False
        self.browserbase_api_key = os.getenv("BROWSERBASE_API_KEY")
        self.browserbase_project_id = os.getenv("BROWSERBASE_PROJECT_ID")
        self._client: Browserbase | None = None
        self._session_id: str | None = None
        self._connect_url: str | None = None

        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    def _init_browserbase(self) -> None:
        """Initialize Browserbase connection (fallback)."""
        if self._initialized:
            return

        if not self.browserbase_api_key or not self.browserbase_project_id:
            raise RuntimeError("Browserbase credentials not found. Set BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID.")

        try:
            self._client = Browserbase(api_key=self.browserbase_api_key)
            session_response = self._client.sessions.create(
                project_id=self.browserbase_project_id,
                keep_alive=True,
            )
            self._session_id = session_response.id
            self._connect_url = (
                getattr(session_response, "connect_url", None)
                or getattr(session_response, "cdp_url", None)
                or getattr(session_response, "ws_url", None)
                or getattr(session_response, "browser_ws_endpoint", None)
                or getattr(session_response, "browser_ws", None)
            )

            if not self._connect_url:
                raise RuntimeError("Browserbase session missing a CDP connect URL.")

            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.connect_over_cdp(self._connect_url)

            contexts = self._browser.contexts
            self._context = contexts[0] if contexts else self._browser.new_context()
            self._page = self._context.pages[0] if self._context.pages else self._context.new_page()

            print(f"[OK] Browserbase session created: {self._session_id}", file=sys.stderr)
            self._initialized = True
        except Exception as e:
            raise RuntimeError(f"Browserbase initialization failed: {e}") from e

    def observe(self) -> Observation:
        """Take a screenshot and get current page state."""
        self._init_browserbase()

        try:
            if not self._page:
                raise RuntimeError("Browserbase page not initialized.")

            screenshot_bytes = self._page.screenshot(full_page=False)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            dom_snapshot = self._page.content()
            self.current_url = self._page.url

            live_url = None
            if self._client and self._session_id:
                try:
                    debug_info = self._client.sessions.debug(id=self._session_id)
                    live_url = getattr(debug_info, "live_url", None)
                except Exception:
                    live_url = None

            return Observation(
                url=self.current_url,
                screenshot_path=None,
                screenshot_base64=screenshot_base64,
                dom_snapshot=dom_snapshot,
                metadata={
                    "session_id": self._session_id,
                    "live_url": live_url,
                },
            )
        except Exception as e:
            print(f"[WARN] Browserbase observe failed: {e}", file=sys.stderr)
            return Observation(
                url=self.current_url,
                screenshot_path=None,
                screenshot_base64=None,
                dom_snapshot=None,
                metadata={"error": str(e)},
            )

    def act(self, action: Action) -> None:
        """Execute a browser action."""
        self._init_browserbase()

        command = action.payload.get("command", "")
        target = action.payload.get("target", "")
        text = action.payload.get("text", "")

        try:
            if not self._page:
                raise RuntimeError("Browserbase page not initialized.")

            if command == "navigate":
                url = target or text
                self._page.goto(url, wait_until="networkidle", timeout=30000)
                self.current_url = self._page.url
                print(f"  [NAV] Navigated to: {url}", file=sys.stderr)
            elif command == "click":
                if target:
                    self._page.click(target, timeout=5000)
                print(f"  [CLICK] Clicked: {target}", file=sys.stderr)
            elif command == "type":
                if target:
                    self._page.fill(target, text, timeout=5000)
                print(f"  [TYPE] Typed '{text}' into: {target}", file=sys.stderr)
            elif command == "scroll":
                self._page.evaluate("window.scrollBy(0, window.innerHeight)")
                print(f"  [SCROLL] Scrolled", file=sys.stderr)
        except Exception as e:
            print(f"  [ERROR] Browser action failed: {e}", file=sys.stderr)
    
    def close(self) -> None:
        """Close the browser session."""
        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
        if self._client and self._session_id:
            try:
                if hasattr(self._client.sessions, "close"):
                    self._client.sessions.close(id=self._session_id)
                print(f"[OK] Closing Browserbase session: {self._session_id}", file=sys.stderr)
            except Exception as e:
                print(f"[WARN] Error closing session: {e}", file=sys.stderr)
