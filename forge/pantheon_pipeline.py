"""
PANTHEON PIPELINE — The Full Loop
Niche Finder → ContentPrime → GhostPrime

Dependencies (ALL Termux-safe, no Fortran/scipy/sklearn needed):
  pip install requests pandas kaggle

Flow:
1. Pull real trending YouTube data via Kaggle API (113 countries, updated daily)
2. Pure-numpy clustering surfaces top niches by engagement
3. ContentPrime generates the video
4. GhostPrime fires the boost
5. Telegram reports every step

Env vars:
  KAGGLE_API_TOKEN    — Kaggle key
  CONTENT_PRIME_URL   — ContentPrime API base (default: http://localhost:8080)
  GHOST_PRIME_URL     — GhostPrime trigger endpoint (optional)
  TELEGRAM_BOT_TOKEN  — Telegram bot token
  TELEGRAM_CHAT_ID    — Telegram chat ID
"""

import os
import json
import glob
import subprocess
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ─── CONFIG ───────────────────────────────────────────────────────────────────

CONTENT_PRIME_URL = os.getenv("CONTENT_PRIME_URL", "http://localhost:8080")
GHOST_PRIME_URL   = os.getenv("GHOST_PRIME_URL", "")
TELEGRAM_TOKEN    = os.getenv("TELEGRAM_BOT_TOKEN", "TG_TOKEN_INJECTED_AT_RUNTIME")
TELEGRAM_CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID", "7135054241")
KAGGLE_TOKEN      = os.getenv("KAGGLE_API_TOKEN", "KGAT_aeb6c1adc3e9ab6162c9006854f0177e")
KAGGLE_DATASET    = "asaniczka/trending-youtube-videos-113-countries"
DATA_DIR          = "./niche_data"

TARGET_COUNTRY    = "US"
MIN_ENGAGEMENT    = 10000
TOP_N_NICHES      = 5
VIDEO_ASPECT      = "9:16"
VOICE             = "en-US-AriaNeural"

# ─── TELEGRAM ─────────────────────────────────────────────────────────────────

