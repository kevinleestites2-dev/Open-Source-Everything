#!/usr/bin/env python3
import urllib.request, json, base64

token = 'GH_TOKEN_INJECTED_AT_RUNTIME'
repo  = 'kevinleestites2-dev/CerberusPrime'
headers = {'Authorization': f'token {token}', 'Content-Type': 'application/json', 'User-Agent': 'ZapiaPrime'}

def get_sha(path):
    url = f'https://api.github.com/repos/{repo}/contents/{path}'
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r).get('sha')
    except:
        return None

def push_file(path, message, content):
    sha = get_sha(path)
    url = f'https://api.github.com/repos/{repo}/contents/{path}'
    payload = {"message": message, "content": base64.b64encode(content.encode()).decode()}
    if sha:
        payload["sha"] = sha
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method='PUT', headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            result = json.load(r)
            return result['commit']['sha'][:12]
    except urllib.error.HTTPError as e:
        print(f"  ERROR {e.code}: {e.read().decode()[:200]}")
        return None

layer11 = open('layer11_doctrine.py').read()
layer12 = open('layer12_prime_cycle.py').read()
layer13 = open('layer13_physical_form.py').read()

print("Pushing Layer 11...")
c = push_file('agent_zero/layer11_doctrine.py', 'feat(L11): Doctrine Engine — four-question validation firewall', layer11)
print(f"  layer11_doctrine.py -> {c}")

print("Pushing Layer 12...")
c = push_file('agent_zero/layer12_prime_cycle.py', 'feat(L12): Prime Cycle Engine — Agent Zero fleet orchestration', layer12)
print(f"  layer12_prime_cycle.py -> {c}")

print("Pushing Layer 13...")
c = push_file('agent_zero/layer13_physical_form.py', 'feat(L13): Psi0 Physical Form — Android control via Nexus Relay', layer13)
print(f"  layer13_physical_form.py -> {c}")

print("All layers pushed.")
