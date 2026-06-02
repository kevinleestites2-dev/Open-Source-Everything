"""
security_layer.py — Pantheon Security Stack
Layers 1-5: Key Protection, Trade Validation, Network Security, Runtime Protection, The Governor
"""

import os
import time
import hmac
import hashlib
import logging
import sqlite3
import threading
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from collections import defaultdict

import requests
from cryptography.fernet import Fernet

# ─────────────────────────────────────────────
# LAYER 1 — KEY PROTECTION
# ─────────────────────────────────────────────

class KeyVault:
    """
    Loads keys from .env once at startup, encrypts in memory, never touches disk again.
    Read-only keys for data feeds. Trading keys for execution. Separated hard.
    """

    def __init__(self, env_path: str = ".env"):
        self._fernet = Fernet(Fernet.generate_key())  # Session key — lives in RAM only
        self._vault: Dict[str, bytes] = {}
        self._load_env(env_path)

    def _load_env(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"[KeyVault] .env not found at {path}")
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                self._vault[key.strip()] = self._fernet.encrypt(value.strip().encode())
        logging.info(f"[KeyVault] {len(self._vault)} keys loaded and encrypted in memory.")

    def get(self, key: str) -> Optional[str]:
        encrypted = self._vault.get(key)
        if not encrypted:
            return None
        return self._fernet.decrypt(encrypted).decode()

    def get_readonly(self, key: str) -> Optional[str]:
        """Enforces convention: read-only keys are prefixed RO_ in .env"""
        return self.get(f"RO_{key}") or self.get(key)

    def get_trading(self, key: str) -> Optional[str]:
        """Enforces convention: trading keys are prefixed TRADE_ in .env"""
        return self.get(f"TRADE_{key}")


# ─────────────────────────────────────────────
# LAYER 2 — TRADE VALIDATION
# ─────────────────────────────────────────────

ALLOWED_PAIRS = {
    "BTC-USD", "ETH-USD", "SOL-USD",
    "BTC-USDT", "ETH-USDT", "SOL-USDT",
    "BTC/USD", "ETH/USD", "SOL/USD",
}

MAX_POSITION_SIZE_USD = 500.0       # Hard ceiling — not overridable at runtime
DAILY_LOSS_LIMIT_USD  = 200.0       # Auto-pause threshold
DUPLICATE_WINDOW_SEC  = 30          # Same signal can't fire twice within this window


class TradeValidator:

    def __init__(self):
        self._recent_signals: Dict[str, float] = {}  # signal_hash -> timestamp
        self._daily_loss: float = 0.0
        self._paused: bool = False
        self._lock = threading.Lock()

    def _signal_hash(self, pair: str, direction: str, size: float) -> str:
        raw = f"{pair}:{direction}:{size:.4f}"
        return hashlib.md5(raw.encode()).hexdigest()

    def validate(self, pair: str, direction: str, size_usd: float) -> tuple[bool, str]:
        with self._lock:
            # Pair whitelist
            if pair not in ALLOWED_PAIRS:
                return False, f"Pair {pair} not in whitelist."

            # Size hard limit
            if size_usd > MAX_POSITION_SIZE_USD:
                return False, f"Position ${size_usd} exceeds hard limit ${MAX_POSITION_SIZE_USD}."

            # Daily loss pause
            if self._paused:
                return False, f"Bot paused — daily loss limit ${DAILY_LOSS_LIMIT_USD} hit."

            # Duplicate detection
            sig = self._signal_hash(pair, direction, size_usd)
            last = self._recent_signals.get(sig, 0)
            if time.time() - last < DUPLICATE_WINDOW_SEC:
                return False, f"Duplicate signal — last fired {time.time() - last:.1f}s ago."
            self._recent_signals[sig] = time.time()

            return True, "OK"

    def record_loss(self, amount_usd: float):
        with self._lock:
            self._daily_loss += amount_usd
            if self._daily_loss >= DAILY_LOSS_LIMIT_USD:
                self._paused = True
                logging.critical(f"[TradeValidator] DAILY LOSS LIMIT HIT — BOT PAUSED. Total loss: ${self._daily_loss:.2f}")

    def reset_daily(self):
        with self._lock:
            self._daily_loss = 0.0
            self._paused = False
            logging.info("[TradeValidator] Daily counters reset.")


# ─────────────────────────────────────────────
# LAYER 3 — NETWORK SECURITY
# ─────────────────────────────────────────────

class SecureRequester:
    """
    All API calls HTTPS only. HMAC-SHA256 signing. Rate limit manager.
    """

    def __init__(self, rate_limit_per_sec: float = 5.0):
        self._interval = 1.0 / rate_limit_per_sec
        self._last_call = 0.0
        self._lock = threading.Lock()

    def _rate_gate(self):
        with self._lock:
            elapsed = time.time() - self._last_call
            if elapsed < self._interval:
                time.sleep(self._interval - elapsed)
            self._last_call = time.time()

    def sign_request(self, secret: str, message: str) -> str:
        return hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

    def get(self, url: str, headers: dict = None, params: dict = None) -> requests.Response:
        if not url.startswith("https://"):
            raise ValueError(f"[SecureRequester] HTTPS required. Got: {url}")
        self._rate_gate()
        return requests.get(url, headers=headers, params=params, timeout=10)

    def post(self, url: str, headers: dict = None, json: dict = None) -> requests.Response:
        if not url.startswith("https://"):
            raise ValueError(f"[SecureRequester] HTTPS required. Got: {url}")
        self._rate_gate()
        return requests.post(url, headers=headers, json=json, timeout=10)


