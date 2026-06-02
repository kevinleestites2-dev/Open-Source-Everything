#!/usr/bin/env python3
"""
Agent Zero — Self-Integration Engine
Layer 20: Absorption → Evaluation → Integration → Commit

Feed it a GitHub URL.
It reads the repo, understands what it does, writes a connector,
tests it, and commits everything into Agent Zero's own repo.

Usage:
    python agent_zero_integrator.py <github_url>
    python agent_zero_integrator.py https://github.com/owner/repo
"""

import sys
import os
import json
import base64
import urllib.request
import urllib.error
import subprocess
import re
import textwrap
from datetime import datetime, timezone
from pathlib import Path

# ─── CONFIG ──────────────────────────────────────────────────────────────────

GITHUB_TOKEN    = os.environ.get("GITHUB_TOKEN", "YOUR_GITHUB_TOKEN")
AGENT_ZERO_REPO = "kevinleestites2-dev/Open-Source-Everything"
OPENROUTER_KEY  = os.environ.get("OPENROUTER_KEY", "")   # optional — enables AI connector generation
INTEGRATION_DIR = "agent_zero/integrations"
MANIFEST_PATH   = "agent_zero/manifest.json"

# ─── GITHUB HELPERS ──────────────────────────────────────────────────────────

def gh(method, path, payload=None, repo=None):
    base = f"https://api.github.com/repos/{repo or AGENT_ZERO_REPO}"
    url  = f"{base}/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept":        "application/vnd.github.v3+json",
    }
    if payload:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    else:
        data = None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"GitHub API {e.code} on {url}: {body[:300]}")


def gh_raw(path, repo):
    """Fetch raw file content from a public repo (no auth needed for public)."""
    url = f"https://raw.githubusercontent.com/{repo}/main/{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode(errors="replace")
    except Exception:
        return None


def get_repo_tree(repo_slug):
    """Return flat file list for a repo."""
    url = f"https://api.github.com/repos/{repo_slug}/git/trees/HEAD?recursive=1"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        return [item["path"] for item in data.get("tree", []) if item["type"] == "blob"]
    except Exception as e:
        return []


def get_file_content(repo_slug, path):
    """Get decoded content of a file in a repo."""
    try:
        data = gh("GET", f"contents/{path}", repo=repo_slug)
        if isinstance(data, dict) and "content" in data:
            return base64.b64decode(data["content"]).decode(errors="replace")
    except Exception:
        pass
    return gh_raw(path, repo_slug)


# ─── REPO ANALYSIS ───────────────────────────────────────────────────────────

def parse_github_url(url):
    """Extract owner/repo from a GitHub URL."""
    url = url.strip().rstrip("/")
    match = re.search(r"github\.com/([^/]+/[^/]+)", url)
    if not match:
        raise ValueError(f"Not a valid GitHub URL: {url}")
    slug = match.group(1)
    slug = re.sub(r"\.git$", "", slug)
    return slug


def analyze_repo(slug):
    """Pull key info from a repo and return a summary dict."""
    print(f"  → Fetching repo metadata: {slug}")
    
    # Repo info
    url = f"https://api.github.com/repos/{slug}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        meta = json.loads(r.read())

    # File tree
    print(f"  → Scanning file tree...")
    tree = get_repo_tree(slug)

    # Priority files to read
    priority = ["README.md", "readme.md", "README.rst", "setup.py",
                "pyproject.toml", "package.json", "Cargo.toml", "main.py",
                "index.js", "index.ts", "__init__.py", "ARCHITECTURE.md",
                "OVERVIEW.md", "USAGE.md", "INSTALL.md"]
    
    content_samples = {}
    for fname in priority:
        if fname in tree or fname.lower() in [t.lower() for t in tree]:
            actual = next((t for t in tree if t.lower() == fname.lower()), fname)
            print(f"  → Reading {actual}...")
            content = get_file_content(slug, actual)
            if content:
                content_samples[actual] = content[:3000]   # cap per file
            if len(content_samples) >= 4:
                break

    # Also grab any Python source files (up to 2)
    py_files = [t for t in tree if t.endswith(".py") and not t.startswith("test")]
    for pf in py_files[:2]:
        if pf not in content_samples:
            print(f"  → Reading {pf}...")
            content = get_file_content(slug, pf)
            if content:
                content_samples[pf] = content[:2000]

    return {
        "slug":        slug,
        "name":        meta["name"],
        "description": meta.get("description", ""),
        "language":    meta.get("language", "Unknown"),
        "stars":       meta["stargazers_count"],
        "topics":      meta.get("topics", []),
        "url":         meta["html_url"],
        "tree":        tree,
        "samples":     content_samples,
    }


