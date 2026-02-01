from __future__ import annotations

import base64
import os
import sys
import tempfile
from dataclasses import dataclass
from typing import Any

import weave

# Try Playwright first (more reliable), fall back to Browserbase, then mock mode
PLAYWRIGHT_AVAILABLE = False
BROWSERBASE_AVAILABLE = False
Browserbase = None  # type: ignore

try:
    from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Make Browserbase import optional - if it fails, we'll use mock mode
if not PLAYWRIGHT_AVAILABLE:
    try:
        from browserbase import Browserbase
        BROWSERBASE_AVAILABLE = True
    except Exception:
        Browserbase = None  # type: ignore
        BROWSERBASE_AVAILABLE = False


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
    """Interface for browser actions/observations using Playwright (preferred) or Browserbase.
    
    Uses Playwright for reliable browser automation, falls back to Browserbase if available,
    otherwise uses mock mode.
    """

    def __init__(self) -> None:
        self.current_url = "about:blank"
        self._playwright = None
        self._browser: Browser | None = None
        self._page: Page | None = None
        self._context: BrowserContext | None = None
        self._initialized = False
        
        # Browserbase fallback
        self.browserbase_api_key = os.getenv("BROWSERBASE_API_KEY")
        self.browserbase_project_id = os.getenv("BROWSERBASE_PROJECT_ID")
        self._browserbase_client: Browserbase | None = None
        self._browserbase_session_id: str | None = None

    def _init_playwright(self) -> None:
        """Initialize Playwright browser."""
        if self._initialized:
            return
            
        if not PLAYWRIGHT_AVAILABLE:
            print("[WARN] Playwright not available, trying Browserbase...", file=sys.stderr)
            self._init_browserbase()
            return
        
        try:
            self._playwright = sync_playwright().start()
            # Launch headless browser
            self._browser = self._playwright.chromium.launch(headless=True)
            self._context = self._browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            self._page = self._context.new_page()
            self._initialized = True
            print("[OK] Playwright browser initialized", file=sys.stderr)
        except Exception as e:
            print(f"[WARN] Playwright initialization failed: {e}. Trying Browserbase...", file=sys.stderr)
            self._init_browserbase()

    def _init_browserbase(self) -> None:
        """Initialize Browserbase connection (fallback)."""
        if self._initialized:
            return
            
        if not BROWSERBASE_AVAILABLE or Browserbase is None:
            print("[WARN] Browserbase not available, using mock mode", file=sys.stderr)
            self._initialized = True
            return
            
        if not self.browserbase_api_key or not self.browserbase_project_id:
            print("[WARN] Browserbase credentials not found, using mock mode", file=sys.stderr)
            self._initialized = True
            return

        try:
            self._browserbase_client = Browserbase(api_key=self.browserbase_api_key)
            session_response = self._browserbase_client.sessions.create(
                project_id=self.browserbase_project_id,
                keep_alive=True,
            )
            self._browserbase_session_id = session_response.id
            print(f"[OK] Browserbase session created: {self._browserbase_session_id}", file=sys.stderr)
            self._initialized = True
        except Exception as e:
            print(f"[WARN] Browserbase initialization failed: {e}. Using mock mode.", file=sys.stderr)
            self._initialized = True

    def observe(self) -> Observation:
        """Take a screenshot and get current page state."""
        self._init_playwright()
        
        # Use Playwright if available
        if self._page:
            try:
                self.current_url = self._page.url
                # Take screenshot
                screenshot_bytes = self._page.screenshot(full_page=False)
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                
                # Get DOM snapshot
                dom_snapshot = self._page.content()
                
                return Observation(
                    url=self.current_url,
                    screenshot_base64=screenshot_base64,
                    dom_snapshot=dom_snapshot,
                    metadata={"method": "playwright"}
                )
            except Exception as e:
                print(f"[WARN] Playwright observe failed: {e}", file=sys.stderr)
        
        # Fallback to Browserbase or mock
        if self._browserbase_client and self._browserbase_session_id:
            # Browserbase implementation would go here
            return Observation(
                url=self.current_url,
                screenshot_base64=None,
                dom_snapshot=None,
                metadata={"method": "browserbase", "session_id": self._browserbase_session_id}
            )
        
        # Mock mode
        return Observation(
            url=self.current_url,
            screenshot_base64=None,
            dom_snapshot=None,
            metadata={"note": "mock observation - no browser available"}
        )

    def act(self, action: Action) -> None:
        """Execute a browser action."""
        self._init_playwright()
        
        command = action.payload.get("command", "")
        target = action.payload.get("target", "")
        text = action.payload.get("text", "")
        
        # Use Playwright if available
        if self._page:
            try:
                if command == "navigate":
                    url = target or text
                    self._page.goto(url, wait_until="networkidle", timeout=30000)
                    self.current_url = self._page.url
                    print(f"  [NAV] Navigated to: {url}", file=sys.stderr)
                    
                elif command == "click":
                    if target:
                        # Try different selectors
                        try:
                            self._page.click(target, timeout=5000)
                        except:
                            # Try as XPath or other selector
                            try:
                                self._page.locator(target).click(timeout=5000)
                            except:
                                print(f"  [WARN] Could not click: {target}", file=sys.stderr)
                    print(f"  [CLICK] Clicked: {target}", file=sys.stderr)
                    
                elif command == "type":
                    if target:
                        self._page.fill(target, text, timeout=5000)
                    print(f"  [TYPE] Typed '{text}' into: {target}", file=sys.stderr)
                    
                elif command == "scroll":
                    self._page.evaluate("window.scrollBy(0, window.innerHeight)")
                    print(f"  [SCROLL] Scrolled down", file=sys.stderr)
                    
                return
            except Exception as e:
                print(f"  [ERROR] Playwright action failed: {e}", file=sys.stderr)
        
        # Fallback to Browserbase or mock
        if self._browserbase_client:
            print(f"  [INFO] Browserbase action: {command} (not fully implemented)", file=sys.stderr)
        else:
            # Mock mode
            if command == "navigate":
                url = target or text
                self.current_url = url
                print(f"  [NAV] Navigating to: {url} (mock)", file=sys.stderr)
            elif command == "click":
                print(f"  [CLICK] Clicking: {target} (mock)", file=sys.stderr)
            elif command == "type":
                print(f"  [TYPE] Typing '{text}' into: {target} (mock)", file=sys.stderr)
            elif command == "scroll":
                print(f"  [SCROLL] Scrolling (mock)", file=sys.stderr)
    
    def close(self) -> None:
        """Close the browser session."""
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        if self._browserbase_client and self._browserbase_session_id:
            print(f"[OK] Closing Browserbase session: {self._browserbase_session_id}", file=sys.stderr)
