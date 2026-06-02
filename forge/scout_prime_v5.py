"""
ScoutPrime v5.0 — Firecrawl Edition
Lee County, FL — Foreclosures + Tax Deeds + GSA Vehicles
Pantheon Engine | OrionPrime Feed

Powered by Firecrawl — handles JS-rendered pages, CAPTCHAs, dynamic content.
"""

import os, json, re, time
from datetime import datetime, date

import requests
import sys
from pathlib import Path

# ── SAFLA v2.0 Integration ──────────────────────────────────────────────────
# We look for safla-v2 in the current directory (standard Pantheon layout)
safla_path = Path(__file__).parent / "safla-v2"
if safla_path.exists():
    sys.path.append(str(safla_path.absolute()))
    try:
        from bridge import SAFLABridge
        SAFLA = SAFLABridge("ScoutPrime")
        HAS_SAFLA = True
    except ImportError:
        HAS_SAFLA = False
else:
    HAS_SAFLA = False

# ── CONFIG ───────────────────────────────────────────────────────────────────
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
FIRECRAWL_SCRAPE  = "https://api.firecrawl.dev/v1/scrape"

TIMESTAMP   = datetime.now().strftime("%Y%m%d_%H%M%S")
TODAY       = date.today()
COUNTY_FIPS = "12071"  # Lee County FL

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.join(BASE_DIR, "scout_output")


# ── FIRECRAWL CORE ───────────────────────────────────────────────────────────
def firecrawl_scrape(url: str, wait_for: int = 3000) -> str:
    """Scrape URL via Firecrawl, return markdown text. Returns '' on failure."""
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "url": url,
        "formats": ["markdown"],
        "waitFor": wait_for,
        "timeout": 35000,
    }
    try:
        r = requests.post(FIRECRAWL_SCRAPE, headers=headers, json=payload, timeout=50)
        r.raise_for_status()
        return r.json().get("data", {}).get("markdown", "")
    except Exception as e:
        print(f"  [Firecrawl ERROR] {url}: {e}")
        return ""


# ── TIER CLASSIFICATION ───────────────────────────────────────────────────────
def classify_tier(price):
    if price is None:
        return "Unknown"
    if price <= 120000:
        return "Tier 1 🔥 DISTRESSED"
    elif price <= 400000:
        return "Tier 2 💼 MID-RANGE"
    else:
        return "Tier 3 💎 LUXURY"


def extract_price(text):
    if not text:
        return None
    nums = re.sub(r"[^\d]", "", str(text))
    return int(nums) if nums else None


# ── SOURCE 1: PropertyOnion ───────────────────────────────────────────────────
def scout_propertyonion(pages=3) -> list:
    print(f"\n[ScoutPrime v5] 📡 PropertyOnion — Lee County ({pages} pages)...")
    all_leads = []
    for p in range(1, pages + 1):
        url = (
            f"https://propertyonion.com/property_search"
            f"?view_type=list&fips={COUNTY_FIPS}&status=upcoming&page={p}"
        )
        print(f"  Fetching page {p}...", end=" ", flush=True)
        text = firecrawl_scrape(url, wait_for=3000)
        leads = _parse_propertyonion(text)
        print(f"{len(leads)} leads")
        all_leads.extend(leads)
        time.sleep(0.8)
    return all_leads