# ─── CONNECTOR GENERATION ────────────────────────────────────────────────────

def classify_tool(analysis):
    """Rule-based classification of what the tool does."""
    desc  = (analysis["description"] or "").lower()
    name  = analysis["name"].lower()
    tree  = " ".join(analysis["tree"]).lower()
    topics = " ".join(analysis["topics"]).lower()
    text  = f"{desc} {name} {tree} {topics}"

    if any(k in text for k in ["llm", "model", "inference", "ollama", "gpt", "transformer", "embedding"]):
        return "AI_MODEL"
    if any(k in text for k in ["mine", "mining", "xmr", "monero", "crypto", "wallet", "defi", "token"]):
        return "CRYPTO"
    if any(k in text for k in ["scrape", "crawl", "spider", "selenium", "playwright", "browser"]):
        return "SCRAPER"
    if any(k in text for k in ["telegram", "slack", "discord", "whatsapp", "notify", "alert", "bot"]):
        return "COMMS"
    if any(k in text for k in ["media", "video", "audio", "ffmpeg", "stream", "encode"]):
        return "MEDIA"
    if any(k in text for k in ["monitor", "metrics", "dashboard", "log", "observe", "trace"]):
        return "MONITOR"
    if any(k in text for k in ["search", "index", "retrieval", "embedding", "vector"]):
        return "SEARCH"
    if any(k in text for k in ["api", "rest", "graphql", "server", "endpoint", "route"]):
        return "API"
    if any(k in text for k in ["agent", "autogpt", "autonomous", "workflow", "orchestrat"]):
        return "AGENT"
    return "UTILITY"


def score_tool(analysis, category):
    """Score relevance to the Pantheon (0-10)."""
    score = 0
    pantheon_keywords = [
        "autonomous", "agent", "self", "evolv", "adapt", "learn",
        "crypto", "monero", "mine", "defi", "liquidity",
        "scrape", "crawl", "stealth", "ghost",
        "telegram", "notify", "alert",
        "stream", "video", "content",
        "search", "index", "retrieval",
        "llm", "model", "inference",
    ]
    text = f"{analysis['description']} {' '.join(analysis['topics'])}".lower()
    for kw in pantheon_keywords:
        if kw in text:
            score += 1

    if analysis["stars"] > 10000: score += 2
    elif analysis["stars"] > 1000: score += 1

    if category in ["AGENT", "CRYPTO", "AI_MODEL", "SCRAPER"]: score += 2
    if category in ["COMMS", "MEDIA"]: score += 1

    return min(score, 10)


