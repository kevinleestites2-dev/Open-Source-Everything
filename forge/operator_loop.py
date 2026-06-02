"""
PropPilot Full Operator Loop
=============================
The autonomous revenue engine. Runs on GitHub Actions every 6 hours.

Cycle:
  1. Run ScoutPrime -> pull latest Lee County auctions
  2. Skip trace new leads (BatchData) -> get owner phones
  3. Aria dials each phone -> qualifies seller
  4. Hot leads -> Telegram alert + Stripe link
  5. EmailOctopus follow-up -> nurture cold leads
  6. Report P&L to Telegram
"""

import os
import sys
import json
import time
import subprocess
import requests
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT  = os.getenv("TELEGRAM_CHAT_ID")
EO_API_KEY     = os.getenv("EO_API_KEY")
EO_LIST_ID     = "2f14af34-2a2f-11f1-bfee-4dc30cc37367"
STRIPE_LINK    = "https://buy.stripe.com/aFadR2fG22C02Fg5Ma8Ra00"
CALLS_PER_RUN  = int(os.getenv("CALLS_PER_RUN", "5"))

WORKSPACE = Path(__file__).parent.parent
LOG_DIR   = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
WAR_CHEST_LOG = LOG_DIR / "war_chest.json"


# ── Telegram ──────────────────────────────────────────────────────────────────
def tg(msg: str):
    if not TELEGRAM_TOKEN:
        print(f"[TG] {msg[:80]}")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": msg, "parse_mode": "Markdown"},
            timeout=10,
        )
    except Exception as e:
        print(f"[TG] {e}")


# ── War Chest ─────────────────────────────────────────────────────────────────
def load_war_chest() -> dict:
    if WAR_CHEST_LOG.exists():
        with open(WAR_CHEST_LOG) as f:
            return json.load(f)
    return {"total_revenue": 0.0, "deals": [], "consults_booked": 0, "calls_made": 0}


def save_war_chest(wc: dict):
    with open(WAR_CHEST_LOG, "w") as f:
        json.dump(wc, f, indent=2)


# ── EmailOctopus ──────────────────────────────────────────────────────────────
def send_eo_followup(email: str, address: str, owner: str = "") -> bool:
    if not email or not EO_API_KEY:
        return False
    url = f"https://emailoctopus.com/api/1.6/lists/{EO_LIST_ID}/contacts"
    payload = {
        "api_key": EO_API_KEY,
        "email_address": email,
        "fields": {
            "FirstName": owner.split()[0] if owner else "Property Owner",
            "LastName": owner.split()[-1] if owner and len(owner.split()) > 1 else "",
        },
        "tags": ["proppilot-outreach", "aria-called", "lee-county"],
        "status": "SUBSCRIBED",
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.ok or r.status_code == 422
    except Exception as e:
        print(f"[EO] {e}")
        return False


def get_eo_lead_count() -> int:
    if not EO_API_KEY:
        return 0
    url = f"https://emailoctopus.com/api/1.6/lists/{EO_LIST_ID}"
    try:
        r = requests.get(url, params={"api_key": EO_API_KEY}, timeout=10)
        if r.ok:
            return r.json().get("counts", {}).get("subscribed", 0)
    except Exception:
        pass
    return 0


# ── Scout ─────────────────────────────────────────────────────────────────────
def run_scout() -> str:
    import glob
    for script_name in ["scout_prime_v4.py", "scout_prime_v3.py", "scoutprime_v2.py"]:
        script = WORKSPACE / script_name
        if script.exists():
            print(f"[SCOUT] Running {script_name}...")
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True, text=True, timeout=120, cwd=str(WORKSPACE),
            )
            if result.returncode == 0:
                files = sorted(glob.glob(str(WORKSPACE / "scout_v4_*.json")))
                if files:
                    return files[-1]
            else:
                print(f"[SCOUT] Error: {result.stderr[:200]}")

    files = sorted(glob.glob(str(WORKSPACE / "scout_v4_*.json")))
    if files:
        print(f"[SCOUT] Using cached: {files[-1]}")
        return files[-1]
    return ""


# ── Skip Trace ────────────────────────────────────────────────────────────────
def run_skip_trace(scout_file: str) -> list:
    try:
        from skip_trace import build_call_list
        return build_call_list(scout_file, limit=CALLS_PER_RUN * 2)
    except Exception as e:
        print(f"[SKIP TRACE] {e}")
    with open(scout_file) as f:
        d = json.load(f)
    leads = d.get("all_leads", [])
    return [l for l in leads if "Tier 1" in l.get("tier", "")][:CALLS_PER_RUN * 2]