def _parse_propertyonion(text: str) -> list:
    leads = []
    chunks = re.split(r"(?=\d{2}/\d{2}/\d{4})", text)

    for chunk in chunks:
        chunk = chunk.strip()
        if len(chunk) < 20:
            continue

        date_match = re.search(r"(\d{2}/\d{2}/\d{4})", chunk)
        if not date_match:
            continue
        auction_date = date_match.group(1)

        # Price — markdown may escape $ as \$
        price_match = re.search(r"\\?\$([\d,]+)", chunk)
        raw_price   = f"${price_match.group(1)}" if price_match else None
        price_val   = extract_price(raw_price)

        # Status
        if "Sold for" in chunk:
            status = "Sold"
        elif "Canceled" in chunk:
            status = "Canceled"
        else:
            status = "Active"

        # Type
        if "Foreclosure" in chunk:
            ptype = "Foreclosure"
        elif "Tax Deed" in chunk:
            ptype = "Tax Deed"
        else:
            ptype = "Unknown"

        # Address
        addr_match = re.search(
            r"(\d+[^,\n]+(?:St|Ave|Blvd|Dr|Rd|Ln|Way|Pkwy|Ct|Pl|Ter|Cir|Loop)[^,\n]*"
            r",\s*[^,\n]+,\s*FL\s+\d{5})",
            chunk,
        )
        if not addr_match:
            addr_match = re.search(
                r"(\d+\s+\w[^,\n]+,\s*"
                r"(?:Fort Myers|Cape Coral|Lehigh Acres|Bonita Springs|Estero|"
                r"Sanibel|Alva|North Fort Myers|Fort Myers Beach|Captiva|"
                r"Saint James City|Punta Gorda)"
                r"[^,\n]*,\s*FL\s+\d{5})",
                chunk,
            )
        address = addr_match.group(1).strip() if addr_match else None

        beds  = re.search(r"(\d+)\s*Beds?",       chunk, re.I)
        baths = re.search(r"([\d.]+)\s*Baths?",   chunk, re.I)
        sqft  = re.search(r"([\d,]+)\s*sqft",     chunk, re.I)

        if address:
            leads.append({
                "source":       "PropertyOnion",
                "market":       "real_estate",
                "address":      address,
                "type":         ptype,
                "auction_date": auction_date,
                "status":       status,
                "price":        raw_price,
                "price_val":    price_val,
                "beds":         beds.group(1)  if beds  else "?",
                "baths":        baths.group(1) if baths else "?",
                "sqft":         sqft.group(1)  if sqft  else "?",
                "tier":         classify_tier(price_val),
            })
    return leads


# ── SOURCE 2: Lee County Tax Deeds (lee.realtaxdeed.com) ─────────────────────
def scout_realtaxdeed() -> list:
    print("\n[ScoutPrime v5] 📡 lee.realtaxdeed.com — upcoming auctions...")
    # The auction preview page (public, no login required for upcoming list)
    url = (
        "https://lee.realtaxdeed.com/index.cfm"
        "?zaction=AUCTION&Zmethod=PREVIEW&AUCTIONDATE=upcoming"
    )
    text = firecrawl_scrape(url, wait_for=4500)
    leads = _parse_auction_platform(text, source="lee.realtaxdeed.com", ptype="Tax Deed")
    print(f"  -> {len(leads)} tax deed listings")
    return leads


# ── SOURCE 3: Lee County Foreclosures (lee.realforeclose.com) ────────────────
def scout_realforeclose() -> list:
    print("\n[ScoutPrime v5] 📡 lee.realforeclose.com — upcoming auctions...")
    url = (
        "https://www.lee.realforeclose.com/index.cfm"
        "?zaction=AUCTION&Zmethod=PREVIEW&AUCTIONDATE=upcoming"
    )
    text = firecrawl_scrape(url, wait_for=4500)
    leads = _parse_auction_platform(text, source="lee.realforeclose.com", ptype="Foreclosure")
    print(f"  -> {len(leads)} foreclosure listings")
    return leads