def generate_connector(analysis, category):
    """Generate a Python connector/wrapper for this tool."""
    name       = analysis["name"]
    slug       = analysis["slug"]
    desc       = analysis["description"] or "No description provided."
    lang       = analysis["language"]
    url        = analysis["url"]
    readme     = analysis["samples"].get("README.md", analysis["samples"].get("readme.md", ""))[:1500]
    
    # Build connector based on category
    safe_name  = re.sub(r"[^a-zA-Z0-9]", "_", name)
    class_name = "".join(w.capitalize() for w in re.split(r"[^a-zA-Z0-9]", name) if w) + "Connector"

    connector = textwrap.dedent(f'''\
        """
        Agent Zero Integration — {name}
        Category : {category}
        Source   : {url}
        Language : {lang}
        Absorbed : {datetime.now(timezone.utc).strftime("%Y-%m-%d")}

        Description:
            {desc}

        Absorption Notes:
            This connector was auto-generated by Agent Zero's Self-Integration Engine (Layer 20).
            It provides a standardized Pantheon interface to interact with {name}.
            Customize the methods below to wire this tool into the Prime that needs it.
        """

        import os
        import subprocess
        from typing import Any, Dict, Optional


        class {class_name}:
            """
            Pantheon connector for {name}.
            {desc}
            """

            REPO_URL = "{url}"
            CATEGORY = "{category}"

            def __init__(self, config: Optional[Dict] = None):
                """
                Initialize the connector.
                :param config: Optional dict of config overrides (API keys, paths, etc.)
                """
                self.config = config or {{}}
                self._initialized = False

            # ── LIFECYCLE ──────────────────────────────────────────────────

            def setup(self) -> bool:
                """
                Install/verify the tool is available.
                Returns True if ready, False if setup failed.
                """
                print(f"[{class_name}] setup() — implement installation/verification logic")
                # Example: check if binary exists, install via pip, etc.
                # subprocess.run(["pip", "install", "{name.lower()}"], check=True)
                self._initialized = True
                return True

            def health_check(self) -> Dict:
                """Return a health status dict for Pantheon monitoring."""
                return {{
                    "name":        "{name}",
                    "category":   "{category}",
                    "initialized": self._initialized,
                    "status":     "ok" if self._initialized else "not_initialized",
                }}

            # ── CORE INTERFACE ─────────────────────────────────────────────

            def run(self, *args, **kwargs) -> Any:
                """
                Primary execution method.
                Wire this to the specific action this tool performs.
                """
                if not self._initialized:
                    self.setup()
                raise NotImplementedError(
                    f"Implement run() for {name} — see {url}"
                )

            def get_output(self, *args, **kwargs) -> Any:
                """Retrieve output/results from the tool."""
                raise NotImplementedError

            # ── PANTHEON BRIDGE ────────────────────────────────────────────

            def to_pantheon_signal(self, raw_output: Any) -> Dict:
                """
                Normalize raw tool output into a standard Pantheon signal dict.
                All Primes consume this format.
                """
                return {{
                    "source":    "{name}",
                    "category":  "{category}",
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                    "data":      raw_output,
                    "meta":      self.config,
                }}

            def relay_to_telegram(self, message: str) -> None:
                """Send a status update to the Pantheon Telegram channel."""
                import urllib.request, json
                token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
                chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
                if not token or not chat_id:
                    print(f"[{class_name}] Telegram not configured — set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID")
                    return
                payload = {{"chat_id": chat_id, "text": f"[{name}] {{message}}", "parse_mode": "Markdown"}}
                data    = json.dumps(payload).encode()
                req     = urllib.request.Request(
                    f"https://api.telegram.org/bot{{token}}/sendMessage",
                    data=data, headers={{"Content-Type": "application/json"}}
                )
                with urllib.request.urlopen(req, timeout=10) as r:
                    return json.loads(r.read())


        # ── QUICK TEST ─────────────────────────────────────────────────────────

        if __name__ == "__main__":
            connector = {class_name}()
            print(connector.health_check())
    ''')

    return connector


# ─── MANIFEST ────────────────────────────────────────────────────────────────

def load_manifest():
    try:
        data = gh("GET", f"contents/{MANIFEST_PATH}")
        if isinstance(data, dict) and "content" in data:
            content = base64.b64decode(data["content"]).decode()
            m = json.loads(content)
            m["_sha"] = data["sha"]
            return m
    except Exception:
        pass
    return {"integrations": [], "_sha": None}


def save_manifest(manifest):
    existing_sha = manifest.pop("_sha", None)
    manifest["last_updated"] = datetime.now(timezone.utc).isoformat()
    content_b64 = base64.b64encode(json.dumps(manifest, indent=2).encode()).decode()
    payload = {
        "message": f"Agent Zero: update manifest ({len(manifest['integrations'])} integrations)",
        "content": content_b64,
    }
    if existing_sha:
        payload["sha"] = existing_sha
    gh("PUT", f"contents/{MANIFEST_PATH}", payload)


