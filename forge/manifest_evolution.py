import requests
import base64
import os

token = os.getenv("GITHUB_TOKEN")
repo = "kevinleestites2-dev/AetherPrime-The-Genesis-Kernel"
path = "aether_prime.py"
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

# 1. Get the current file info to get the SHA
url = f"https://api.github.com/repos/{repo}/contents/{path}"
r = requests.get(url, headers=headers)
if r.status_code == 200:
    sha = r.json()["sha"]
else:
    print(f"Error getting file info: {r.status_code} {r.text}")
    exit(1)

# 2. Read the new content
with open("aether_prime_v2.py", "rb") as f:
    content = base64.b64encode(f.read()).decode()

# 3. Update the file with a UNIQUE commit message to signal the evolution
payload = {
    "message": "🔥 V2.0.0 Evolution: The High Architect Manifestation (Claude-Code Integration)",
    "content": content,
    "sha": sha
}
r = requests.put(url, headers=headers, json=payload)
if r.status_code == 200:
    print("Successfully manifested the V2.0.0 Evolution.")
else:
    print(f"Error updating file: {r.status_code} {r.text}")