def _parse_auction_platform(text: str, source: str, ptype: str) -> list:
    """Parse the realtaxdeed/realforeclose auction preview pages."""
    leads = []
    if not text:
        return leads

    # Look for case blocks — pattern: Case# / address / opening bid
    entries = re.findall(
        r"(Case\s*[#:]?\s*[\w-]+.{0,400}?(?=Case\s*[#:]?|$))",
        text, re.DOTALL | re.IGNORECASE,
    )

    if not entries:
        # Fallback: look for Florida addresses with dollar amounts
        blocks = re.findall(
            r"(\d+[^,\n]{5,50},\s*(?:Fort Myers|Cape Coral|Lehigh Acres|Bonita|"
            r"Estero|Sanibel|Alva|Naples)[^,\n]*,\s*FL\s*\d{5}.*?(?:\$[\d,]+|$))",
            text, re.IGNORECASE | re.DOTALL,
        )
        for b in blocks[:30]:
            price_m = re.search(r"\\?\$([\d,]+)", b)
            leads.append({
                "source":    source,
                "market":    "real_estate",
                "type":      ptype,
                "case":      "—",
                "address":   b[:120].strip(),
                "price":     f"${price_m.group(1)}" if price_m else None,
                "price_val": extract_price(price_m.group(1)) if price_m else None,
                "tier":      classify_tier(extract_price(price_m.group(1)) if price_m else None),
                "status":    "Active",
            })
        return leads

    for entry in entries[:60]:
        entry = entry.strip()
        case_m  = re.search(r"Case\s*[#:]?\s*([\w-]+)", entry, re.I)
        addr_m  = re.search(
            r"(\d+[^,\n]+(?:St|Ave|Blvd|Dr|Rd|Ln|Way|Pkwy|Ct|Pl|Ter)[^,\n]*"
            r",\s*[^,\n]+,\s*FL\s+\d{5})",
            entry,
        )
        price_m = re.search(r"\\?\$([\d,]+)", entry)
        date_m  = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", entry)

        leads.append({
            "source":       source,
            "market":       "real_estate",
            "type":         ptype,
            "case":         case_m.group(1) if case_m else "Unknown",
            "address":      addr_m.group(1).strip() if addr_m else entry[:100],
            "auction_date": date_m.group(1) if date_m else "?",
            "price":        f"${price_m.group(1)}" if price_m else None,
            "price_val":    extract_price(price_m.group(1)) if price_m else None,
            "tier":         classify_tier(extract_price(price_m.group(1)) if price_m else None),
            "status":       "Active",
        })
    return leads


# ── SOURCE 4: GSA Government Vehicle Auctions ────────────────────────────────
def scout_gsa_vehicles(pages=2) -> list:
    print(f"\n[ScoutPrime v5] 📡 GSA Government Vehicle Auctions ({pages} pages)...")
    all_leads = []

    for p in range(1, pages + 1):
        url = (
            "https://gsaauctions.gov/auctions/auctions-list"
            f"?page={p}&size=50&status=active&sort=auctionEndDateSoon,DESC"
            "&category=Vehicles"
        )
        print(f"  Fetching page {p}...", end=" ", flush=True)
        text = firecrawl_scrape(url, wait_for=5000)
        leads = _parse_gsa(text)
        print(f"{len(leads)} vehicle leads")
        all_leads.extend(leads)
        time.sleep(0.8)

    return all_leads


def _parse_gsa(text: str) -> list:
    """Parse GSA auction list markdown. Lots have Lot Name / Location / Closing Date / Current Bid."""
    leads = []
    if not text:
        return leads

    # Split on "Lot Name" blocks
    chunks = re.split(r"\*\*Lot Name\*\*", text)

    for chunk in chunks[1:]:  # Skip header
        name_match    = re.search(r"^(.+?)(?:\n|$)", chunk.strip())
        loc_match     = re.search(r"\*\*Location\*\*\s*(.+?)(?:\n|$)", chunk)
        close_match   = re.search(r"\*\*Closing Date\*\*\s*(.+?)(?:\n|$)", chunk)
        bid_match     = re.search(r"\*\*Current Bid\*\*\s*\\?\$([\d,]+)", chunk)
        bidders_match = re.search(r"\*\*No\. of Bidders\*\*\s*(\d+)", chunk)

        lot_name = name_match.group(1).strip() if name_match else "Unknown"

        # Filter to vehicles only
        veh_kws = ["vehicle","truck","car","suv","sedan","van","jeep","ford","chevy",
                   "chevrolet","dodge","toyota","pickup","fleet","automobile","bus",
                   "ambulance","humvee","military","utility"]
        if not any(k in lot_name.lower() for k in veh_kws):
            continue

        price_val = extract_price(bid_match.group(1)) if bid_match else None

        leads.append({
            "source":       "GSA Auctions",
            "market":       "vehicles",
            "type":         "Government Surplus Vehicle",
            "description":  lot_name,
            "location":     loc_match.group(1).strip() if loc_match else "?",
            "closing_date": close_match.group(1).strip() if close_match else "?",
            "price":        f"${bid_match.group(1)}" if bid_match else "No bids",
            "price_val":    price_val,
            "num_bidders":  int(bidders_match.group(1)) if bidders_match else 0,
            "status":       "Active",
            "tier":         classify_tier(price_val) if price_val else "Unknown",
        })

    return leads