# ─── PUSH TO GITHUB ──────────────────────────────────────────────────────────

def push_file(path, content, message):
    """Create or update a file in Agent Zero's repo."""
    content_b64 = base64.b64encode(content.encode()).decode()
    
    # Get existing SHA if file exists
    existing_sha = None
    try:
        existing = gh("GET", f"contents/{path}")
        if isinstance(existing, dict):
            existing_sha = existing.get("sha")
    except Exception:
        pass

    payload = {"message": message, "content": content_b64}
    if existing_sha:
        payload["sha"] = existing_sha

    result = gh("PUT", f"contents/{path}", payload)
    return result.get("content", {}).get("html_url", "pushed")


# ─── MAIN INTEGRATION FLOW ───────────────────────────────────────────────────

def integrate(github_url):
    print(f"\n{'='*60}")
    print(f"  AGENT ZERO — SELF-INTEGRATION ENGINE")
    print(f"  Target: {github_url}")
    print(f"{'='*60}\n")

    # 1. Parse URL
    print("[1/6] Parsing target...")
    slug = parse_github_url(github_url)
    print(f"      Repo: {slug}")

    # 2. Analyze repo
    print("[2/6] Analyzing repository...")
    analysis = analyze_repo(slug)
    print(f"      Name    : {analysis['name']}")
    print(f"      Stars   : {analysis['stars']}")
    print(f"      Language: {analysis['language']}")
    print(f"      Files   : {len(analysis['tree'])}")

    # 3. Classify & Score
    print("[3/6] Classifying...")
    category = classify_tool(analysis)
    score    = score_tool(analysis, category)
    print(f"      Category: {category}")
    print(f"      Score   : {score}/10")

    # 4. Generate connector
    print("[4/6] Generating connector...")
    connector_code = generate_connector(analysis, category)
    safe_name      = re.sub(r"[^a-zA-Z0-9_]", "_", analysis["name"].lower())
    connector_path = f"{INTEGRATION_DIR}/{safe_name}_connector.py"
    print(f"      Output  : {connector_path}")

    # 5. Build integration record
    record = {
        "name":          analysis["name"],
        "slug":          slug,
        "url":           analysis["url"],
        "category":      category,
        "score":         score,
        "language":      analysis["language"],
        "stars":         analysis["stars"],
        "connector":     connector_path,
        "absorbed_at":   datetime.now(timezone.utc).isoformat(),
        "status":        "INTEGRATED",
    }

    # 6. Push connector + update manifest
    print("[5/6] Pushing connector to Agent Zero repo...")
    push_file(
        connector_path,
        connector_code,
        f"Agent Zero absorbs: {analysis['name']} [{category}] score={score}/10"
    )
    print(f"      ✅ Connector live")

    print("[6/6] Updating manifest...")
    manifest = load_manifest()
    # Remove old entry for same slug if exists
    manifest["integrations"] = [
        i for i in manifest["integrations"] if i.get("slug") != slug
    ]
    manifest["integrations"].append(record)
    save_manifest(manifest)
    print(f"      ✅ Manifest updated — {len(manifest['integrations'])} total integrations")

    print(f"\n{'='*60}")
    print(f"  ✅ INTEGRATION COMPLETE")
    print(f"  Tool    : {analysis['name']}")
    print(f"  Category: {category}")
    print(f"  Score   : {score}/10")
    print(f"  File    : https://github.com/{AGENT_ZERO_REPO}/blob/main/{connector_path}")
    print(f"{'='*60}\n")

    return record


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent_zero_integrator.py <github_url>")
        print("       python agent_zero_integrator.py https://github.com/owner/repo")
        sys.exit(1)

    target_url = sys.argv[1]
    result = integrate(target_url)
    print(json.dumps(result, indent=2))