# ── Aria Campaign — uses run_call() from aria_sip.py ─────────────────────────
def run_aria_campaign(call_list: list) -> dict:
    """
    Calls each lead using aria_sip.run_call().
    Returns summary dict.
    """
    try:
        from aria_sip import run_call
    except ImportError as e:
        print(f"[ARIA] Import error: {e}")
        return {"called": 0, "hot": 0, "cold": 0, "no_answer": 0, "errors": 1}

    results = {"called": 0, "hot": 0, "cold": 0, "no_answer": 0, "errors": 0}
    hot_leads = []

    for contact in call_list[:CALLS_PER_RUN]:
        phone   = contact.get("phone", "")
        address = contact.get("clean_address", contact.get("address", "Unknown property"))
        owner   = contact.get("owner", "Owner")

        if not phone:
            print(f"[ARIA] No phone for {address} — skipping")
            results["no_answer"] += 1
            continue

        print(f"[ARIA] Calling {phone} — {address}")
        try:
            outcome = run_call(phone, address, owner)
            status  = outcome.get("status", "ERROR")
            results["called"] += 1

            if status == "HOT_LEAD":
                results["hot"] += 1
                hot_leads.append(outcome)
            elif status == "COLD_LEAD":
                results["cold"] += 1
            elif status == "NO_ANSWER":
                results["no_answer"] += 1
            else:
                results["errors"] += 1

        except Exception as e:
            print(f"[ARIA] Error on {phone}: {e}")
            results["errors"] += 1

        time.sleep(3)  # Pause between calls

    # Update war chest with calls made
    wc = load_war_chest()
    wc["calls_made"] += results["called"]
    wc["consults_booked"] += results["hot"]
    save_war_chest(wc)

    return results


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n{'='*55}")
    print(f"PropPilot Operator Loop — {now}")
    print(f"{'='*55}\n")

    tg(f"*PropPilot Engine Starting*\n{now}")

    # 1. Scout
    print("[1/5] ScoutPrime...")
    scout_file = run_scout()
    if not scout_file:
        tg("ScoutPrime failed — no lead data. Aborting cycle.")
        return

    # 2. Skip Trace
    print("[2/5] Skip tracing leads...")
    call_list = run_skip_trace(scout_file)
    print(f"  {len(call_list)} leads ready")

    # 3. Aria Calls
    print(f"[3/5] Aria campaign ({CALLS_PER_RUN} calls)...")
    call_results = run_aria_campaign(call_list)

    # 4. EmailOctopus
    print("[4/5] EmailOctopus nurture...")
    nurture_count = 0
    for lead in call_list[:CALLS_PER_RUN]:
        if send_eo_followup(lead.get("email", ""), lead.get("clean_address", ""), lead.get("owner", "")):
            nurture_count += 1
    print(f"  {nurture_count} leads added to email sequence")

    # 5. Report
    print("[5/5] Report...")
    wc = load_war_chest()
    eo_count = get_eo_lead_count()

    with open(scout_file) as f:
        scout_data = json.load(f)
    summary = scout_data.get("summary", {})

    sip_status = "SIP live" if os.getenv("SIP_USER") else "No SIP creds — add voip.ms secrets"
    bd_status  = "Skip trace active" if os.getenv("BATCHDATA_API_KEY") else "No BatchData key"

    report = (
        f"*PropPilot Engine Report*\n"
        f"{now}\n\n"
        f"*SCOUT*\n"
        f"Tier 1 distressed: {summary.get('tier1_distressed', 0)}\n"
        f"Tier 2 mid-range:  {summary.get('tier2_midrange', 0)}\n"
        f"Tier 3 luxury:     {summary.get('tier3_luxury', 0)}\n\n"
        f"*ARIA*\n"
        f"Calls: {call_results['called']} | Hot: {call_results['hot']} | "
        f"Cold: {call_results['cold']} | No answer: {call_results['no_answer']}\n\n"
        f"*EMAIL*\n"
        f"EO subscribers: {eo_count} | Added: {nurture_count}\n\n"
        f"*WAR CHEST*\n"
        f"Revenue: ${wc['total_revenue']:,.0f} | Deals: {len(wc.get('deals', []))}\n"
        f"Total calls: {wc.get('calls_made', 0)}\n\n"
        f"*STATUS*\n"
        f"{sip_status}\n"
        f"{bd_status}\n\n"
        f"PropPilot AI — Autonomous"
    )

    print("\n" + report)
    tg(report)
    print("\n[DONE] Cycle complete.")


if __name__ == "__main__":
    run()