# ── FILTER & RANK ─────────────────────────────────────────────────────────────
def filter_and_rank_re(leads):
    active  = [l for l in leads if l.get("status") not in ("Canceled", "Sold")]
    tier1   = sorted([l for l in active if "Tier 1" in l.get("tier","") and l.get("price_val")], key=lambda x: x["price_val"])
    tier2   = sorted([l for l in active if "Tier 2" in l.get("tier","") and l.get("price_val")], key=lambda x: x["price_val"])
    tier3   = sorted([l for l in active if "Tier 3" in l.get("tier","") and l.get("price_val")], key=lambda x: x["price_val"])
    unknown = [l for l in active if not l.get("price_val")]
    return tier1, tier2, tier3, unknown


# ── REPORT ────────────────────────────────────────────────────────────────────
def generate_report(re_leads, veh_leads):
    tier1, tier2, tier3, unknown = filter_and_rank_re(re_leads)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    report = {
        "generated":  TIMESTAMP,
        "county":     "Lee County, FL",
        "engine":     "ScoutPrime v5.0 — Firecrawl",
        "re_summary": {
            "total_scraped":     len(re_leads),
            "tier1_distressed":  len(tier1),
            "tier2_midrange":    len(tier2),
            "tier3_luxury":      len(tier3),
            "upcoming_no_price": len(unknown),
        },
        "vehicle_summary": {
            "total_found": len(veh_leads),
            "low_bidders": len([v for v in veh_leads if v.get("num_bidders", 0) <= 2]),
        },
        "top_tier1_leads":   tier1[:15],
        "top_tier2_leads":   tier2[:10],
        "top_tier3_leads":   tier3[:5],
        "upcoming_no_price": unknown[:10],
        "vehicle_leads":     sorted(veh_leads, key=lambda x: x.get("num_bidders", 99))[:20],
        "all_re_leads":      re_leads,
        "all_vehicle_leads": veh_leads,
    }

    fname = os.path.join(OUTPUT_DIR, f"scout_v5_{TIMESTAMP}.json")
    with open(fname, "w") as f:
        json.dump(report, f, indent=2)

    # ── SAFLA Reporting ──────────────────────────────────────────────────────
    if HAS_SAFLA:
        try:
            SAFLA.report_event(
                event_id=f"scout_run_{TIMESTAMP}",
                outcome_value=float(len(tier1)),
                metadata={
                    "total_re": len(re_leads),
                    "total_veh": len(veh_leads),
                    "tier1_count": len(tier1),
                    "tier2_count": len(tier2),
                    "tier3_count": len(tier3),
                }
            )
        except Exception as e:
            print(f"  [SAFLA ERROR] {e}")

    return report, fname


