#!/usr/bin/env python3
"""
Agent Zero Integration — Android-MCP
Category : ANDROID_CONTROL / NEXUSCLAW_V4
Source   : https://github.com/CursorTouch/Android-MCP
Stars    : 641 | Forks: 86
Language : Python
Updated  : 2026-06-03 (active — updated today)
Absorbed : 2026-06-02

ENGINE SCORE: 8/10
Reason: Clean, real, production-grade Android MCP server. 641 stars, actively
        maintained (updated TODAY). Built on uiautomator2 + ADB + FastMCP.
        No computer vision pipeline required — works off Android's native
        Accessibility API (XML UI hierarchy dump). Supports USB AND WiFi ADB.
        This is NexusClaw v4: the clean Python MCP server the Pantheon needs to
        control the Red Magic without root, without tunnels, without Cloudflare.
        
        Why not 10: small footprint (21 files), no self-evolution, no memory.
        But for Android control, it is the right primitive. Complements omp (which
        has browser.ts but not native Android control) and LAMDA (which requires root).
        Android-MCP fills the no-root, MCP-native gap in the Pantheon's control stack.

What it is:
    A Python MCP server (FastMCP) that gives any AI agent full control over an
    Android device via ADB and the Android Accessibility Service API. No CV model,
    no OCR, no fine-tuning. The AI sees the XML UI hierarchy and acts on it.

    INSTALL (one command):
        pip install android-mcp
        # or via uv (recommended):
        uvx android-mcp --wifi 192.168.x.x

    CONNECT:
        USB:  android-mcp --usb
        WiFi: android-mcp --wifi 192.168.1.x   # or IP:PORT, defaults to :5555
        Auto: ANDROID_MCP_DEVICE=192.168.1.x:5555 android-mcp

    MCP CONFIG (for Claude Desktop / omp / any MCP client):
        {
          "mcpServers": {
            "android": {
              "command": "uvx",
              "args": ["android-mcp"],
              "env": {
                "ANDROID_MCP_DEVICE": "192.168.1.x:5555",
                "ANDROID_MCP_CONNECTION": "wifi"
              }
            }
          }
        }

    TOOL INVENTORY:
    From uiautomator2 + FastMCP wrapper:
    - list_devices()         → enumerate connected ADB devices
    - connect(serial)        → connect to device by serial or IP:PORT
    - get_state()            → dump interactive UI element tree (XML → structured)
    - screenshot()           → capture screen (PIL Image → base64)
    - tap(x, y)              → tap at coordinates
    - swipe(x1,y1,x2,y2)    → swipe gesture
    - input_text(text)       → type text into focused field
    - press_key(keycode)     → send Android keycode (HOME, BACK, ENTER, etc.)
    - launch_app(package)    → start app by package name
    - shell(cmd)             → execute ADB shell command (arbitrary)
    - get_device_info()      → device model, Android version, screen size

    ELEMENT TREE (TreeState):
    Each element returned:
        ElementNode {
            name:         str    (content-desc or text)
            class_name:   str    (android.widget.Button, etc.)
            coordinates:  CenterCord(x, y)
            bounding_box: BoundingBox(x1, y1, x2, y2)
            resource_id:  str    (e.g. "login_button")
        }
    The AI taps by name or coordinates. No vision needed.

    LATENCY: 2–4s between actions (device-dependent). Acceptable for automation.
    NOT suitable for sub-100ms reaction loops (use LAMDA root mode for that).

    ARCHITECTURE:
    ┌───────────────────────────────────┐
    │  AI Agent (omp / Agent Zero)      │
    │  ↓ MCP tool call                  │
    │  Android-MCP (FastMCP server)     │
    │  ↓ uiautomator2 / ADB             │
    │  Red Magic (Android 10+)          │
    │  ↓ Android Accessibility Service  │
    │  UI Element Tree + Actions        │
    └───────────────────────────────────┘

PANTHEON INTEGRATION:

    RED MAGIC / NEXUSCLAW V4 (PRIMARY):
    - Deploy Android-MCP on any machine with ADB access to the Red Magic
    - WiFi ADB: connect to Red Magic IP → ZapiaPrime controls the phone
    - No USB required, no tunnel, no proot, no root
    - omp on Nexus → MCP call → Android-MCP → Red Magic = full remote phone control
    - This is cleaner than NexusClaw v3 (LAMDA/root) and simpler than Nexus Relay

    NEXUSCLAW STACK COMPARISON:
    v1 (NexusClaw):     Cloudflare tunnel + MCP — dies on hotel WiFi
    v2 (OpenJarvis):    mobile-mcp + uiautomator2 — same approach, less clean
    v3 (LAMDA):         Root required — Red Magic NOT rooted (locked per MY_RULES.md)
    v4 (Android-MCP):   WiFi ADB + FastMCP + NO ROOT = the clean path ✅

    AGENT ZERO + OMP:
    - omp has browser.ts (web browser) but NOT native Android control
    - Android-MCP fills the gap: Agent Zero controls the Red Magic screen
    - Chain: Agent Zero → omp bash.ts → uvx android-mcp → Red Magic

    ELEFTHERIAPRIME:
    - Android-MCP is the lightweight complement to EleftheriaPrime (ZeroTap APK)
    - EleftheriaPrime: on-device accessibility service (APK side)
    - Android-MCP: off-device ADB/MCP bridge (server side)
    - Combined: EleftheriaPrime handles what ADB can't; Android-MCP handles the rest

    GHOSTPRIME:
    - Social platform automation on Red Magic (Xiaohongshu, TikTok, YouTube)
    - Android-MCP taps → scrolls → screenshots for social signal injection
    - Complements browser.ts for native app automation (browser can't reach native apps)

    SCOUTPRIME:
    - LEEPA, PropertyOnion, Zillow native Android apps → Android-MCP scrapes UI
    - No Cloudflare bypass needed — it's the native app, not the web
    - Screenshot + element tree = structured property data without web scraping

    ZEUSPRIME:
    - Polymarket / Kalshi Android apps → Android-MCP places bets via UI
    - Fallback when API is blocked or rate-limited

    WIFI ADB SETUP (Red Magic → ZapiaPrime):
    1. On Red Magic: Settings → Developer Options → Wireless Debugging → Enable
    2. Note the IP:PORT shown (e.g. 192.168.1.x:5555)
    3. On machine running Android-MCP: adb connect 192.168.1.x:5555
    4. Start: ANDROID_MCP_DEVICE=192.168.1.x:5555 uvx android-mcp
    5. Wire omp MCP config to point at this server
    6. Agent Zero now controls the Red Magic screen

    ANDROID 11+ WIRELESS DEBUGGING (no USB ever needed):
    - Settings → Developer Options → Wireless Debugging → Pair device with pairing code
    - adb pair 192.168.1.x:PAIR_PORT (enter 6-digit code)
    - adb connect 192.168.1.x:5555
    - Works entirely over WiFi — no USB, no USB debugging toggle
"""