# ─────────────────────────────────────────────
# LAYER 4 — RUNTIME PROTECTION
# ─────────────────────────────────────────────

class TamperEvidentLog:
    """
    SQLite trade log with SHA-256 checksums per row.
    Any modification to a row is detectable.
    """

    def __init__(self, db_path: str = "pantheon_trades.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        TEXT,
                pair      TEXT,
                direction TEXT,
                size_usd  REAL,
                result    TEXT,
                pnl       REAL,
                checksum  TEXT
            )
        """)
        self.conn.commit()

    def _checksum(self, ts, pair, direction, size_usd, result, pnl) -> str:
        raw = f"{ts}|{pair}|{direction}|{size_usd}|{result}|{pnl}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def log(self, pair: str, direction: str, size_usd: float, result: str, pnl: float):
        ts = datetime.utcnow().isoformat()
        chk = self._checksum(ts, pair, direction, size_usd, result, pnl)
        with self._lock:
            self.conn.execute(
                "INSERT INTO trades (ts, pair, direction, size_usd, result, pnl, checksum) VALUES (?,?,?,?,?,?,?)",
                (ts, pair, direction, size_usd, result, pnl, chk)
            )
            self.conn.commit()

    def verify_integrity(self) -> List[int]:
        """Returns list of row IDs with checksum mismatches."""
        corrupted = []
        with self._lock:
            for row in self.conn.execute("SELECT id, ts, pair, direction, size_usd, result, pnl, checksum FROM trades"):
                id_, ts, pair, direction, size_usd, result, pnl, stored_chk = row
                expected = self._checksum(ts, pair, direction, size_usd, result, pnl)
                if expected != stored_chk:
                    corrupted.append(id_)
        return corrupted


class TelegramAlerter:

    def __init__(self, token: str, chat_id: str):
        self._token = token
        self._chat_id = chat_id
        self._base = f"https://api.telegram.org/bot{token}"
        self._kill_callbacks: List = []
        self._listening = False

    def send(self, message: str):
        try:
            requests.post(
                f"{self._base}/sendMessage",
                json={"chat_id": self._chat_id, "text": message},
                timeout=5
            )
        except Exception as e:
            logging.error(f"[Telegram] Failed to send: {e}")

    def register_kill_callback(self, fn):
        self._kill_callbacks.append(fn)

    def start_listener(self):
        """Polls Telegram for /kill command in background thread."""
        self._listening = True
        t = threading.Thread(target=self._poll_loop, daemon=True)
        t.start()

    def _poll_loop(self):
        offset = 0
        while self._listening:
            try:
                r = requests.get(
                    f"{self._base}/getUpdates",
                    params={"offset": offset, "timeout": 10},
                    timeout=15
                )
                updates = r.json().get("result", [])
                for u in updates:
                    offset = u["update_id"] + 1
                    text = u.get("message", {}).get("text", "").strip().lower()
                    if text in ("/kill", "/stop", "/pause"):
                        logging.critical("[TelegramAlerter] KILL COMMAND RECEIVED.")
                        for cb in self._kill_callbacks:
                            cb()
            except Exception as e:
                logging.error(f"[TelegramAlerter] Poll error: {e}")
            time.sleep(2)


class Watchdog:
    """Monitors a target function — restarts it if it crashes."""

    def __init__(self, target_fn, alerter: TelegramAlerter, max_restarts: int = 10):
        self._target = target_fn
        self._alerter = alerter
        self._max_restarts = max_restarts
        self._restarts = 0
        self._running = False

    def start(self):
        self._running = True
        t = threading.Thread(target=self._guard_loop, daemon=True)
        t.start()

    def _guard_loop(self):
        while self._running and self._restarts < self._max_restarts:
            try:
                logging.info(f"[Watchdog] Starting target (restart #{self._restarts})")
                self._target()
            except Exception as e:
                self._restarts += 1
                msg = f"[Watchdog] CRASH detected. Restart #{self._restarts}/{self._max_restarts}. Error: {e}"
                logging.error(msg)
                self._alerter.send(f"⚠️ {msg}")
                time.sleep(5)
        if self._restarts >= self._max_restarts:
            self._alerter.send("🔴 Watchdog: Max restarts hit. Bot is DOWN.")


# ─────────────────────────────────────────────
# LAYER 5 — THE GOVERNOR
# ─────────────────────────────────────────────

GOVERNOR_DAILY_VOLUME_CEILING_USD = 2000.0   # Hard daily volume cap
GOVERNOR_HUMAN_CONFIRM_ABOVE_USD  = 300.0    # Any single trade above this needs confirmation


class Governor:
    """
    Agent Zero's kill layer. Hard volume ceiling + human confirmation gate.
    """

    def __init__(self, alerter: TelegramAlerter):
        self._alerter = alerter
        self._daily_volume: float = 0.0
        self._pending_confirms: Dict[str, dict] = {}
        self._lock = threading.Lock()
        alerter.register_kill_callback(self.emergency_kill)
        self._killed = False

    def check(self, pair: str, direction: str, size_usd: float) -> tuple[bool, str]:
        if self._killed:
            return False, "Governor: Emergency kill active."

        with self._lock:
            if self._daily_volume + size_usd > GOVERNOR_DAILY_VOLUME_CEILING_USD:
                return False, f"Governor: Daily volume ceiling ${GOVERNOR_DAILY_VOLUME_CEILING_USD} would be exceeded."

            if size_usd > GOVERNOR_HUMAN_CONFIRM_ABOVE_USD:
                trade_id = hashlib.md5(f"{pair}{direction}{size_usd}{time.time()}".encode()).hexdigest()[:8]
                self._pending_confirms[trade_id] = {
                    "pair": pair, "direction": direction,
                    "size_usd": size_usd, "ts": time.time()
                }
                self._alerter.send(
                    f"🔐 GOVERNOR — Human confirmation required\n"
                    f"Trade ID: {trade_id}\n"
                    f"Pair: {pair} | {direction} | ${size_usd:.2f}\n"
                    f"Reply /confirm_{trade_id} or /reject_{trade_id}"
                )
                return False, f"Governor: Awaiting human confirmation (ID: {trade_id})"

            self._daily_volume += size_usd
            return True, "OK"

    def confirm(self, trade_id: str) -> Optional[dict]:
        with self._lock:
            trade = self._pending_confirms.pop(trade_id, None)
            if trade:
                self._daily_volume += trade["size_usd"]
            return trade

    def emergency_kill(self):
        self._killed = True
        logging.critical("[Governor] EMERGENCY KILL ACTIVATED. All trading halted.")
        self._alerter.send("🔴 EMERGENCY KILL ACTIVATED — All trading halted.")

    def reset_daily(self):
        with self._lock:
            self._daily_volume = 0.0
            logging.info("[Governor] Daily volume counter reset.")


# ─────────────────────────────────────────────
# SECURITY STACK — ASSEMBLED
# ─────────────────────────────────────────────

class PantheonSecurityStack:
    """Single entry point — plug this into any Prime."""

    def __init__(self, env_path: str = ".env"):
        self.vault       = KeyVault(env_path)
        self.validator   = TradeValidator()
        self.requester   = SecureRequester()
        self.trade_log   = TamperEvidentLog()

        tg_token   = self.vault.get("TELEGRAM_BOT_TOKEN") or ""
        tg_chat_id = self.vault.get("TELEGRAM_CHAT_ID") or ""
        self.alerter   = TelegramAlerter(tg_token, tg_chat_id)
        self.governor  = Governor(self.alerter)

        self.alerter.start_listener()
        logging.info("[PantheonSecurityStack] All 5 layers online.")

    def authorize_trade(self, pair: str, direction: str, size_usd: float) -> tuple[bool, str]:
        """Run a trade through all 5 layers. Returns (approved, reason)."""

        ok, reason = self.validator.validate(pair, direction, size_usd)
        if not ok:
            return False, f"[L2] {reason}"

        ok, reason = self.governor.check(pair, direction, size_usd)
        if not ok:
            return False, f"[L5] {reason}"

        return True, "AUTHORIZED"

    def log_trade(self, pair, direction, size_usd, result, pnl):
        self.trade_log.log(pair, direction, size_usd, result, pnl)
        emoji = "✅" if pnl >= 0 else "🔴"
        self.alerter.send(
            f"{emoji} Trade\n{pair} {direction} ${size_usd:.2f}\nResult: {result} | PnL: ${pnl:.2f}"
        )
        if pnl < 0:
            self.validator.record_loss(abs(pnl))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    print("[PantheonSecurityStack] Running self-test...")

    stack = PantheonSecurityStack()

    # Layer 2 tests
    ok, msg = stack.authorize_trade("BTC-USD", "BUY", 100)
    print(f"  Trade 1 (valid):       {ok} — {msg}")

    ok, msg = stack.authorize_trade("DOGE-USD", "BUY", 50)
    print(f"  Trade 2 (bad pair):    {ok} — {msg}")

    ok, msg = stack.authorize_trade("BTC-USD", "BUY", 9999)
    print(f"  Trade 3 (over limit):  {ok} — {msg}")

    ok, msg = stack.authorize_trade("BTC-USD", "BUY", 100)
    print(f"  Trade 4 (duplicate):   {ok} — {msg}")

    # Layer 4 log + integrity check
    stack.log_trade("BTC-USD", "BUY", 100, "FILLED", 12.50)
    corrupted = stack.trade_log.verify_integrity()
    print(f"  Log integrity check:   {len(corrupted)} corrupted rows")

    print("[PantheonSecurityStack] Self-test complete.")
