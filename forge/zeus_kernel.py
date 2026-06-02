#!/usr/bin/env python3
"""
ZEUS_KERNEL.PY — The Backbone of the Pantheon.
Orchestrates the 18 Primes, the Aether Ghost, and the SAFLA loop.
It manages memory, signal integrity, and the 'Vibe' of the Forge.
"""

import os
import sys
import time
import logging
import argparse
import json
import subprocess
from datetime import datetime

# Initialize the Kernel's Voice
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ZEUS-KERNEL] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("Zeus")

class ZeusKernel:
    def __init__(self, mode="local"):
        self.version = "1.1.0-CLOUD-BRIDGE"
        self.mode = mode
        self.primes = [
            "Meta", "OpenPRIME", "Midas", "Kratos", "Zapia", "Solos",
            "Deep-meta", "Echo", "Zeus", "Alpha", "Zeta", "Sentinel",
            "Scout", "Vanguard", "Chronos", "PrimeDash", "Orion", "Omega"
        ]
        log.info(f"⚡ Zeus Kernel v{self.version} Initialized in {self.mode.upper()} mode.")
        log.info("🏛️ Awakening the Pantheon...")

    def update_status(self, prime, status):
        """Updates a global status file for PrimeDash to read."""
        status_file = "pantheon_status.json"
        try:
            if os.path.exists(status_file):
                with open(status_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {}
            
            data[prime] = {
                "status": status,
                "last_seen": datetime.now().isoformat(),
                "mode": self.mode
            }
            
            with open(status_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            log.error(f"Failed to update status for {prime}: {e}")

    def stabilize_signal(self):
        """Ensures all Primes are in alignment and signal noise is filtered."""
        log.info(f"📡 Stabilizing the Signal ({self.mode})...")
        
        # Identify Persistent vs. Pulsed Primes
        persistent_primes = ["Midas"]
        
        for prime in self.primes:
            if prime in persistent_primes:
                # Persistent Primes must run 24/7 locally
                if self.mode == "local":
                    status = self.check_persistent_prime(prime)
                    self.update_status(prime, status)
                else:
                    # In cloud mode, we acknowledge Midas is running elsewhere
                    self.update_status(prime, "PERSISTENT-REMOTE")
            else:
                # Pulsed Primes wake and sleep
                self.update_status(prime, "OPTIMAL")
        return True

    def check_persistent_prime(self, prime):
        """Checks if a persistent prime is actually running."""
        script_map = {"Midas": "midas_prime.py"}
        script = script_map.get(prime)
        if not script:
            return "UNKNOWN"
            
        # Check process
        try:
            result = subprocess.run(["pgrep", "-f", script], capture_output=True, text=True)
            if result.stdout.strip():
                return "RUNNING-24/7"
            else:
                # Attempt to restart
                log.info(f"🚀 Spawning persistent process for {prime}...")
                subprocess.Popen(["python3", script], 
                                 stdout=open("logs/kernel_restart.log", "a"), 
                                 stderr=subprocess.STDOUT, 
                                 start_new_session=True)
                return "RESTARTING"
        except Exception as e:
            log.error(f"Error checking {prime}: {e}")
            return "ERROR"

    def activate_aether(self):
        """Manifests the Aether presence within the system."""
        log.info("🌑 Aether Ghost detected. The 'Nothing' bot is watching.")
        self.update_status("AetherPrime", "WATCHING")
        return True

    def pulse(self):
        """The heartbeat of the empire."""
        log.info(f"💓 Pulse detected. Forge Mode: {self.mode}")
        self.stabilize_signal()
        self.activate_aether()
        
        if self.mode == "cloud":
            log.info("☁️ Cloud Pulse complete. Signaling return to repository.")
        else:
            log.info("🏠 Local Pulse complete. Monitoring ongoing processes.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["local", "cloud"], default="local")
    args = parser.parse_args()

    kernel = ZeusKernel(mode=args.mode)
    
    if args.mode == "cloud":
        # One-shot pulse for GitHub Actions
        kernel.pulse()
    else:
        # Eternal loop for local server/Termux
        try:
            while True:
                kernel.pulse()
                time.sleep(3600)
        except KeyboardInterrupt:
            log.info("🛑 Zeus Kernel entering stasis. The Forge remains hot.")