import os
import sys
import json
import subprocess
import shutil
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ─── CONFIG ──────────────────────────────────────────────────────────────────

REPO_URL       = "https://github.com/CursorTouch/Android-MCP"
PACKAGE        = "android-mcp"
INSTALL_CMD    = "pip install android-mcp"
INSTALL_UVX    = "uvx android-mcp"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "TG_TOKEN_INJECTED_AT_RUNTIME")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT_ID", "7135054241")

TOOLS = {
    "list_devices":   "Enumerate ADB-connected devices (serial, status)",
    "connect":        "Connect to device by USB serial or WiFi IP:PORT",
    "get_state":      "Dump interactive UI element tree (XML → structured ElementNode list)",
    "screenshot":     "Capture screen → PIL Image / base64",
    "tap":            "Tap at (x, y) coordinates",
    "swipe":          "Swipe from (x1,y1) to (x2,y2)",
    "input_text":     "Type text into focused field",
    "press_key":      "Send Android keycode (HOME=3, BACK=4, ENTER=66, etc.)",
    "launch_app":     "Launch app by package name (e.g. com.reddit.frontpage)",
    "shell":          "Execute arbitrary ADB shell command",
    "get_device_info":"Device model, Android version, screen resolution",
}

NEXUSCLAW_COMPARISON = {
    "v1_nexusclaw":   "Cloudflare tunnel + NexusClaw MCP — dies on hotel WiFi. RETIRED.",
    "v2_openjarvus":  "mobile-mcp + uiautomator2 — same approach, less clean. RETIRED.",
    "v3_lamda":       "Root required (Frida + Magisk). Red Magic NOT rooted. BLOCKED per MY_RULES.md.",
    "v4_android_mcp": "WiFi ADB + FastMCP + NO ROOT = clean path. THIS IS IT. ✅",
}