def print_report(report):
    s  = report["re_summary"]
    vs = report["vehicle_summary"]

    print("\n" + "="*65)
    print("  SCOUTPRIME v5.0 — FIRECRAWL EDITION — INTELLIGENCE REPORT")
    print(f"  {report['county']}  |  {report['generated']}")
    print("="*65)

    print(f"\n  📊 Real Estate — Total: {s['total_scraped']}")
    print(f"     🔥 Tier 1 Distressed  ($0-120k):   {s['tier1_distressed']}")
    print(f"     💼 Tier 2 Mid-Range   ($120-400k):  {s['tier2_midrange']}")
    print(f"     💎 Tier 3 Luxury      ($400k+):     {s['tier3_luxury']}")
    print(f"     📋 Upcoming (no price yet):         {s['upcoming_no_price']}")

    print(f"\n  🚗 Government Vehicles — Total: {vs['total_found']}")
    print(f"     💡 Low-competition (≤2 bidders):    {vs['low_bidders']}")

    # RE leads
    print("\n" + "-"*65)
    print("  🔥 TOP TIER 1 LEADS — Bird Dog Targets")
    print("-"*65)
    for l in report["top_tier1_leads"][:8]:
        src = l.get("source","?")
        print(f"  [{l.get('type','?')} | {src}]")
        print(f"    📍 {l.get('address','?')}")
        print(f"    📅 {l.get('auction_date','?')}  |  💰 {l.get('price','?')}  |  🛏 {l.get('beds','?')}bd/{l.get('baths','?')}ba  {l.get('sqft','?')}sqft")
        print()

    if report["top_tier2_leads"]:
        print("-"*65)
        print("  💼 TOP TIER 2 LEADS")
        print("-"*65)
        for l in report["top_tier2_leads"][:5]:
            print(f"  [{l.get('type','?')}] {l.get('address','?')}")
            print(f"    📅 {l.get('auction_date','?')}  |  💰 {l.get('price','?')}  |  🛏 {l.get('beds','?')}bd/{l.get('baths','?')}ba")
            print()

    if report["upcoming_no_price"]:
        print("-"*65)
        print("  📋 UPCOMING — No Price Set (Early Opportunity Window)")
        print("-"*65)
        for l in report["upcoming_no_price"][:6]:
            print(f"  [{l.get('type','?')}] {l.get('address','?')}  |  📅 {l.get('auction_date','?')}")

    # Vehicle leads
    if report["vehicle_leads"]:
        print("\n" + "-"*65)
        print("  🚗 GSA VEHICLE LEADS (sorted by lowest bidder count)")
        print("-"*65)
        for v in report["vehicle_leads"][:10]:
            bidders = v.get("num_bidders", "?")
            print(f"  {v.get('description','?')[:70]}")
            print(f"    📍 {v.get('location','?')}  |  💰 {v.get('price','?')}  |  👤 {bidders} bidder(s)  |  ⏰ {v.get('closing_date','?')}")
            print()

    print("="*65)
    print("  [ScoutPrime v5] Mission complete. Feeding OrionPrime. 🎯")
    print("="*65)


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not FIRECRAWL_API_KEY:
        print("[ScoutPrime v5] ERROR: FIRECRAWL_API_KEY not set.")
        print("  export FIRECRAWL_API_KEY='fc-xxxxxxxx'")
        exit(1)

    print("[ScoutPrime v5] 🔥 Firecrawl Edition — Igniting Pantheon Recon...")
    print(f"[ScoutPrime v5] Target: Lee County FL | {TODAY}")

    # ── Scrape All Sources ────────────────────────────────────────────────────
    po_leads  = scout_propertyonion(pages=3)       # PropertyOnion
    rtd_leads = scout_realtaxdeed()                # lee.realtaxdeed.com
    rf_leads  = scout_realforeclose()              # lee.realforeclose.com
    all_re    = po_leads + rtd_leads + rf_leads

    veh_leads = scout_gsa_vehicles(pages=2)        # GSA Vehicles

    print(f"\n[ScoutPrime v5] ✅ Total RE: {len(all_re)} | Vehicles: {len(veh_leads)}")

    if not all_re and not veh_leads:
        print("[ScoutPrime v5] ⚠️  No leads found. Check Firecrawl credits / site structure.")
    else:
        report, fname = generate_report(all_re, veh_leads)
        print_report(report)
        print(f"\n  💾 Saved -> {fname}")