def telegram(msg: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
    except Exception as e:
        print(f"[Telegram] {e}")

# ─── PURE NUMPY K-MEANS (no sklearn/scipy) ────────────────────────────────────

def numpy_kmeans(X: np.ndarray, k: int, max_iters: int = 100) -> np.ndarray:
    """Simple K-Means in pure numpy. No Fortran, no scipy, runs on any ARM."""
    np.random.seed(42)
    # Normalize
    mean = X.mean(axis=0)
    std  = X.std(axis=0) + 1e-9
    X_n  = (X - mean) / std

    # Init centroids by spread
    idx = np.random.choice(len(X_n), k, replace=False)
    centroids = X_n[idx]

    labels = np.zeros(len(X_n), dtype=int)
    for _ in range(max_iters):
        # Assign
        dists = np.linalg.norm(X_n[:, None, :] - centroids[None, :, :], axis=2)
        new_labels = dists.argmin(axis=1)
        if np.all(new_labels == labels):
            break
        labels = new_labels
        # Update centroids
        for c in range(k):
            members = X_n[labels == c]
            if len(members) > 0:
                centroids[c] = members.mean(axis=0)

    return labels

# ─── STEP 1: NICHE FINDER ─────────────────────────────────────────────────────

def fetch_trending_data() -> pd.DataFrame:
    """Pull real trending YouTube data from Kaggle. Falls back to sample data."""
    cached = glob.glob(f"{DATA_DIR}/*.csv")
    if cached:
        print(f"[NicheFinder] Loading cache: {cached[0]}")
        df = pd.read_csv(cached[0], low_memory=False)
        print(f"[NicheFinder] {len(df):,} rows.")
        return df

    if KAGGLE_TOKEN:
        print("[NicheFinder] Pulling from Kaggle...")
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            env = {**os.environ, "KAGGLE_API_TOKEN": KAGGLE_TOKEN}
            result = subprocess.run(
                ["kaggle", "datasets", "download",
                 "-d", KAGGLE_DATASET, "--unzip", "-p", DATA_DIR],
                capture_output=True, text=True, timeout=300, env=env
            )
            print(result.stdout[-300:] if result.stdout else "")
            if result.returncode != 0:
                print(f"[NicheFinder] Kaggle error: {result.stderr[-300:]}")
            csvs = glob.glob(f"{DATA_DIR}/*.csv")
            if csvs:
                df = pd.read_csv(csvs[0], low_memory=False)
                print(f"[NicheFinder] {len(df):,} rows downloaded.")
                return df
        except Exception as e:
            print(f"[NicheFinder] Kaggle failed: {e}")

    # Sample fallback
    print("[NicheFinder] Offline — using sample data.")
    rows = [
        ("AI tools that will blow your mind",        ["ai","technology","tools","future"],        980000, 45000),
        ("Real estate investing for beginners",       ["realestate","investing","money","wealth"], 750000, 38000),
        ("5 money habits of millionaires",            ["money","finance","millionaire","wealth"],  1200000, 62000),
        ("Florida housing market crash 2026",         ["realestate","florida","housing","crash"],  890000, 71000),
        ("How AI is replacing jobs in 2026",          ["ai","jobs","future","technology"],         1100000, 55000),
        ("Easiest side hustles from your phone",      ["sidehustle","money","passive","income"],   950000, 48000),
        ("The truth about crypto in 2026",            ["crypto","bitcoin","investing","finance"],  820000, 39000),
        ("Things nobody tells you about being broke", ["money","finance","survival","truth"],      1400000, 89000),
        ("How to flip furniture for profit",          ["flipping","furniture","money","hustle"],   670000, 31000),
        ("Secret apps that pay you real money",       ["apps","money","sidehustle","income"],      1050000, 58000),
    ]
    data = []
    for title, tags, views, eng in rows:
        data.append({
            "title": title, "tags": "|".join(tags),
            "view_count": views, "likes": int(eng * 0.85),
            "comment_count": int(eng * 0.15),
            "country": "US"
        })
    return pd.DataFrame(data)


def find_top_niches(df: pd.DataFrame) -> list:
    """Cluster by engagement using pure numpy K-Means. No sklearn needed."""
    print("[NicheFinder] Clustering...")
    df.columns = [c.lower().strip() for c in df.columns]

    # Country filter
    cc = next((c for c in df.columns if "country" in c), None)
    if cc:
        us = df[df[cc].astype(str).str.upper() == TARGET_COUNTRY]
        if len(us) > 100:
            df = us.copy()

    # Resolve column names
    like_col    = next((c for c in df.columns if "like" in c and "dislike" not in c), None)
    comment_col = next((c for c in df.columns if "comment" in c), None)
    view_col    = next((c for c in df.columns if "view" in c), None)
    title_col   = next((c for c in df.columns if "title" in c), None)
    tag_col     = next((c for c in df.columns if "tag" in c), None)

    df["_likes"]    = pd.to_numeric(df[like_col],    errors="coerce").fillna(0) if like_col    else 0
    df["_comments"] = pd.to_numeric(df[comment_col], errors="coerce").fillna(0) if comment_col else 0
    df["_views"]    = pd.to_numeric(df[view_col],    errors="coerce").fillna(0) if view_col    else 0
    df["_eng"]      = df["_likes"] + df["_comments"]

    df = df[df["_eng"] >= MIN_ENGAGEMENT].copy()
    if df.empty:
        df = df.copy()
        df["_eng"] = df["_likes"] + df["_comments"]

    # Cluster with pure numpy
    X = df[["_views", "_eng"]].values.astype(float)
    k = min(TOP_N_NICHES, len(df))
    labels = numpy_kmeans(X, k)
    df["_cluster"] = labels

    # Score clusters by mean engagement
    scores = df.groupby("_cluster")["_eng"].mean().sort_values(ascending=False)
    top_clusters = scores.head(TOP_N_NICHES).index.tolist()

    results = []
    for cid in top_clusters:
        cdf = df[df["_cluster"] == cid].sort_values("_eng", ascending=False)
        row = cdf.iloc[0]
        title = str(row[title_col]) if title_col else "trending topic"
        tags = []
        if tag_col and pd.notna(row.get(tag_col, "")):
            raw = str(row[tag_col]).replace("|", ",").replace('"', "")
            tags = [t.strip() for t in raw.split(",") if t.strip()][:5]
        results.append({
            "niche":            title,
            "tags":             tags,
            "engagement_score": int(cdf["_eng"].mean()),
            "view_count":       int(row["_views"]),
            "cluster_size":     len(cdf)
        })

    return results

# ─── STEP 2: CONTENT PRIME ────────────────────────────────────────────────────

def generate_video(niche: dict) -> dict:
    print(f"[ContentPrime] Sending: {niche['niche']}")
    payload = {
        "video_subject":      niche["niche"],
        "video_terms":        niche["tags"],
        "video_aspect":       VIDEO_ASPECT,
        "video_clip_duration": 4,
        "video_count":        1,
        "voice_name":         VOICE,
        "bgm_name":           "random",
        "font_size":          55,
        "text_color":         "#FFFFFF",
        "stroke_color":       "#000000",
        "stroke_width":       1.5,
        "subtitle_enabled":   True,
        "video_language":     "en-US",
        "paragraph_number":   3,
    }
    try:
        resp = requests.post(f"{CONTENT_PRIME_URL}/api/v1/videos", json=payload, timeout=300)
        if resp.status_code == 200:
            task_id = resp.json().get("data", {}).get("task_id", "")
            print(f"[ContentPrime] Task: {task_id}")
            return {"task_id": task_id, "subject": niche["niche"], "status": "queued"}
        print(f"[ContentPrime] Error {resp.status_code}: {resp.text[:200]}")
        return {"task_id": None, "subject": niche["niche"], "status": "error"}
    except Exception as e:
        print(f"[ContentPrime] Offline: {e}")
        return {"task_id": "pending", "subject": niche["niche"], "status": "pending_server"}


def poll_video_result(task_id: str, timeout_mins: int = 10) -> str:
    if not task_id or task_id == "pending":
        return ""
    import time
    deadline = datetime.now() + timedelta(minutes=timeout_mins)
    while datetime.now() < deadline:
        try:
            resp = requests.get(f"{CONTENT_PRIME_URL}/api/v1/tasks/{task_id}", timeout=30)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                if data.get("state") == 1:
                    vids = data.get("videos", [])
                    if vids:
                        return vids[0]
                elif data.get("state") == -1:
                    return ""
        except Exception:
            pass
        time.sleep(15)
    return ""

# ─── STEP 3: GHOST PRIME ──────────────────────────────────────────────────────

def fire_ghost_prime(video_url: str, niche: dict):
    if not GHOST_PRIME_URL or not video_url:
        print("[GhostPrime] No endpoint — skipping boost.")
        return
    try:
        resp = requests.post(GHOST_PRIME_URL, json={
            "target_url": video_url,
            "cycles": 50,
            "tags": niche.get("tags", []),
            "mode": "social_boost"
        }, timeout=30)
        print(f"[GhostPrime] {resp.status_code}")
    except Exception as e:
        print(f"[GhostPrime] {e}")

# ─── QUEUE ────────────────────────────────────────────────────────────────────

def save_queue(niche: dict):
    queue_file = "niche_queue.json"
    queue = []
    if os.path.exists(queue_file):
        with open(queue_file) as f:
            queue = json.load(f)
    queue.append({**niche, "queued_at": datetime.now().isoformat()})
    with open(queue_file, "w") as f:
        json.dump(queue, f, indent=2)
    print(f"[Queue] Saved → {queue_file}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def run_pipeline():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'='*60}\n🔱 PANTHEON PIPELINE — {ts}\n{'='*60}\n")
    telegram(f"🔱 *Pantheon Pipeline firing* — {ts}")

    # Step 1 — Find niche
    df     = fetch_trending_data()
    niches = find_top_niches(df)

    if not niches:
        telegram("❌ NicheFinder: No niches found.")
        return

    top = niches[0]
    print(f"\n🔥 TOP NICHE: {top['niche']}")
    print(f"   Tags:       {top['tags']}")
    print(f"   Engagement: {top['engagement_score']:,}")
    print(f"   Views:      {top['view_count']:,}")

    niche_list = "\n".join([
        f"{i+1}. {n['niche']} ({n['engagement_score']:,} eng)"
        for i, n in enumerate(niches)
    ])
    telegram(
        f"📊 *NicheFinder — Top Niche*\n"
        f"`{top['niche']}`\n"
        f"Tags: {', '.join(top['tags'])}\n"
        f"Engagement: {top['engagement_score']:,} | Views: {top['view_count']:,}\n\n"
        f"📋 *All Top {TOP_N_NICHES}:*\n{niche_list}"
    )

    # Step 2 — Generate video
    task = generate_video(top)

    if task["status"] == "pending_server":
        save_queue(top)
        telegram(
            f"⏳ *ContentPrime offline* — niche queued.\n"
            f"Subject: `{top['niche']}`\n"
            f"Start ContentPrime to render."
        )
        print("\n[Pipeline] Done — niche queued. Start ContentPrime to render.")
        return

    if task["status"] == "error":
        telegram("❌ ContentPrime: Video generation failed.")
        return

    # Step 3 — Wait for video
    video_url = poll_video_result(task["task_id"])

    if video_url:
        telegram(f"🎬 *Video Ready!*\nSubject: `{top['niche']}`\n{video_url}")
        fire_ghost_prime(video_url, top)
        if GHOST_PRIME_URL:
            telegram("👻 *GhostPrime boost fired.*")
    else:
        telegram(f"⚠️ Video timed out for: `{top['niche']}`")

    print(f"\n{'='*60}\n🔱 Pipeline complete.\n{'='*60}\n")


if __name__ == "__main__":
    run_pipeline()