PANTHEON_ROLES = {
    "NexusClaw v4":      "PRIMARY — WiFi ADB control of Red Magic, no root, no tunnel",
    "Agent Zero + omp":  "omp routes Android tasks via MCP call to Android-MCP server",
    "EleftheriaPrime":   "Complement — EleftheriaPrime (on-device APK) + Android-MCP (off-device bridge)",
    "GhostPrime":        "Native Android app automation for social platforms (TikTok, YouTube)",
    "ScoutPrime":        "Native app UI scraping for property data (LEEPA, Zillow apps)",
    "ZeusPrime":         "Native Polymarket / Kalshi app → UI-based trade execution",
}


# ─── WIFI ADB SETUP ──────────────────────────────────────────────────────────

WIFI_ADB_SETUP = {
    "android_10_11": [
        "1. Red Magic: Settings → Developer Options → USB Debugging → Enable",
        "2. Connect USB once to authorize the ADB host",
        "3. adb tcpip 5555  (switch to TCP mode)",
        "4. Disconnect USB",
        "5. adb connect 192.168.1.x:5555",
        "6. uvx android-mcp --wifi 192.168.1.x",
    ],
    "android_11_plus_wireless_debug": [
        "1. Red Magic: Settings → Developer Options → Wireless Debugging → Enable",
        "2. Tap 'Pair device with pairing code'",
        "3. adb pair 192.168.1.x:PAIR_PORT  (enter 6-digit code shown)",
        "4. adb connect 192.168.1.x:5555",
        "5. ANDROID_MCP_DEVICE=192.168.1.x:5555 uvx android-mcp",
        "NOTE: No USB required. Pure WiFi. Works on hotel WiFi.",
    ],
    "env_vars": {
        "ANDROID_MCP_DEVICE":     "Device serial or IP:PORT",
        "ANDROID_MCP_CONNECTION": "auto | usb | wifi",
        "ANDROID_MCP_HOST":       "WiFi host (when using env-based config)",
        "SCREENSHOT_QUANTIZED":   "true = reduce screenshot size for LLM context",
    }
}

MCP_CONFIG = {
    "mcpServers": {
        "android": {
            "command": "uvx",
            "args": ["android-mcp"],
            "env": {
                "ANDROID_MCP_DEVICE": "REPLACE_WITH_REDMAGIC_IP:5555",
                "ANDROID_MCP_CONNECTION": "wifi",
                "SCREENSHOT_QUANTIZED": "true"
            }
        }
    }
}


# ─── CORE CONNECTOR ──────────────────────────────────────────────────────────

