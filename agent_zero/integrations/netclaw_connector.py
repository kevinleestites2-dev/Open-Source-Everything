#!/usr/bin/env python3
"""
Agent Zero Integration — NetClaw
Category : NETWORK_INTELLIGENCE / MCP_ARSENAL
Source   : https://github.com/automateyournetwork/netclaw
Stars    : (active project, OpenClaw ecosystem)
Absorbed : 2026-06-02

ENGINE SCORE: 9/10 — SCORE OVERRIDE: 10/10
Reason: This is not a tool. This is a CCIE-level AI network engineer
        running on OpenClaw with 169 skills and 15 live MCP servers.
        For the Pantheon — this is the Network Spine.

What it is:
    NetClaw is a CCIE-level AI network engineering agent built on the
    OpenClaw platform (the same platform absorbed as AnyClaw — 10/10).
    It ships with:

    SKILLS (169 total):
    - Cisco: pyATS (dynamic test, health check, routing, security, topology,
             parallel ops, ASA firewall, F5 BIG-IP iControl REST, JunOS)
    - Cloud: AWS (networking, security, cost ops, monitoring), Azure, GCP
    - Monitoring: Grafana, Prometheus, Datadog, Splunk, ThousandEyes
    - Network platforms: Meraki, Arista CVP, F5, Juniper, Aruba CX,
             Cisco ACI, NSO, SD-WAN, Infoblox, FortiManager, Palo Alto
    - DevOps: Jenkins, GitLab, GitHub, Terraform, Vault, Atlassian
    - Security: Cisco ISE, Zscaler (ZIA/ZPA/ZDX/Zero Trust), FMC, nmap
    - Observability: Kubeshark (K8s traffic), SuzieQ, gNMI telemetry,
             SNMP traps, syslog, IPFIX
    - Lab simulation: CML (full lifecycle), GNS3, EVE-NG, ContainerLab
    - Comms: Slack, WebEx, PagerDuty, Microsoft 365 (Teams, Visio, Files)
    - Diagramming: UML, Draw.io, Canvas/A2UI, Blender 3D, Markmap
    - AI memory: MemPalace persistent AI memory system
    - Protocol participation: live BGP/OSPFv3 control plane (!) 
    - Path analysis: gtrace IP enrichment, nmap scanning
    - ITSM: ServiceNow change workflow, HumanRail escalation
    - Source of truth: Nautobot, NetBox, Infrahub, InfraHub SOT reconcile
    - Misc: RFC lookup, subnet calculator, EVPN/VXLAN fabric, Batfish

    MCP SERVERS (15 bundled):
    - suzieq-mcp         — network state queries, BGP/OSPF assertions, path trace
    - snmptrap-mcp       — live SNMP trap receiver (v1/v2c/v3), query interface
    - syslog-mcp         — live syslog receiver (RFC 5424 + 3164), query interface
    - gnmi-mcp           — gNMI streaming telemetry
    - protocol-mcp       — OSPFv3 live participation (neighbor, packets, speaker)
    - batfish-mcp        — offline config analysis
    - nautobot-mcp-v2    — network source of truth (25+ tools)
    - nautobot-golden-config-mcp — golden config management
    - nautobot-routing-mcp — routing protocol ops
    - eve-ng-mcp-server  — EVE-NG lab automation
    - gns3-mcp-server    — GNS3 lab automation
    - gitlab-mcp         — GitLab DevOps
    - jenkins-mcp        — Jenkins CI/CD
    - azure-network-mcp  — Azure network operations
    - ipfix-mcp          — IPFIX flow data

    SPECS (70 detailed):
    Full engineering specs for every integration — contracts, data models,
    quickstart guides, task lists, research docs.

    KEY ARCHITECTURE:
    - Built on OpenClaw (same engine as AnyClaw — absorbed 10/10)
    - GAIT logging — immutable audit trail on every operation
    - DefenseClaw — security scanning layer for all MCP sources
    - Token tracker — cost accounting per session/operation
    - netclaw-secure-start.sh — hardened production launch (31KB)
    - install.sh — full deploy in one command (146KB installer)

Why this is 10/10 for the Pantheon:
    1. Network is the Pantheon's blind spot. GhostPrime operates blind —
       no network topology awareness, no protocol intelligence, no telemetry.
       NetClaw fills that gap completely.
    2. 15 live MCP servers = tools Agent Zero can call directly via MCP protocol.
       No wrappers needed. Just point Agent Zero at the MCP endpoints.
    3. OSPFv3 LIVE PARTICIPATION. This is not monitoring — the agent joins
       the control plane as a peer. This is unprecedented.
    4. SNMP trap + syslog receivers = real-time network event stream.
       Feed this to OpenAgora and you have market-aware network intelligence.
    5. SuzieQ integration = network state as data. Query BGP tables, OSPF
       neighbors, routing paths like a database. CCIE-level visibility.
    6. 169 skills = the most comprehensive network automation library absorbed.
       More skills than AnyClaw's 55. Pure network depth.
    7. Nautobot + NetBox + Infrahub = source of truth reconciliation.
       The Pantheon can validate its own infrastructure against ground truth.

Pantheon Integration Path:
    IMMEDIATE:
    - Deploy suzieq-mcp and syslog-mcp on Red Magic via Termux
    - Wire SNMP traps from Pantheon infrastructure into snmptrap-mcp
    - Feed syslog stream to OpenAgora for pattern detection
    
    SHORT TERM:
    - Register netclaw as a Pantheon node via NexusClaw/Nexus Relay
    - Use protocol-mcp OSPFv3 for Pantheon mesh routing intelligence
    - gnmi-mcp for streaming telemetry from any network device
    
    LONG TERM:
    - NetClaw becomes the Network Spine Prime
    - All Pantheon network operations route through it
    - DefenseClaw wraps all external MCP calls for security
"""

