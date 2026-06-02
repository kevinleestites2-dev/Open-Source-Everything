#!/usr/bin/env python3
"""
Agent Zero — Layer 13: Physical Form (Psi0)
Android control via Nexus Relay. Agent Zero gets hands.

Capabilities:
  tap(x, y)             -- touch screen at coordinates
  type_text(text)       -- keyboard input
  open_url(url)         -- launch browser to URL
  launch_app(package)   -- start Android app by package name
  swipe(x1,y1,x2,y2)   -- gesture swipe
  read_screen()         -- get UI accessibility tree
  screenshot()          -- capture screen
  press_key(keycode)    -- hardware/virtual key press
  run_shell(cmd)        -- Termux command (safety-gated)
  ping()                -- check Nexus Relay liveness
"""

import json
import logging
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger("AgentZero.L13.PhysicalForm")

PSI0_LOG     = Path("cerberus_state/psi0_log.jsonl")
NEXUS_URL    = "https://nexus-relay-production.up.railway.app"
NEXUS_SECRET = "pantheon_prime"

# Commands that are never allowed — no exceptions
SHELL_BLOCKLIST = [
    "rm -rf", "format", "dd if=", "mkfs", "shutdown", "reboot",
    ":(){ :|:& };:", "wget|sh", "curl|sh",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Psi0PhysicalForm:
    """
    Layer 13 — Physical Form.
    Translates Agent Zero intent into physical device actions
    via Nexus Relay -> NexusClaw on the Red Magic.

    Named Psi0: the bridge between pure cognition and physical reality.
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        head_name: str,
        telegram_fn: Callable,
        nexus_url: Optional[str] = None,
        nexus_secret: Optional[str] = None,
        result_timeout: int = 15,
    ):
        self.head             = head_name
        self.tg               = telegram_fn
        self.url              = nexus_url    or NEXUS_URL
        self.secret           = nexus_secret or NEXUS_SECRET
        self.timeout          = result_timeout
        self.actions_executed = 0
        self.actions_failed   = 0

        PSI0_LOG.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"[{self.head}][L13] Psi0 Physical Form ONLINE — v{self.VERSION}")
        logger.info(f"[{self.head}][L13] Nexus Relay: {self.url}")

    # ── Internal relay comms ──────────────────────────────────────────────────

    def _post_command(self, command: Dict) -> Optional[str]:
        """Send command to Nexus Relay, return command _id."""
        try:
            payload = json.dumps({"command": json.dumps(command)}).encode()
            req = urllib.request.Request(
                f"{self.url}/command", data=payload, method="POST",
                headers={"Content-Type": "application/json", "X-Secret": self.secret}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                return json.load(r).get("_id")
        except Exception as e:
            logger.warning(f"[{self.head}][L13] Post command failed: {e}")
            return None

    def _poll_result(self, cmd_id: str) -> Optional[Dict]:
        """Poll for result by command ID, with timeout."""
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            try:
                req = urllib.request.Request(
                    f"{self.url}/result/{cmd_id}",
                    headers={"X-Secret": self.secret}
                )
                with urllib.request.urlopen(req, timeout=5) as r:
                    data = json.load(r)
                if data.get("result"):
                    return data
            except Exception:
                pass
            time.sleep(1.5)
        return None

    def _execute(self, action: str, params: Dict) -> Dict:
        """Core execution pipeline: post -> poll -> log -> return."""
        command = {"action": action, "source": f"AgentZero-L13-{self.head}", **params}
        self.actions_executed += 1

        cmd_id = self._post_command(command)
        if not cmd_id:
            self.actions_failed += 1
            return {"success": False, "error": "relay_unavailable", "action": action}

        result = self._poll_result(cmd_id)
        outcome = {
            "action": action, "cmd_id": cmd_id,
            "success": result is not None,
            "result": result, "ts": _now(),
        }
        if not result:
            self.actions_failed += 1
            outcome["error"] = "timeout_no_result"

        with open(PSI0_LOG, "a") as f:
            f.write(json.dumps({"ts": _now(), "head": self.head, **outcome}) + "\n")

        return outcome

    # ── Physical actions ──────────────────────────────────────────────────────

    def tap(self, x: int, y: int) -> Dict:
        """Tap screen at (x, y)."""
        return self._execute("tap", {"x": x, "y": y})

    def type_text(self, text: str) -> Dict:
        """Type text via soft keyboard."""
        return self._execute("type_text", {"text": text})

    def open_url(self, url: str) -> Dict:
        """Open URL in Android browser."""
        return self._execute("open_url", {"url": url})

    def launch_app(self, package: str) -> Dict:
        """Launch app by Android package name."""
        return self._execute("launch_app", {"package": package})

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> Dict:
        """Swipe from (x1,y1) to (x2,y2)."""
        return self._execute("swipe", {
            "x1": x1, "y1": y1, "x2": x2, "y2": y2, "duration_ms": duration_ms
        })

    def read_screen(self) -> Dict:
        """Get current UI accessibility tree."""
        return self._execute("read_screen", {})

    def screenshot(self) -> Dict:
        """Capture screen and return image data."""
        return self._execute("screenshot", {})

    def press_key(self, keycode: str) -> Dict:
        """Press hardware/virtual key (e.g. KEYCODE_BACK, KEYCODE_HOME)."""
        return self._execute("press_key", {"keycode": keycode})

    def run_shell(self, cmd: str) -> Dict:
        """
        Run shell command in Termux.
        Safety-gated: destructive commands are always blocked.
        """
        for blocked in SHELL_BLOCKLIST:
            if blocked in cmd:
                logger.warning(f"[{self.head}][L13] Shell BLOCKED: {cmd}")
                return {"success": False, "error": "blocked_destructive_command", "cmd": cmd}
        return self._execute("shell", {"command": cmd})

    def ping(self) -> bool:
        """Check if Nexus Relay is alive."""
        try:
            req = urllib.request.Request(
                f"{self.url}/ping", headers={"X-Secret": self.secret}
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.load(r)
            return data.get("status") == "ok" or "version" in data
        except Exception:
            return False

    def status(self) -> Dict:
        relay_alive = self.ping()
        return {
            "version":          self.VERSION,
            "nexus_relay":      self.url,
            "relay_alive":      relay_alive,
            "actions_executed": self.actions_executed,
            "actions_failed":   self.actions_failed,
            "success_rate":     round(
                (self.actions_executed - self.actions_failed) / max(1, self.actions_executed), 3
            ),
        }


def _init_physical_form(
    head_name: str,
    telegram_fn: Callable,
    nexus_url: Optional[str] = None,
) -> Optional[Psi0PhysicalForm]:
    """Factory — safe init, returns None on failure."""
    try:
        return Psi0PhysicalForm(
            head_name=head_name,
            telegram_fn=telegram_fn,
            nexus_url=nexus_url,
        )
    except Exception as e:
        logger.warning(f"[L13] Physical Form init failed: {e}")
        return None