class AndroidMCPConnector:
    """
    Pantheon connector for Android-MCP (NexusClaw v4).
    641 stars. Python. FastMCP + uiautomator2 + ADB. No root. WiFi-native.

    Pantheon Role: ANDROID_CONTROL / NEXUSCLAW_V4

    This is the clean Android control path. WiFi ADB → FastMCP → Red Magic.
    No tunnel. No root. No Cloudflare. Complements omp (web) and
    EleftheriaPrime (on-device APK).

    Usage:
        amcp = AndroidMCPConnector()
        print(amcp.health_check())
        print(amcp.wifi_setup())
        print(amcp.mcp_config(device_ip="192.168.1.x"))
        print(amcp.nexusclaw_comparison())
        print(amcp.pantheon_roles())
    """

    REPO_URL      = REPO_URL
    CATEGORY      = "ANDROID_CONTROL"
    ROLE          = "NEXUSCLAW_V4"
    PANTHEON_ROLE = "ANDROID_CONTROL / NEXUSCLAW_V4"
    SCORE         = 8
    STARS         = 641
    FORKS         = 86

    def health_check(self) -> Dict:
        return {
            "name":       "android-mcp",
            "category":   self.CATEGORY,
            "role":       self.PANTHEON_ROLE,
            "score":      self.SCORE,
            "score_note": "NexusClaw v4. Clean WiFi ADB + FastMCP Android control. No root. No tunnel. No CV pipeline. uiautomator2 + Accessibility API. Fills the gap omp (web-only) and LAMDA (root-required) leave open.",
            "stars":      self.STARS,
            "forks":      self.FORKS,
            "stack":      ["Python 3.13", "FastMCP 2.14+", "uiautomator2 3.3+", "ADB", "Android Accessibility API"],
            "requires":   ["ADB installed on host", "Android 10+ device", "WiFi ADB or USB debugging enabled"],
            "no_root":    True,
            "no_tunnel":  True,
            "no_cv":      True,
            "install":    INSTALL_CMD,
            "install_uvx": INSTALL_UVX,
            "tools":      TOOLS,
            "latency_ms": "2000-4000ms per action",
            "key_use_cases": [
                "Red Magic control from Nexus/ZapiaPrime via WiFi (NexusClaw v4)",
                "GhostPrime native Android social app automation",
                "ScoutPrime native property app UI scraping",
                "EleftheriaPrime complement (off-device bridge side)",
                "ZeusPrime native Polymarket/Kalshi app UI execution",
            ],
            "repo":   self.REPO_URL,
            "status": "production — updated today, 641 stars, actively maintained",
        }

    def wifi_setup(self, android_version: str = "11+") -> Dict:
        key = "android_11_plus_wireless_debug" if android_version >= "11" else "android_10_11"
        return self.to_pantheon_signal({
            "action":  "wifi_setup",
            "android": android_version,
            "steps":   WIFI_ADB_SETUP[key],
            "env":     WIFI_ADB_SETUP["env_vars"],
            "note":    "Red Magic runs Android 12+. Use android_11_plus_wireless_debug path. No USB ever needed.",
        })

    def mcp_config(self, device_ip: Optional[str] = None) -> Dict:
        cfg = json.loads(json.dumps(MCP_CONFIG))
        if device_ip:
            cfg["mcpServers"]["android"]["env"]["ANDROID_MCP_DEVICE"] = f"{device_ip}:5555"
        return self.to_pantheon_signal({
            "action":     "mcp_config",
            "config":     cfg,
            "usage":      "Paste into omp MCP config or Claude Desktop config.json",
            "omp_note":   "omp reads MCP config from ~/.omp/mcp.json — wire Android-MCP there",
        })

    def nexusclaw_comparison(self) -> Dict:
        return self.to_pantheon_signal({
            "action":     "nexusclaw_comparison",
            "comparison": NEXUSCLAW_COMPARISON,
            "winner":     "v4_android_mcp",
            "reason":     "No root (LAMDA blocked), no tunnel (hotel WiFi kills v1), pure WiFi ADB + FastMCP",
        })

    def pantheon_roles(self) -> Dict:
        return self.to_pantheon_signal({
            "action": "pantheon_roles",
            "roles":  PANTHEON_ROLES,
        })

    def tool_manifest(self) -> Dict:
        return self.to_pantheon_signal({
            "action": "tool_manifest",
            "tools":  TOOLS,
            "count":  len(TOOLS),
        })

    def run_command(self, device_ip: str, adb_cmd: str, timeout: int = 30) -> Dict:
        """Direct ADB command execution (requires ADB on PATH)."""
        if not shutil.which("adb"):
            return {"error": "adb not found on PATH"}
        try:
            result = subprocess.run(
                ["adb", "-s", f"{device_ip}:5555", "shell"] + adb_cmd.split(),
                capture_output=True, text=True, timeout=timeout
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except Exception as e:
            return {"error": str(e)}

    def to_pantheon_signal(self, raw: Any) -> Dict:
        return {
            "source":    "android-mcp",
            "category":  self.CATEGORY,
            "role":      self.PANTHEON_ROLE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data":      raw,
        }


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    amcp = AndroidMCPConnector()

    if len(sys.argv) < 2:
        print(json.dumps(amcp.health_check(), indent=2))
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "health":
        print(json.dumps(amcp.health_check(), indent=2))
    elif cmd == "setup":
        ver = sys.argv[2] if len(sys.argv) > 2 else "11+"
        print(json.dumps(amcp.wifi_setup(ver), indent=2))
    elif cmd == "config":
        ip = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(amcp.mcp_config(ip), indent=2))
    elif cmd == "compare":
        print(json.dumps(amcp.nexusclaw_comparison(), indent=2))
    elif cmd == "roles":
        print(json.dumps(amcp.pantheon_roles(), indent=2))
    elif cmd == "tools":
        print(json.dumps(amcp.tool_manifest(), indent=2))
    elif cmd == "run" and len(sys.argv) > 3:
        print(json.dumps(amcp.run_command(sys.argv[2], sys.argv[3]), indent=2))
    else:
        print(f"Usage: {sys.argv[0]} [health|setup [version]|config [ip]|compare|roles|tools|run <ip> <cmd>]")