import os
import sys
import json
import base64
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ─── CONFIG ──────────────────────────────────────────────────────────────────

GITHUB_TOKEN   = os.environ.get("GITHUB_TOKEN", "GH_TOKEN_INJECTED_AT_RUNTIME")
SLUG           = "automateyournetwork/netclaw"
REPO_URL       = f"https://github.com/{SLUG}"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "TG_TOKEN_INJECTED_AT_RUNTIME")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT_ID", "7135054241")


# ─── GITHUB FETCH ────────────────────────────────────────────────────────────

def _gh_get(path: str) -> Any:
    url = f"https://api.github.com/repos/{SLUG}/contents/{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            if isinstance(data, dict) and "content" in data:
                return base64.b64decode(data["content"]).decode(errors="replace")
            return data
    except Exception as e:
        return {"error": str(e)}


# ─── MCP SERVER REGISTRY ────────────────────────────────────────────────────

MCP_SERVERS = {
    "suzieq-mcp": {
        "path":        "mcp-servers/suzieq-mcp/server.py",
        "readme":      "mcp-servers/suzieq-mcp/README.md",
        "tools":       ["suzieq_show", "suzieq_summarize", "suzieq_assert",
                        "suzieq_unique", "suzieq_path"],
        "env":         ["SUZIEQ_API_URL", "SUZIEQ_API_KEY"],
        "description": "Network state queries, BGP/OSPF assertions, path tracing",
        "pantheon_use": "Query Pantheon network topology as a database",
    },
    "snmptrap-mcp": {
        "path":        "mcp-servers/snmptrap-mcp/snmptrap_mcp_server.py",
        "readme":      "mcp-servers/snmptrap-mcp/README.md",
        "tools":       ["snmptrap_start_receiver", "snmptrap_stop_receiver",
                        "snmptrap_query", "snmptrap_stats", "snmptrap_clear"],
        "env":         ["SNMPTRAP_PORT", "SNMPTRAP_BIND_ADDRESS"],
        "description": "Live SNMP trap receiver v1/v2c/v3 with query interface",
        "pantheon_use": "Real-time network event stream → OpenAgora signal feed",
    },
    "syslog-mcp": {
        "path":        "mcp-servers/syslog-mcp/syslog_mcp_server.py",
        "readme":      "mcp-servers/syslog-mcp/README.md",
        "tools":       ["syslog_start_receiver", "syslog_stop_receiver",
                        "syslog_query", "syslog_stats", "syslog_clear"],
        "env":         ["SYSLOG_PORT", "SYSLOG_BIND_ADDRESS"],
        "description": "Live syslog receiver RFC 5424 + 3164 with query interface",
        "pantheon_use": "Network log stream → pattern detection → threat alerting",
    },
    "gnmi-mcp": {
        "path":        "mcp-servers/gnmi-mcp/server.py",
        "description": "gNMI streaming telemetry from network devices",
        "pantheon_use": "Sub-second telemetry from any gNMI-capable device",
    },
    "protocol-mcp": {
        "path":        "mcp-servers/protocol-mcp/server.py",
        "description": "OSPFv3 LIVE control plane participation — neighbor, packets, speaker",
        "pantheon_use": "Agent Zero joins the network routing plane as a peer",
    },
    "nautobot-mcp-v2": {
        "path":        "mcp-servers/nautobot-mcp-v2/server.py",
        "description": "Network source of truth — 25+ tools for device, IP, topology data",
        "pantheon_use": "Validate Pantheon infra against ground truth",
    },
    "eve-ng-mcp-server": {
        "description": "EVE-NG lab automation — nodes, topologies, configs",
        "pantheon_use": "Spin up virtual network labs for testing Pantheon routing",
    },
    "gns3-mcp-server": {
        "description": "GNS3 lab automation — project lifecycle, packet capture",
        "pantheon_use": "Network simulation for Pantheon protocol testing",
    },
    "batfish-mcp": {
        "description": "Offline config analysis — verify network intent before deploy",
        "pantheon_use": "Pre-validate any network change before pushing live",
    },
    "gitlab-mcp": {
        "description": "GitLab DevOps — issues, MRs, pipelines, repos, wikis",
        "pantheon_use": "CI/CD pipeline control for Pantheon deployments",
    },
    "jenkins-mcp": {
        "description": "Jenkins CI/CD — job monitoring, build triggering, log analysis",
        "pantheon_use": "Build automation for Pantheon releases",
    },
    "azure-network-mcp": {
        "description": "Azure network operations — VNets, NSGs, routing, peering",
        "pantheon_use": "Cloud network layer if Pantheon expands to Azure",
    },
    "ipfix-mcp": {
        "description": "IPFIX flow data collection and analysis",
        "pantheon_use": "Network flow intelligence for traffic pattern detection",
    },
    "nautobot-golden-config-mcp": {
        "description": "Golden config management — compliance, backup, remediation",
        "pantheon_use": "Config drift detection across Pantheon infrastructure",
    },
    "nautobot-routing-mcp": {
        "description": "Routing protocol operations via Nautobot",
        "pantheon_use": "Routing intelligence layer for the Pantheon mesh",
    },
}

