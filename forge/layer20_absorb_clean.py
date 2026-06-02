import json, re, base64, urllib.request
from datetime import datetime

PANTHEON_TAGS = [
    "crypto","monero","xmr","privacy","anonymity","stealth",
    "scraping","automation","ai","llm","memory","agent",
    "network","proxy","tunnel","security","audit",
    "container","deploy","stream","media","content",
    "database","storage","search","finance","trading"
]
ALREADY_ABSORBED = [
    "xmrig","ollama","supermemory","scrapling","camoufox",
    "telegram-drive","vane","lamda","playwright"
]

def score_tool(name, url, category):
    score = 0
    text = (name + url + category).lower()
    for tag in PANTHEON_TAGS:
        if tag in text:
            score += 2
    for absorbed in ALREADY_ABSORBED:
        if absorbed in text:
            score += 5
    return min(score, 10)

def extract_tools(content):
    tools = []
    current_category = "Unknown"
    lines = content.split('\n')
    for i, line in enumerate(lines):
        h3 = re.search(r'<h3[^>]*>\s*([^<\n]+)', line)
        if h3:
            current_category = h3.group(1).strip()
        href = re.search(r'href="(https?://[^"]+)"', line)
        if href and i+1 < len(lines):
            name_m = re.search(r'^\s{16,}([^\n<]{3,})', lines[i+1])
            if name_m:
                url = href.group(1)
                name = name_m.group(1).strip()
                if 'Assets' not in url and name and len(name) < 60:
                    score = score_tool(name, url, current_category)
                    tools.append({
                        "name": name, "url": url,
                        "category": current_category,
                        "score": score,
                        "status": "ABSORB" if score >= 4 else "EVALUATE" if score >= 2 else "SKIP"
                    })
    return tools

TOKEN = "YOUR_GITHUB_TOKEN"
req = urllib.request.Request(
    "https://api.github.com/repos/kevinleestites2-dev/Open-Source-Everything/contents/README.md",
    headers={"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
)
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())
content = base64.b64decode(data['content']).decode()

tools = extract_tools(content)
absorb = sorted([t for t in tools if t['status']=='ABSORB'], key=lambda x: -x['score'])
evaluate = [t for t in tools if t['status']=='EVALUATE']

log = {
    "generated": datetime.utcnow().isoformat(),
    "source": "kevinleestites2-dev/Open-Source-Everything",
    "total": len(tools),
    "absorb_count": len(absorb),
    "evaluate_count": len(evaluate),
    "skip_count": len([t for t in tools if t['status']=='SKIP']),
    "absorb_queue": absorb,
    "evaluate_queue": evaluate[:15]
}
with open('absorption_log.json','w') as f:
    json.dump(log, f, indent=2)
print("DONE", len(tools), "tools parsed")
