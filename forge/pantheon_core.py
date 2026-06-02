import json, os
from datetime import datetime

class CerebralBridge:
    def __init__(self):
        self.state_file = "PANTHEON_STATE.json"
        self.patch()

    def patch(self):
        if not os.path.exists(self.state_file):
            state = {"version": "1.1.0", "primes": {}, "signals": []}
        else:
            with open(self.state_file, 'r') as f: state = json.load(f)
        if "signals" not in state: state["signals"] = []
        if "primes" not in state: state["primes"] = {}
        with open(self.state_file, 'w') as f: json.dump(state, f, indent=4)

    def push(self, origin, data):
        with open(self.state_file, 'r') as f: state = json.load(f)
        state["signals"].append({"time": datetime.now().isoformat(), "from": origin, "data": data})
        with open(self.state_file, 'w') as f: json.dump(state, f, indent=4)
        print(f"[BRIDGE] SIGNAL INJECTED: {origin}")

if __name__ == "__main__":
    b = CerebralBridge()
    b.push("Aeon", {"type": "REAL_ESTATE_HIT", "loc": "Fort Myers"})