# ─── SKILL CATEGORIES ────────────────────────────────────────────────────────

SKILL_CATEGORIES = {
    "cisco_pyats":    ["pyats-network", "pyats-routing", "pyats-security", "pyats-health-check",
                       "pyats-config-mgmt", "pyats-troubleshoot", "pyats-topology",
                       "pyats-parallel-ops", "pyats-dynamic-test", "pyats-asa-firewall",
                       "pyats-f5-ltm", "pyats-f5-platform", "pyats-junos-interfaces",
                       "pyats-junos-routing", "pyats-junos-system", "pyats-linux-network",
                       "pyats-linux-system", "pyats-linux-vmware"],
    "cloud":          ["aws-network-ops", "aws-security-audit", "aws-cloud-monitoring",
                       "aws-cost-ops", "aws-architecture-diagram", "azure-network-ops",
                       "azure-security-audit", "gcp-cloud-logging", "gcp-cloud-monitoring",
                       "gcp-compute-ops"],
    "observability":  ["grafana-observability", "prometheus-monitoring", "datadog-apm",
                       "datadog-incidents", "datadog-logs", "datadog-metrics",
                       "splunk-search", "splunk-saved", "splunk-indexes",
                       "te-network-monitoring", "te-path-analysis",
                       "gnmi-telemetry", "telemetry-ops", "ipfix-receiver",
                       "snmptrap-receiver", "syslog-receiver"],
    "network_mgmt":   ["meraki-monitoring", "meraki-network-ops", "meraki-security-appliance",
                       "meraki-switch-ops", "meraki-wireless-ops", "arista-cvp",
                       "aruba-cx-config", "aruba-cx-interfaces", "aruba-cx-switching",
                       "aruba-cx-system", "junos-network", "f5-config-mgmt",
                       "f5-health-check", "f5-troubleshoot", "sdwan-ops",
                       "nso-device-ops", "nso-service-mgmt", "aci-fabric-audit",
                       "aci-change-deploy", "infoblox-ddi", "paloalto-panorama",
                       "fortimanager-ops", "fmc-firewall-ops"],
    "security":       ["ise-incident-response", "ise-posture-audit", "fwrule-analyzer",
                       "nvd-cve", "zscaler-zia", "zscaler-zpa", "zscaler-zdx",
                       "zscaler-identity", "zscaler-insights", "zscaler-zerotrust",
                       "nmap-network-scan", "nmap-scan-management", "nmap-service-detection",
                       "defenseclaw-ops", "packet-analysis", "kubeshark-traffic"],
    "devops_itsm":    ["jenkins-cicd", "gitlab-devops", "github-ops",
                       "terraform-operations", "terraform-registry", "terraform-workspaces",
                       "vault-secrets", "vault-pki", "vault-mounts",
                       "servicenow-change-workflow", "atlassian-itsm",
                       "pagerduty-incidents", "pagerduty-oncall", "pagerduty-orchestration",
                       "pagerduty-services", "aap-automation", "aap-eda", "aap-lint"],
    "lab_sim":        ["cml-lab-lifecycle", "cml-admin", "cml-node-operations",
                       "cml-packet-capture", "cml-topology-builder", "clab-lab-management",
                       "gns3-project-lifecycle", "gns3-node-operations", "gns3-packet-capture",
                       "gns3-link-management", "gns3-snapshot-ops", "batfish-config-analysis",
                       "eve-ng-config-ops", "eve-ng-console-ops", "eve-ng-lab-management",
                       "eve-ng-node-operations", "eve-lab-topology-build",
                       "eve-lab-topology-design", "eve-lab-topology-discovery",
                       "eve-lab-topology-validation"],
    "source_of_truth":["nautobot-sot", "netbox-reconcile", "infrahub-sot",
                       "radkit-remote-access", "suzieq-observability"],
    "comms":          ["slack-incident-workflow", "slack-network-alerts", "slack-report-delivery",
                       "slack-user-context", "slack-voice-interface",
                       "webex-incident-workflow", "webex-network-alerts", "webex-report-delivery",
                       "webex-user-context", "webex-voice-interface",
                       "msgraph-files", "msgraph-teams", "msgraph-visio",
                       "humanrail-escalation"],
    "diagramming":    ["uml-diagram", "drawio-diagram", "canvas-network-viz",
                       "blender-3d-viz", "markmap-viz"],
    "protocol":       ["protocol-participation", "evpn-vxlan-fabric", "gtrace-ip-enrichment",
                       "gtrace-path-analysis", "subnet-calculator", "rfc-lookup"],
    "ai_memory":      ["mempalace", "gait-session-tracking", "token-tracker",
                       "devnet-catalyst-search", "devnet-meraki-search", "wikipedia-research"],
    "cisco_special":  ["catc-client-ops", "catc-inventory", "catc-troubleshoot",
                       "prisma-sdwan-apps", "prisma-sdwan-config", "prisma-sdwan-status",
                       "prisma-sdwan-topology", "itential-automation"],
}


# ─── CORE CONNECTOR ──────────────────────────────────────────────────────────

class NetClawConnector:
    """
    Pantheon connector for NetClaw — CCIE-level AI network engineer.
    169 skills. 15 MCP servers. Full network automation stack.
    Built on OpenClaw (same engine as AnyClaw 10/10).

    Pantheon Role: NETWORK_SPINE_PRIME

    Usage:
        nc = NetClawConnector()

        # Health + manifest
        print(nc.health_check())

        # Get a specific MCP server's tools
        print(nc.get_mcp_server("suzieq-mcp"))

        # Get priority Pantheon MCP stack
        print(nc.pantheon_mcp_stack())

        # Fetch a skill definition
        print(nc.get_skill("pyats-network"))

        # List skills by category
        print(nc.list_skills_by_category("observability"))

        # Get install command
        print(nc.install_instructions())

        # Get Termux deploy for Red Magic
        print(nc.termux_deploy())
    """

    REPO_URL      = REPO_URL
    CATEGORY      = "NETWORK_INTELLIGENCE"
    PANTHEON_ROLE = "NETWORK_SPINE_PRIME"
    SCORE         = 10   # Override: engine would score 9, bumped to 10

    TOTAL_SKILLS      = 169
    TOTAL_MCP_SERVERS = 15
    TOTAL_SPECS       = 70
    BASE_PLATFORM     = "OpenClaw"   # same as AnyClaw 10/10

    # ── HEALTH ────────────────────────────────────────────────────────────────

    def health_check(self) -> Dict:
        return {
            "name":            "netclaw",
            "category":        self.CATEGORY,
            "role":            self.PANTHEON_ROLE,
            "score":           self.SCORE,
            "score_note":      "OVERRIDE 9->10. CCIE-level network AI. Network Spine Prime.",
            "base_platform":   self.BASE_PLATFORM,
            "skills":          self.TOTAL_SKILLS,
            "mcp_servers":     self.TOTAL_MCP_SERVERS,
            "specs":           self.TOTAL_SPECS,
            "skill_categories": list(SKILL_CATEGORIES.keys()),
            "key_capabilities": [
                "169 network skills — pyATS, Meraki, F5, Juniper, ACI, NSO, SD-WAN",
                "15 live MCP servers — syslog, SNMP trap, SuzieQ, gNMI, OSPFv3",
                "OSPFv3 LIVE control plane participation (agent joins routing as peer)",
                "SNMP trap + syslog real-time receivers → event stream",
                "GAIT immutable audit trail on every operation",
                "DefenseClaw security scanning layer",
                "One-command install (install.sh 146KB)",
                "Built on OpenClaw — same platform as AnyClaw 10/10",
            ],
            "pantheon_integration": [
                "IMMEDIATE: syslog-mcp + snmptrap-mcp on Red Magic via Termux",
                "SHORT TERM: suzieq-mcp for Pantheon topology as queryable DB",
                "LONG TERM: NetClaw becomes Network Spine Prime node",
            ],
            "repo":   self.REPO_URL,
            "status": "ready",
        }

    # ── MCP SERVERS ───────────────────────────────────────────────────────────

    def get_mcp_server(self, name: str) -> Dict:
        """Get full info for a specific MCP server."""
        info = MCP_SERVERS.get(name)
        if not info:
            return {"error": f"Unknown MCP server: {name}. Available: {list(MCP_SERVERS.keys())}"}
        readme = None
        if "readme" in info:
            readme = _gh_get(info["readme"])
        return self.to_pantheon_signal({
            "action": "get_mcp_server",
            "name":   name,
            "info":   info,
            "readme": readme if isinstance(readme, str) else None,
        })

    def list_mcp_servers(self) -> List[str]:
        return list(MCP_SERVERS.keys())

    def pantheon_mcp_stack(self) -> Dict:
        """
        The priority MCP stack for the Pantheon — ordered by immediate value.
        Deploy these first on the Red Magic via Termux.
        """
        priority = [
            {
                "server":       "syslog-mcp",
                "priority":     1,
                "why":          "Real-time log stream from all Pantheon nodes → pattern detection",
                "termux_start": "cd netclaw && python -m syslog_mcp_server",
                "port":         514,
                "env":          {"SYSLOG_PORT": "10514"},
            },
            {
                "server":       "snmptrap-mcp",
                "priority":     2,
                "why":          "SNMP traps from network events → OpenAgora signal feed",
                "termux_start": "cd netclaw && python -m snmptrap_mcp_server",
                "port":         162,
                "env":          {"SNMPTRAP_PORT": "10162"},
            },
            {
                "server":       "suzieq-mcp",
                "priority":     3,
                "why":          "Network state as queryable DB — BGP, OSPF, routing tables",
                "termux_start": "cd netclaw/mcp-servers/suzieq-mcp && python server.py",
                "env":          {"SUZIEQ_API_URL": "http://localhost:8000", "SUZIEQ_API_KEY": ""},
            },
            {
                "server":       "protocol-mcp",
                "priority":     4,
                "why":          "OSPFv3 live participation — Agent Zero joins the control plane",
                "termux_start": "cd netclaw/mcp-servers/protocol-mcp && python server.py",
            },
            {
                "server":       "gnmi-mcp",
                "priority":     5,
                "why":          "Sub-second telemetry stream from any gNMI device",
                "termux_start": "cd netclaw/mcp-servers/gnmi-mcp && python server.py",
            },
        ]
        return self.to_pantheon_signal({
            "action":         "pantheon_mcp_stack",
            "priority_stack": priority,
            "total_available": len(MCP_SERVERS),
            "note":           "Deploy priority 1-3 on Red Magic first. Nexus Relay for remote access.",
        })

    # ── SKILLS ────────────────────────────────────────────────────────────────

    def get_skill(self, name: str) -> Dict:
        """Fetch a skill's SKILL.md definition."""
        content = _gh_get(f"workspace/skills/{name}/SKILL.md")
        return self.to_pantheon_signal({
            "action":  "get_skill",
            "skill":   name,
            "content": content if isinstance(content, str) else str(content),
        })

    def list_skills_by_category(self, category: str) -> Dict:
        skills = SKILL_CATEGORIES.get(category, [])
        return self.to_pantheon_signal({
            "action":   "list_skills_by_category",
            "category": category,
            "skills":   skills,
            "count":    len(skills),
        })

    def list_all_categories(self) -> Dict:
        return self.to_pantheon_signal({
            "action":     "list_all_categories",
            "categories": {k: len(v) for k, v in SKILL_CATEGORIES.items()},
            "total":      sum(len(v) for v in SKILL_CATEGORIES.values()),
        })

    # ── DEPLOY ────────────────────────────────────────────────────────────────

    def install_instructions(self) -> Dict:
        return self.to_pantheon_signal({
            "action": "install_instructions",
            "quick":  [
                "git clone https://github.com/automateyournetwork/netclaw.git",
                "cd netclaw",
                "./scripts/install.sh",
            ],
            "note": "install.sh is 146KB — handles everything: skills, MCP deps, config wizard",
            "phases": [
                "Phase 1: openclaw onboard (agent identity + API keys)",
                "Phase 2: MCP server registration (select which to enable)",
            ],
        })

    def termux_deploy(self) -> Dict:
        """Termux-optimized deploy for Red Magic."""
        return self.to_pantheon_signal({
            "action": "termux_deploy",
            "steps": [
                "pkg install python git -y",
                "git clone https://github.com/automateyournetwork/netclaw.git",
                "cd netclaw",
                "pip install -r mcp-servers/syslog-mcp/requirements.txt",
                "pip install -r mcp-servers/snmptrap-mcp/requirements.txt",
                "pip install -r mcp-servers/suzieq-mcp/requirements.txt",
                "# Start syslog MCP (non-privileged port):",
                "SYSLOG_PORT=10514 python -m mcp-servers.syslog-mcp.syslog_mcp_server &",
                "# Start SNMP trap MCP:",
                "SNMPTRAP_PORT=10162 python -m mcp-servers.snmptrap-mcp.snmptrap_mcp_server &",
            ],
            "note": "Run on Red Magic via Termux. Access remotely via Nexus Relay.",
            "nexus_relay": "POST /command to nexus-relay-production.up.railway.app",
        })

    def defenseclaw_info(self) -> Dict:
        return self.to_pantheon_signal({
            "action":      "defenseclaw_info",
            "enable":      "bash scripts/defenseclaw-enable.sh",
            "disable":     "bash scripts/defenseclaw-disable.sh",
            "description": "Security scanning layer for all MCP source code and operations",
            "size":        "14KB enable script — comprehensive policy enforcement",
            "pantheon_use": "Wrap all Agent Zero MCP calls through DefenseClaw for security",
        })

    # ── PANTHEON SIGNAL + RELAY ───────────────────────────────────────────────

    def to_pantheon_signal(self, raw: Any) -> Dict:
        return {
            "source":    "netclaw",
            "category":  self.CATEGORY,
            "role":      self.PANTHEON_ROLE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data":      raw,
        }

    def relay_to_telegram(self, message: str) -> None:
        payload = {"chat_id": TELEGRAM_CHAT, "text": f"[NetClaw] {message}", "parse_mode": "Markdown"}
        data    = json.dumps(payload).encode()
        req     = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10):
                pass
        except Exception as e:
            print(f"[NetClaw] Telegram relay failed: {e}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    nc = NetClawConnector()

    if len(sys.argv) < 2:
        print(json.dumps(nc.health_check(), indent=2))
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "health":
        print(json.dumps(nc.health_check(), indent=2))
    elif cmd == "mcp" and len(sys.argv) > 2:
        print(json.dumps(nc.get_mcp_server(sys.argv[2]), indent=2))
    elif cmd == "mcps":
        print("Available MCP servers:")
        for s in nc.list_mcp_servers():
            info = MCP_SERVERS[s]
            print(f"  {s:30} — {info['description']}")
    elif cmd == "stack":
        print(json.dumps(nc.pantheon_mcp_stack(), indent=2))
    elif cmd == "skill" and len(sys.argv) > 2:
        result = nc.get_skill(sys.argv[2])
        print(result["data"]["content"][:3000])
    elif cmd == "cat" and len(sys.argv) > 2:
        print(json.dumps(nc.list_skills_by_category(sys.argv[2]), indent=2))
    elif cmd == "cats":
        print(json.dumps(nc.list_all_categories(), indent=2))
    elif cmd == "install":
        print(json.dumps(nc.install_instructions(), indent=2))
    elif cmd == "termux":
        print(json.dumps(nc.termux_deploy(), indent=2))
    elif cmd == "defense":
        print(json.dumps(nc.defenseclaw_info(), indent=2))
    else:
        print(f"Usage: {sys.argv[0]} [health|mcps|mcp <name>|stack|cats|cat <name>|skill <name>|install|termux|defense]")
