#!/usr/bin/env python3
"""Generate Obsidian vault + live HTML graph for ZBook home lab (run on Mac)."""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VAULT = Path(__file__).resolve().parent

MEDIUM_META = {
    "wifi_2g": {"label": "Wi-Fi 2.4 GHz", "color": "#f9a825", "dashes": [8, 4]},
    "wifi_5g": {"label": "Wi-Fi 5 GHz", "color": "#ffb74d", "dashes": False},
    "wifi": {"label": "Wi-Fi", "color": "#ffcc80", "dashes": [6, 3]},
    "ethernet": {"label": "Gigabit Ethernet", "color": "#64b5f6", "dashes": False},
    "docker_bridge": {"label": "Docker bridge (WSL2)", "color": "#ce93d8", "dashes": [2, 6]},
    "portproxy": {"label": "Windows portproxy", "color": "#4dd0e1", "dashes": [4, 4]},
    "tailscale": {"label": "Tailscale overlay", "color": "#81c784", "dashes": [10, 5]},
    "cloud_api": {"label": "Cloud API (Tuya)", "color": "#90a4ae", "dashes": [3, 3]},
    "cast": {"label": "Google Cast protocol", "color": "#fff176", "dashes": [5, 5]},
    "rtsp": {"label": "RTSP video stream", "color": "#ef5350", "dashes": False},
    "http": {"label": "HTTP / Web UI", "color": "#ba68c8", "dashes": False},
    "logical": {"label": "Logical / documented link", "color": "#78909c", "dashes": [2, 8]},
    "bluetooth": {"label": "Bluetooth (personal)", "color": "#4fc3f7", "dashes": [3, 5]},
    "ha_mobile": {"label": "Home Assistant app", "color": "#26a69a", "dashes": [6, 2]},
}

# Always rendered (homelab core) even when not in current ARP/router scan.
ALWAYS_ON_IDS = frozenset(
    {
        "router-gateway",
        "zbook-wifi",
        "wsl-ubuntu",
        "homeassistant",
        "minecraft-server",
        "minecraft-phantom",
        "zbook-webcam",
        "kitchen-speaker",
        "smart-plugs",
    }
)

# Map HA device_tracker entity → one canonical graph node id.
HA_ENTITY_CANONICAL: dict[str, str] = {
    "device_tracker.mashall_spratts_iphone": "marshall-iphone",
    "device_tracker.homebase_macbook": "homebase-macbook",
    "device_tracker.home_panel_droid": "w09n-frame",
}

SCANNER_DEVICE_ALIASES = {
    "mf-mac-905": "mac-primary",
    "tests-macbook-pro": "old-macbook",
    "desktop-d1h9i0p": "zbook-wifi",
}

EXTRA_DEVICES_FILE = VAULT / "extra-devices.json"
HA_TOKEN_FILES = (VAULT / "ha-token.local", VAULT / ".ha-token")
KNOWN_CLIENTS_FILE = VAULT / "known-clients.json"
HELIX_ROUTER_FILE = VAULT / "helix-router.json"
LAN_SUBNET_PREFIX = "10.0.0."

DEVICES: dict[str, dict] = {
    "router-gateway": {
        "name": "Router Gateway",
        "type": "network",
        "role": "Gateway · DHCP · NAT",
        "ips": ["10.0.0.1"],
        "tailscale": [],
        "hardware": "VIDEOTRON router",
        "services": ["DHCP", "DNS", "NAT"],
        "power_profile": "always_on",
    },
    "zbook-wifi": {
        "name": "ZBook Server",
        "type": "server",
        "role": "Home lab host (Windows + WSL2)",
        "ips": ["10.0.0.169"],
        "tailscale": ["100.97.161.68"],
        "hardware": "HP ZBook · DESKTOP-D1H9I0P",
        "services": ["Home Assistant :8123", "Cockpit :9090", "Glances :61208", "SMB ZBookShare :445"],
        "power_profile": "always_on",
        "probe_ports": [8123, 61208, 445],
    },
    "wsl-ubuntu": {
        "name": "WSL Ubuntu",
        "type": "compute",
        "role": "Docker engine on ZBook",
        "runs_on": "zbook-wifi",
        "ips": ["172.27.133.182"],
        "tailscale": [],
        "hardware": "Ubuntu WSL2 · Docker",
        "services": ["Docker", "Home Assistant container", "Glances", "Minecraft Paper+Geyser"],
        "power_profile": "always_on",
        "lan_routable": False,
        "infer_from": ["zbook-wifi", "homeassistant"],
    },
    "homeassistant": {
        "name": "Home Assistant",
        "type": "service",
        "role": "Automation hub · Docker container",
        "runs_on": "wsl-ubuntu",
        "ips": ["10.0.0.169"],
        "tailscale": ["https://desktop-d1h9i0p-1.tailf11422.ts.net"],
        "hardware": "Docker · Trusted Networks auth",
        "services": ["/live-kiosk", "/frame-panel", "Tuya plugs", "Cast", "Robot Intercom"],
        "power_profile": "always_on",
        "probe_http": "http://10.0.0.169:8123/",
    },
    "minecraft-server": {
        "name": "Minecraft Paper",
        "type": "service",
        "role": "Java + Bedrock cross-play · Docker",
        "runs_on": "wsl-ubuntu",
        "ips": ["10.0.0.169"],
        "tailscale": [],
        "hardware": "Docker · 2G RAM · Geyser + Floodgate",
        "services": ["Java :25565", "Geyser backend :19133"],
        "power_profile": "on_demand",
        "probe_ports": [(25565, "tcp")],
    },
    "minecraft-phantom": {
        "name": "Phantom Proxy",
        "type": "service",
        "role": "Xbox LAN discovery beacon · Docker host net",
        "runs_on": "wsl-ubuntu",
        "ips": ["10.0.0.169"],
        "tailscale": [],
        "hardware": "Docker host network on ZBook",
        "services": ["Bedrock LAN UDP :19132"],
        "power_profile": "on_demand",
        "infer_from": ["minecraft-server"],
    },
    "mac-primary": {
        "name": "MacBook Pro (This Mac)",
        "type": "client",
        "role": "Daily driver · mf-mac-905",
        "ips": ["10.0.0.227"],
        "tailscale": ["100.88.199.80"],
        "hardware": "MF-MAC-905 · marshalls",
        "services": ["Obsidian", "Cursor", "Tailscale"],
        "power_profile": "active_use",
    },
    "old-macbook": {
        "name": "Old MacBook Pro",
        "type": "client",
        "role": "Family workstation",
        "ips": ["10.0.0.8"],
        "tailscale": [],
        "hardware": "Tests-MacBook-Pro",
        "services": ["Migration source"],
        "power_profile": "standby_capable",
    },
    "w09n-frame": {
        "name": "W09N Smart Frame",
        "type": "iot",
        "role": "HA kiosk display",
        "ips": ["10.0.0.113"],
        "tailscale": [],
        "hardware": "NexFoto W09N · Android 4.4.2 · WallPanel",
        "services": ["Firefox", "/frame-panel dashboard"],
        "power_profile": "display_always_on",
        "probe_http": "http://10.0.0.169:8123/frame-panel",
    },
    "chromecast": {
        "name": "Chromecast",
        "type": "iot",
        "role": "Cast target",
        "ips": ["10.0.0.14"],
        "tailscale": [],
        "hardware": "Google Cast",
        "services": ["Cast :8009"],
        "power_profile": "standby_capable",
        "probe_ports": [(8009, "tcp")],
    },
    "kitchen-speaker": {
        "name": "Kitchen Speaker",
        "type": "iot",
        "role": "Cast media · Robot Intercom TTS",
        "ips": [],
        "tailscale": [],
        "hardware": "media_player.kitchen_speaker",
        "services": ["Google Cast", "TTS output"],
        "power_profile": "standby_capable",
        "ha_entity": "media_player.kitchen_speaker",
    },
    "smart-plugs": {
        "name": "Tuya Smart Plugs",
        "type": "iot",
        "role": "Power control (cloud + local)",
        "ips": [],
        "tailscale": [],
        "hardware": "Plug 1 Desk · Plug 2 Shed · Plug 3 Command Central",
        "services": ["switch.plug_1/2/3_socket_1"],
        "power_profile": "switchable",
        "ha_entities": [
            "switch.plug_1_socket_1",
            "switch.plug_2_socket_1",
            "switch.plug_3_socket_1",
        ],
    },
    "zbook-webcam": {
        "name": "ZBook Webcam",
        "type": "iot",
        "role": "Basement camera feed · go2rtc in WSL",
        "runs_on": "wsl-ubuntu",
        "ips": ["172.27.128.1"],
        "tailscale": [],
        "hardware": "go2rtc · camera.172_27_128_1",
        "services": ["RTSP", "HA picture-glance"],
        "power_profile": "always_on",
        "ha_entity": "camera.172_27_128_1",
        "lan_routable": False,
        "infer_from": ["homeassistant"],
    },
}

CONNECTIONS: list[dict] = [
    {"from": "router-gateway", "to": "zbook-wifi", "medium": "wifi_5g", "traffic": "routing", "direction": "bidirectional", "note": "ZBook wireless uplink"},
    {"from": "router-gateway", "to": "mac-primary", "medium": "wifi", "traffic": "routing", "direction": "bidirectional", "note": "Daily driver Mac"},
    {"from": "router-gateway", "to": "old-macbook", "medium": "wifi", "traffic": "routing", "direction": "bidirectional", "note": "Family Mac"},
    {"from": "router-gateway", "to": "w09n-frame", "medium": "wifi_2g", "traffic": "routing", "direction": "bidirectional", "note": "Frame on 2.4 GHz SSID"},
    {"from": "router-gateway", "to": "chromecast", "medium": "wifi", "traffic": "routing", "direction": "bidirectional", "note": "Cast discovery"},
    {"from": "router-gateway", "to": "smart-plugs", "medium": "wifi_2g", "traffic": "routing", "direction": "bidirectional", "note": "Tuya Wi-Fi plugs"},
    {"from": "zbook-wifi", "to": "wsl-ubuntu", "medium": "docker_bridge", "traffic": "management", "direction": "bidirectional", "note": "Hyper-V virtual switch"},
    {"from": "zbook-wifi", "to": "homeassistant", "medium": "portproxy", "traffic": "data", "direction": "bidirectional", "note": ":8123 LAN bridge"},
    {"from": "wsl-ubuntu", "to": "homeassistant", "medium": "docker_bridge", "traffic": "data", "direction": "bidirectional", "note": "HA container bind mount"},
    {"from": "wsl-ubuntu", "to": "minecraft-server", "medium": "docker_bridge", "traffic": "data", "direction": "bidirectional", "note": "Paper server container"},
    {"from": "wsl-ubuntu", "to": "minecraft-phantom", "medium": "docker_bridge", "traffic": "data", "direction": "bidirectional", "note": "Host-network phantom"},
    {"from": "minecraft-server", "to": "minecraft-phantom", "medium": "logical", "traffic": "data", "direction": "bidirectional", "note": "Geyser backend :19133"},
    {"from": "mac-primary", "to": "zbook-wifi", "medium": "wifi", "traffic": "management", "direction": "bidirectional", "note": "SSH · SMB · HA UI"},
    {"from": "mac-primary", "to": "homeassistant", "medium": "http", "traffic": "management", "direction": "bidirectional", "note": "Dashboard · Obsidian refresh"},
    {"from": "mac-primary", "to": "zbook-wifi", "medium": "tailscale", "traffic": "routing", "direction": "bidirectional", "note": "Remote access overlay"},
    {"from": "old-macbook", "to": "zbook-wifi", "medium": "wifi", "traffic": "management", "direction": "bidirectional", "note": "LAN file share"},
    {"from": "w09n-frame", "to": "homeassistant", "medium": "http", "traffic": "data", "direction": "downstream", "note": "Loads /frame-panel tiles"},
    {"from": "w09n-frame", "to": "zbook-wifi", "medium": "wifi_2g", "traffic": "data", "direction": "downstream", "note": "HTTP to HA portproxy"},
    {"from": "homeassistant", "to": "kitchen-speaker", "medium": "cast", "traffic": "control", "direction": "downstream", "note": "TTS · media control"},
    {"from": "homeassistant", "to": "smart-plugs", "medium": "cloud_api", "traffic": "control", "direction": "downstream", "note": "Tuya integration"},
    {"from": "homeassistant", "to": "chromecast", "medium": "cast", "traffic": "control", "direction": "downstream", "note": "Cast discovery"},
    {"from": "chromecast", "to": "kitchen-speaker", "medium": "cast", "traffic": "data", "direction": "downstream", "note": "Speaker group / Cast route"},
    {"from": "zbook-webcam", "to": "homeassistant", "medium": "rtsp", "traffic": "upstream", "note": "Camera stream to HA"},
    {"from": "zbook-webcam", "to": "wsl-ubuntu", "medium": "docker_bridge", "traffic": "upstream", "note": "go2rtc in WSL"},
    {"from": "zbook-webcam", "to": "zbook-wifi", "medium": "logical", "traffic": "upstream", "note": "Host camera passthrough"},
]

HA_ENTITIES = {
    "switch.plug_1_socket_1": "Plug 1 · Desk",
    "switch.plug_2_socket_1": "Plug 2 · Shed",
    "switch.plug_3_socket_1": "Plug 3 · Command Central",
    "media_player.kitchen_speaker": "Kitchen Speaker",
    "camera.172_27_128_1": "Basement Webcam",
}


def run(cmd: list[str], timeout: int = 8) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "") + (r.stderr or "")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def ping_probe(ip: str) -> dict:
    out = run(["ping", "-c", "3", "-W", "2000", ip])
    ok = " 0.0% packet loss" in out or "1 packets received" in out or "bytes from" in out
    latencies: list[float] = []
    for m in re.finditer(r"time=([\d.]+)\s*ms", out):
        latencies.append(float(m.group(1)))
    avg = round(sum(latencies) / len(latencies), 1) if latencies else None
    loss_match = re.search(r"([\d.]+)% packet loss", out)
    loss = float(loss_match.group(1)) if loss_match else (0.0 if ok else 100.0)
    return {"online": ok, "latency_ms": avg, "packet_loss_pct": loss, "samples": len(latencies)}


def tcp_probe(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_probe(url: str) -> dict:
    if not shutil.which("curl"):
        return {"online": None, "code": None}
    code = run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "5", url]).strip()
    return {"online": code in ("200", "301", "302", "401"), "code": code}


def resolve_ha_token() -> str | None:
    env = os.environ.get("HOMELAB_HA_TOKEN", "").strip()
    if env:
        return env
    for path in HA_TOKEN_FILES:
        if path.exists():
            token = path.read_text(encoding="utf-8").strip()
            if token and not token.startswith("#"):
                return token
    return None


def ha_fetch_json(base: str, token: str, path: str) -> dict | list | None:
    if not token or not shutil.which("curl"):
        return None
    out = run(
        [
            "curl", "-s", "--max-time", "10",
            "-H", f"Authorization: Bearer {token}",
            f"{base.rstrip('/')}{path}",
        ]
    )
    if not out.strip() or out.strip().startswith("<"):
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def ha_fetch_states(base: str, token: str) -> dict[str, dict]:
    rows = ha_fetch_json(base, token, "/api/states")
    if not isinstance(rows, list):
        return {}
    return {row["entity_id"]: row for row in rows if isinstance(row, dict) and "entity_id" in row}


def safe_name(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "-", name).strip()


def safe_name(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "-", name).strip()


def slug_device_id(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:48] or "device"


def resolve_scanner_device_id(devices: dict[str, dict]) -> str | None:
    host = platform.node().lower()
    if host in SCANNER_DEVICE_ALIASES:
        return SCANNER_DEVICE_ALIASES[host]
    for did, d in devices.items():
        blob = " ".join(
            [
                d.get("name", ""),
                d.get("hardware", ""),
                d.get("role", ""),
                " ".join(d.get("ips", [])),
            ]
        ).lower()
        if host and host in blob:
            return did
    return None


def build_viewer_index(devices: dict[str, dict]) -> list[dict]:
    rows = []
    for did, d in devices.items():
        rows.append(
            {
                "id": did,
                "name": d.get("name", did),
                "short": DEVICE_CAPACITY.get(did, DEFAULT_CAPACITY).get("short") or d.get("name", did),
                "ips": [ip for ip in d.get("ips", []) if re.match(r"^\d+\.\d+\.\d+\.\d+$", ip)],
            }
        )
    return rows


def match_viewer_device(client_ip: str, hostname: str, index: list[dict]) -> dict | None:
    if client_ip in ("127.0.0.1", "::1"):
        alias = SCANNER_DEVICE_ALIASES.get(hostname.lower())
        if alias:
            return next((row for row in index if row["id"] == alias), None)
        for row in index:
            if hostname.lower() in row["name"].lower():
                return row
        return next((row for row in index if row["id"] == "mac-primary"), None)
    for row in index:
        if client_ip in row.get("ips", []):
            return row
    return None


def load_extra_devices(devices: dict[str, dict], connections: list[dict]) -> None:
    if not EXTRA_DEVICES_FILE.exists():
        return
    try:
        extras = json.loads(EXTRA_DEVICES_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    if not isinstance(extras, list):
        return
    for item in extras:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        did = item["id"]
        if did in devices:
            continue
        devices[did] = {
            "name": item.get("name", did),
            "type": item.get("type", "client"),
            "role": item.get("role", "Manual entry"),
            "ips": item.get("ips", []),
            "tailscale": item.get("tailscale", []),
            "hardware": item.get("hardware", "Manual"),
            "services": item.get("services", []),
            "power_profile": item.get("power_profile", "standby_capable"),
            "ha_entity": item.get("ha_entity"),
            "ha_entities": item.get("ha_entities", []),
            "discovered": False,
            "manual": True,
        }
        DEVICE_CAPACITY[did] = {
            **DEFAULT_CAPACITY,
            **(item.get("capacity") or {}),
            "short": item.get("short") or item.get("name", did)[:14],
            "personality": item.get("personality", "edge"),
        }
        uplink = item.get("uplink", "router-gateway")
        medium = item.get("medium", "wifi")
        if uplink in devices or uplink == "router-gateway":
            connections.append(
                {
                    "from": uplink,
                    "to": did,
                    "medium": medium,
                    "traffic": item.get("traffic", "routing"),
                    "direction": "bidirectional",
                    "note": item.get("note", "Manual extra device"),
                }
            )
        parent = item.get("parent")
        if parent and parent in devices:
            connections.append(
                {
                    "from": parent,
                    "to": did,
                    "medium": item.get("parent_medium", "bluetooth"),
                    "traffic": item.get("traffic", "data"),
                    "direction": "bidirectional",
                    "note": item.get("parent_note", "Personal peripheral"),
                }
            )


def _merge_tracker_into_lan_device(devices: dict[str, dict], tracker_name: str, entity_id: str) -> str | None:
    """Attach HA device_tracker to an existing LAN node instead of creating a duplicate."""
    name_l = tracker_name.lower()
    entity_l = entity_id.lower()

    def matches(did: str) -> bool:
        if did == "wife-iphone":
            return any(x in name_l or x in entity_l for x in ("wife", "stephanie", "cleroux", "cléroux"))
        if did == "marshall-iphone":
            return any(x in name_l or x in entity_l for x in ("mashall", "marshall", "spratt"))
        if did == "family-ipad":
            return "ipad" in name_l or ("ipad" in entity_l and "iphone" not in entity_l)
        if did == "homebase-macbook":
            return "homebase" in name_l or "homebase" in entity_l
        if did == "home-panel-droid":
            return "panel" in name_l or "droid" in name_l or "home_panel" in entity_l
        return False

    for did in (
        "wife-iphone",
        "marshall-iphone",
        "family-ipad",
        "homebase-macbook",
        "home-panel-droid",
    ):
        if did in devices and not devices[did].get("ha_entity") and matches(did):
            devices[did]["ha_entity"] = entity_id
            devices[did]["role"] = (devices[did].get("role") or "").split(" · HA")[0] + " · HA linked"
            return did

    for did, d in devices.items():
        if not d.get("lan_arp") or d.get("ha_entity"):
            continue
        dn = d.get("name", "").lower()
        if "wife" in dn or "stephanie" in dn:
            if any(x in name_l or x in entity_l for x in ("wife", "stephanie", "cleroux", "cléroux")):
                d["ha_entity"] = entity_id
                return did
        if "ipad" in dn and ("ipad" in name_l or "ipad" in entity_l) and "iphone" not in entity_l:
            d["ha_entity"] = entity_id
            return did
    return None


def expand_ha_devices(devices: dict[str, dict], connections: list[dict], ha_states: dict[str, dict]) -> int:
    if not ha_states:
        return 0
    known_ips = {ip for d in devices.values() for ip in d.get("ips", []) if ip}
    known_entities = {d.get("ha_entity") for d in devices.values() if d.get("ha_entity")}
    known_entities |= {e for d in devices.values() for e in d.get("ha_entities", [])}
    added = 0
    phone_ids: dict[str, str] = {}
    trackers = [eid for eid in ha_states if eid.startswith("device_tracker.")]

    for eid in trackers:
        row = ha_states[eid]
        if eid in known_entities:
            continue
        attrs = row.get("attributes", {}) or {}
        ip = attrs.get("ip") or attrs.get("ipv4")
        if isinstance(ip, list):
            ip = ip[0] if ip else None
        if ip and ip in known_ips:
            continue
        name = attrs.get("friendly_name") or attrs.get("device_name") or eid.split(".", 1)[1].replace("_", " ").title()
        cid = canonical_id_for_ha(eid, name)
        if cid and cid in devices:
            devices[cid]["ha_entity"] = eid
            if ip and ip not in devices[cid].get("ips", []):
                devices[cid].setdefault("ips", []).append(ip)
            phone_ids[eid] = cid
            added += 1
            continue
        if ip and ip in known_ips:
            attached = False
            for did, d in devices.items():
                if ip not in d.get("ips", []):
                    continue
                if not d.get("ha_entity"):
                    d["ha_entity"] = eid
                phone_ids[eid] = did
                attached = True
                added += 1
                break
            if attached:
                continue
        merged = _merge_tracker_into_lan_device(devices, name, eid)
        if merged:
            phone_ids[eid] = merged
            added += 1
            continue
        if cid:
            did = cid
        else:
            did = f"ha-{slug_device_id(eid)}"
        if did in devices:
            if not devices[did].get("ha_entity"):
                devices[did]["ha_entity"] = eid
            phone_ids[eid] = did
            added += 1
            continue
        devices[did] = {
            "name": name,
            "type": "client",
            "role": "Mobile / tablet · Home Assistant tracker",
            "ips": [ip] if ip else [],
            "tailscale": [],
            "hardware": " ".join(x for x in (attrs.get("manufacturer"), attrs.get("model")) if x) or "Mobile device",
            "services": ["Home Assistant device_tracker"],
            "power_profile": "standby_capable",
            "ha_entity": eid,
            "discovered": True,
        }
        DEVICE_CAPACITY[did] = {
            "ram_gb": 0.064,
            "storage_gb": 0.256,
            "compute": 0.12,
            "short": name[:16],
            "personality": "edge",
            "capacity_note": f"HA tracker · {row.get('state', 'unknown')}",
        }
        eid_l = eid.lower()
        if any(k in eid_l for k in ("phone", "iphone", "ipad", "android", "mobile", "tablet")):
            phone_ids[eid] = did
        if ip:
            known_ips.add(ip)
        added += 1

    mapped_players = {d.get("ha_entity") for d in devices.values() if d.get("ha_entity", "").startswith("media_player.")}
    for eid, row in ha_states.items():
        if not eid.startswith("media_player."):
            continue
        if eid in mapped_players:
            continue
        attrs = row.get("attributes", {}) or {}
        name = attrs.get("friendly_name") or eid.split(".", 1)[1].replace("_", " ").title()
        source = str(attrs.get("source", "")).lower()
        if "bluetooth" not in source and "bluetooth" not in eid and "headphone" not in name.lower() and "airpod" not in name.lower():
            continue
        did = f"ha-{slug_device_id(eid)}"
        if did in devices:
            continue
        parent_id = None
        for peid, pdid in phone_ids.items():
            if peid.split(".")[-1].split("_")[0] in eid or peid.split(".")[-1] in eid:
                parent_id = pdid
                break
        devices[did] = {
            "name": name,
            "type": "iot",
            "role": "Bluetooth audio · personal peripheral",
            "ips": [],
            "tailscale": [],
            "hardware": attrs.get("device_class") or "Bluetooth media",
            "services": ["Bluetooth audio"],
            "power_profile": "standby_capable",
            "ha_entity": eid,
            "discovered": True,
        }
        DEVICE_CAPACITY[did] = {
            "ram_gb": 0.008,
            "storage_gb": 0.004,
            "compute": 0.04,
            "short": name[:16],
            "personality": "sensor",
            "capacity_note": "Bluetooth peripheral",
        }
        if parent_id:
            connections.append(
                {
                    "from": parent_id,
                    "to": did,
                    "medium": "bluetooth",
                    "traffic": "data",
                    "direction": "bidirectional",
                    "note": "Personal Bluetooth link",
                }
            )
        else:
            connections.append(
                {
                    "from": "router-gateway",
                    "to": did,
                    "medium": "bluetooth",
                    "traffic": "data",
                    "direction": "bidirectional",
                    "note": "Bluetooth device (no phone mapped yet)",
                }
            )
        added += 1
    return added


def parse_arp_table(subnet_prefix: str = LAN_SUBNET_PREFIX) -> dict[str, str]:
    """Return {ip: mac} for reachable LAN hosts from this Mac's ARP cache."""
    clients: dict[str, str] = {}
    for line in run(["arp", "-a"]).splitlines():
        match = re.search(r"\((\d+\.\d+\.\d+\.\d+)\) at ([0-9a-f:]{11,17})", line, re.I)
        if not match:
            continue
        ip, mac = match.group(1), match.group(2).lower()
        if ip.startswith(subnet_prefix) and not ip.endswith(".255") and mac != "ff:ff:ff:ff:ff:ff":
            clients[ip] = mac
    return clients


def load_helix_hints() -> dict[str, dict]:
    if not HELIX_ROUTER_FILE.exists():
        return {}
    try:
        data = json.loads(HELIX_ROUTER_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data.get("by_hostname") or {}


def apply_helix_mac_hints(arp: dict[str, str], by_ip: dict[str, dict], by_mac: dict[str, dict]) -> None:
    """Match Helix ESP hostnames to IPs via MAC suffix (ESP_18FE85 → …:18:fe:85)."""
    for hostname, spec in load_helix_hints().items():
        if not isinstance(spec, dict):
            continue
        suffix = spec.get("mac_suffix")
        prefix = spec.get("mac_prefix")
        for ip, mac in arp.items():
            if ip in by_ip:
                continue
            matched = False
            if suffix and mac.endswith(str(suffix).lower()):
                matched = True
            elif prefix and mac.startswith(str(prefix).lower()):
                matched = True
            elif "ESP_" in hostname:
                token = hostname.split("ESP_", 1)[-1].lower()
                compact = mac.replace(":", "")
                if token in compact:
                    matched = True
            if not matched:
                continue
            label = {
                "id": spec.get("id") or f"helix-{slug_device_id(hostname)}",
                "name": spec.get("name") or hostname,
                "short": spec.get("short") or hostname[:14],
                "personality": spec.get("personality", "sensor"),
                "hardware": spec.get("hardware") or f"Helix: {hostname}",
                "role": f"Helix router · {hostname}",
            }
            by_ip[ip] = label
            by_mac[mac] = label


def load_known_client_labels() -> tuple[dict[str, dict], dict[str, dict]]:
    by_ip: dict[str, dict] = {}
    by_mac: dict[str, dict] = {}
    if not KNOWN_CLIENTS_FILE.exists():
        return by_ip, by_mac
    try:
        data = json.loads(KNOWN_CLIENTS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return by_ip, by_mac
    if isinstance(data, dict):
        for ip, spec in (data.get("by_ip") or {}).items():
            if isinstance(spec, dict):
                by_ip[str(ip)] = spec
        for mac, spec in (data.get("by_mac") or {}).items():
            if isinstance(spec, dict):
                by_mac[str(mac).lower()] = spec
    return by_ip, by_mac


def enrich_ha_ips_from_arp(devices: dict[str, dict], arp: dict[str, str]) -> None:
    """Attach LAN IPs to HA device_tracker nodes when MAC matches ARP table."""
    mac_to_ip = {mac: ip for ip, mac in arp.items()}
    for did, d in devices.items():
        entity = d.get("ha_entity") or ""
        if not entity.startswith("device_tracker."):
            continue
        mac = (d.get("mac") or "").lower()
        if mac and mac in mac_to_ip and mac_to_ip[mac] not in d.get("ips", []):
            d.setdefault("ips", []).append(mac_to_ip[mac])


def discover_lan_clients(devices: dict[str, dict], connections: list[dict]) -> tuple[int, list[str], dict[str, str]]:
    """Add router-linked nodes for ARP-visible LAN clients not already mapped."""
    known_ips = {ip for d in devices.values() for ip in d.get("ips", []) if ip}
    by_ip, by_mac = load_known_client_labels()
    arp = parse_arp_table()
    arp = load_router_active_ips(arp)
    apply_helix_mac_hints(arp, by_ip, by_mac)
    enrich_ha_ips_from_arp(devices, arp)
    known_ips = {ip for d in devices.values() for ip in d.get("ips", []) if ip}
    added = 0
    unlabeled: list[str] = []

    for ip, mac in sorted(arp.items()):
        if ip in known_ips:
            for did, d in devices.items():
                if ip in d.get("ips", []):
                    d["lan_arp"] = True
                    if not d.get("mac"):
                        d["mac"] = mac
            continue
        spec = by_ip.get(ip) or by_mac.get(mac)
        if spec and spec.get("stale"):
            continue
        if spec:
            name = spec.get("name", f"Client {ip}")
            did = spec.get("id") or f"client-{slug_device_id(name)}"
            short = spec.get("short") or name[:16]
            personality = spec.get("personality", "edge")
            role = spec.get("role", "Known LAN client")
            hardware = spec.get("hardware") or f"MAC {mac}"
        else:
            name = f"Unknown · {ip}"
            did = f"arp-{ip.replace('.', '-')}"
            short = ip.split(".")[-1]
            personality = "sensor"
            role = "Unlabeled LAN client · add to known-clients.json"
            hardware = f"MAC {mac}"
            unlabeled.append(f"{ip}  {mac}")

        if did in devices:
            devices[did].setdefault("ips", [])
            if ip not in devices[did]["ips"]:
                devices[did]["ips"].append(ip)
            continue

        devices[did] = {
            "name": name,
            "type": (spec or {}).get("type", "client"),
            "role": role,
            "ips": [ip],
            "mac": mac,
            "tailscale": [],
            "hardware": hardware,
            "services": (spec or {}).get("services", []),
            "power_profile": (spec or {}).get("power_profile", "standby_capable"),
            "discovered": True,
            "lan_arp": True,
            "helix_name": (spec or {}).get("helix_name"),
        }
        DEVICE_CAPACITY[did] = {
            **DEFAULT_CAPACITY,
            **((spec or {}).get("capacity") or {}),
            "short": short,
            "personality": personality,
            "capacity_note": "Seen on LAN (ARP)" + (f" · {mac}" if not spec else ""),
        }
        connections.append(
            {
                "from": "router-gateway",
                "to": did,
                "medium": "wifi",
                "traffic": "routing",
                "direction": "bidirectional",
                "note": "LAN ARP discovery",
            }
        )
        known_ips.add(ip)
        added += 1

    return added, unlabeled, arp


def canonical_id_for_ha(entity_id: str, name: str) -> str | None:
    if entity_id in HA_ENTITY_CANONICAL:
        return HA_ENTITY_CANONICAL[entity_id]
    e = entity_id.lower()
    n = name.lower()
    if "stephanie" in n or "stephanie" in e or ("wife" in n and "iphone" in n):
        return "wife-iphone"
    if "ipad" in e and "iphone" not in e:
        return "family-ipad"
    if "mashall" in e or ("marshall" in n and "iphone" in n):
        return "marshall-iphone"
    if "homebase" in e or "homebase" in n:
        return "homebase-macbook"
    if "home_panel" in e or "panel droid" in n:
        return "w09n-frame"
    return None


def _merge_into_canonical(target: dict, source: dict, ha_states: dict[str, dict]) -> None:
    for ip in source.get("ips", []):
        if ip and ip not in target.setdefault("ips", []):
            target["ips"].append(ip)
    if source.get("mac") and not target.get("mac"):
        target["mac"] = source["mac"]
    ent = source.get("ha_entity")
    if ent and not target.get("ha_entity"):
        target["ha_entity"] = ent
    if source.get("name") and (
        not target.get("ha_entity") or "Unknown" in target.get("name", "") or target["name"].startswith("LAN ")
    ):
        target["name"] = source["name"]
    if ent and ent in ha_states:
        target["ha_state"] = ha_states[ent].get("state")
    target["discovered"] = target.get("discovered") or source.get("discovered")
    target["lan_arp"] = target.get("lan_arp") or source.get("lan_arp")
    if ent and ent in ha_states:
        attrs = ha_states[ent].get("attributes", {}) or {}
        fn = attrs.get("friendly_name")
        if fn:
            target["name"] = fn


def load_router_active_ips(arp: dict[str, str]) -> dict[str, str]:
    """ARP cache on the Mac is the live LAN view; optional router-online.json adds Helix exports."""
    active = dict(arp)
    router_file = VAULT / "router-online.json"
    if not router_file.exists():
        return active
    try:
        data = json.loads(router_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return active
    for ip in data.get("ips") or []:
        ip = str(ip)
        if ip.startswith(LAN_SUBNET_PREFIX):
            active.setdefault(ip, (data.get("macs") or {}).get(ip, ""))
    return active


def consolidate_devices(
    devices: dict[str, dict],
    connections: list[dict],
    ha_states: dict[str, dict],
    active_ips: dict[str, str],
) -> dict[str, str]:
    """Merge HA + LAN duplicates into one node per physical device."""
    id_remap: dict[str, str] = {}
    active_set = set(active_ips.keys())

    for did, d in list(devices.items()):
        ent = d.get("ha_entity")
        name = d.get("name", "")
        if not ent and did.startswith("ha-"):
            ent = d.get("ha_entity")
        if not ent:
            continue
        cid = canonical_id_for_ha(ent, name)
        if not cid:
            continue
        if cid not in devices:
            devices[cid] = {
                "name": name,
                "type": "client",
                "role": "Mobile · Home Assistant + Wi‑Fi",
                "ips": list(d.get("ips", [])),
                "mac": d.get("mac"),
                "tailscale": [],
                "hardware": d.get("hardware", "Mobile device"),
                "services": ["Home Assistant Companion"],
                "power_profile": "active_use",
                "ha_entity": ent,
                "discovered": True,
            }
            DEVICE_CAPACITY[cid] = {
                "ram_gb": 0.064,
                "storage_gb": 0.256,
                "compute": 0.12,
                "short": (DEVICE_CAPACITY.get(cid, {}).get("short") or name)[:16],
                "personality": "edge",
                "capacity_note": "HA Companion",
            }
        if did != cid:
            _merge_into_canonical(devices[cid], d, ha_states)
            id_remap[did] = cid

    # Merge arp-* into known ids sharing the same IP.
    for did, d in list(devices.items()):
        if not did.startswith("arp-"):
            continue
        ip = (d.get("ips") or [None])[0]
        if not ip:
            continue
        for cid, cd in devices.items():
            if cid == did or cid.startswith("arp-") or cid.startswith("ha-"):
                continue
            if ip in cd.get("ips", []):
                _merge_into_canonical(cd, d, ha_states)
                id_remap[did] = cid
                break

    for old, new in id_remap.items():
        if old in devices:
            del devices[old]

    for did, d in devices.items():
        d["_id"] = did
        ent = d.get("ha_entity")
        if ent and ent in ha_states:
            fn = ha_states[ent].get("attributes", {}).get("friendly_name")
            if fn:
                d["name"] = fn
                if did in DEVICE_CAPACITY:
                    DEVICE_CAPACITY[did]["short"] = fn[:16]

    rewire_connections(connections, id_remap)
    dedupe_connections(connections)
    filter_to_active_lan(devices, connections, active_set)
    ensure_client_path_links(devices, connections, ha_states, active_set)
    dedupe_connections(connections)
    return id_remap


def rewire_connections(connections: list[dict], id_remap: dict[str, str]) -> None:
    for c in connections:
        c["from"] = id_remap.get(c["from"], c["from"])
        c["to"] = id_remap.get(c["to"], c["to"])


def dedupe_connections(connections: list[dict]) -> None:
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict] = []
    for c in connections:
        key = (c["from"], c["to"], c.get("medium", ""))
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)
    connections[:] = unique


def filter_to_active_lan(
    devices: dict[str, dict],
    connections: list[dict],
    active_ips: set[str],
) -> None:
    """Drop stale LAN ghosts not in current ARP (= router-active proxy)."""
    remove: set[str] = set()
    for did, d in devices.items():
        if did in ALWAYS_ON_IDS:
            continue
        if d.get("stale") or did.endswith("-stale") or "stale arp" in d.get("name", "").lower():
            remove.add(did)
            continue
        if d.get("runs_on"):
            continue
        if not (d.get("discovered") or d.get("lan_arp") or did.startswith("arp-")):
            continue
        ips = [ip for ip in d.get("ips", []) if ip]
        if not ips:
            if d.get("ha_entity") and did in ("marshall-iphone", "wife-iphone", "family-ipad", "homebase-macbook"):
                continue
            remove.add(did)
            continue
        if not any(ip in active_ips for ip in ips):
            if d.get("ha_entity"):
                continue
            if (spec or {}).get("stale") or did.endswith("-stale") or "stale" in d.get("name", "").lower():
                remove.add(did)
                continue
            remove.add(did)
    for did in remove:
        del devices[did]
    connections[:] = [c for c in connections if c["from"] not in remove and c["to"] not in remove]


def ensure_client_path_links(
    devices: dict[str, dict],
    connections: list[dict],
    ha_states: dict[str, dict],
    active_ips: set[str],
) -> None:
    """Each client: Wi‑Fi→router when on LAN; HA app→homeassistant when tracked."""
    existing = {(c["from"], c["to"], c.get("medium", "")) for c in connections}

    def add(fr: str, to: str, medium: str, note: str) -> None:
        key = (fr, to, medium)
        if key in existing:
            return
        connections.append(
            {
                "from": fr,
                "to": to,
                "medium": medium,
                "traffic": "control" if medium == "ha_mobile" else "routing",
                "direction": "bidirectional",
                "note": note,
            }
        )
        existing.add(key)

    for did, d in devices.items():
        ent = d.get("ha_entity") or ""
        ips = d.get("ips", [])
        on_lan = any(ip in active_ips for ip in ips)

        if ent.startswith("device_tracker.") and "homeassistant" in devices:
            state = ha_states.get(ent, {}).get("state", "unknown")
            add("homeassistant", did, "ha_mobile", f"HA Companion · {state}")

        if on_lan and did not in ("router-gateway",) and "router-gateway" in devices:
            if d.get("type") in ("client", "iot", "network") or d.get("discovered") or d.get("lan_arp"):
                has_router = any(
                    c.get("from") == "router-gateway"
                    and c.get("to") == did
                    and str(c.get("medium", "")).startswith("wifi")
                    for c in connections
                )
                if not has_router:
                    add("router-gateway", did, "wifi", "Helix / LAN Wi‑Fi")


def summarize_ha_trackers(ha_states: dict[str, dict]) -> str:
    names = []
    for eid in sorted(ha_states):
        if not eid.startswith("device_tracker."):
            continue
        row = ha_states[eid]
        attrs = row.get("attributes", {}) or {}
        label = attrs.get("friendly_name") or eid.split(".", 1)[1]
        names.append(f"{label} ({row.get('state', '?')})")
    if not names:
        return "no device_tracker entities found"
    return ", ".join(names[:8]) + ("…" if len(names) > 8 else "")


def device_links(devices: dict[str, dict], connections: list[dict] | None = None) -> None:
    conns = connections if connections is not None else CONNECTIONS
    for d in devices.values():
        d["links"] = []
    for c in conns:
        fr, to = c["from"], c["to"]
        if fr in devices and to not in devices[fr]["links"]:
            devices[fr]["links"].append(to)
        if c.get("direction") == "bidirectional" and to in devices and fr not in devices[to]["links"]:
            devices[to]["links"].append(fr)


def resolve_mode(device: dict, ha_states: dict[str, dict]) -> str:
    if device.get("online") is False:
        return "offline"
    if device.get("online") is not True:
        return "unknown"

    profile = device.get("power_profile", "")
    if profile in ("always_on", "display_always_on"):
        return "active"

    entity = device.get("ha_entity")
    if entity and entity in ha_states:
        state = ha_states[entity].get("state", "unknown")
        attrs = ha_states[entity].get("attributes", {})
        if entity.startswith("media_player."):
            return "playing" if state == "playing" else "idle" if state in ("idle", "paused", "off") else state
        if entity.startswith("camera."):
            return "streaming" if state == "idle" else state
        return state

    entities = device.get("ha_entities", [])
    if entities and ha_states:
        on_count = sum(1 for e in entities if ha_states.get(e, {}).get("state") == "on")
        if on_count:
            return f"{on_count}_on"
        return "all_off"

    if device.get("http_ok"):
        return "active"
    if device.get("ports_open"):
        return "active"
    if profile == "active_use":
        return "active"
    if device.get("lan_arp") and device.get("online") is True and device.get("type") == "client":
        return "active"
    if profile in ("standby_capable", "on_demand", "switchable"):
        return "standby"
    if device.get("latency_ms") is not None:
        return "reachable"
    return "unknown"


def probe_devices(
    devices: dict[str, dict],
    zbook: str,
    ha_token: str | None,
    connections: list[dict] | None = None,
    ha_states: dict[str, dict] | None = None,
) -> dict:
    conns = connections if connections is not None else CONNECTIONS
    ha_base = f"http://{zbook}:8123"
    if ha_states is None:
        ha_states = ha_fetch_states(ha_base, ha_token or "")

    for d in devices.values():
        d.pop("online", None)
        d.pop("latency_ms", None)
        d.pop("packet_loss_pct", None)
        d.pop("mode", None)
        d.pop("http_ok", None)
        d.pop("ports_open", None)
        d.pop("ha_detail", None)

    for d in devices.values():
        for ip in d.get("ips", []):
            if re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
                if d.get("lan_routable") is False:
                    continue
                result = ping_probe(ip)
                d.update(result)
                break

    zb = devices["zbook-wifi"]
    for port in zb.get("probe_ports", []):
        if isinstance(port, int):
            zb.setdefault("ports", {})[str(port)] = tcp_probe(zbook, port)
    if zb.get("ports"):
        zb["ports_open"] = any(zb["ports"].values())

    for key in ("homeassistant", "w09n-frame"):
        url = devices[key].get("probe_http")
        if url:
            http = http_probe(url)
            devices[key]["http_ok"] = http["online"]
            devices[key]["http_code"] = http["code"]
            if http["online"]:
                devices[key]["online"] = True

    for key in ("minecraft-server", "chromecast"):
        d = devices[key]
        for spec in d.get("probe_ports", []):
            if isinstance(spec, tuple):
                port, _ = spec
            else:
                port = spec
            host = zbook if key != "chromecast" else d["ips"][0]
            open_ = tcp_probe(host, port)
            d.setdefault("ports", {})[str(port)] = open_
            if open_:
                d["ports_open"] = True
                d["online"] = True

    for key, d in devices.items():
        infer = d.get("infer_from", [])
        if not infer:
            continue
        if all(devices[s].get("online") for s in infer if s in devices):
            d["online"] = True
        elif d.get("online") is None:
            d["online"] = False

    for d in devices.values():
        ents = []
        if d.get("ha_entity"):
            ents.append(d["ha_entity"])
        ents.extend(d.get("ha_entities", []))
        details = []
        for e in ents:
            if e in ha_states:
                row = ha_states[e]
                details.append(f"{HA_ENTITIES.get(e, e)}: {row.get('state')}")
        if details:
            d["ha_detail"] = "; ".join(details)

    for d in devices.values():
        d["mode"] = resolve_mode(d, ha_states)

    ts = run(["tailscale", "status"])
    if ts:
        devices["mac-primary"]["tailscale_live"] = "100.88.199.80" in ts or "mf-mac-905" in ts

    path_health: list[dict] = []
    for c in conns:
        src = devices.get(c["from"], {})
        dst = devices.get(c["to"], {})
        src_ok = src.get("online") is True or src.get("http_ok") or src.get("ports_open")
        dst_ok = dst.get("online") is True or dst.get("http_ok") or dst.get("ports_open")
        if c["medium"] in ("docker_bridge", "portproxy", "logical") and devices.get("zbook-wifi", {}).get("online"):
            if c["to"] in ("wsl-ubuntu", "homeassistant", "minecraft-server", "minecraft-phantom", "zbook-webcam"):
                path_health.append({**c, "status": "up" if dst_ok or src_ok else "inferred"})
            else:
                path_health.append({**c, "status": "up" if src_ok and dst_ok else "degraded" if src_ok or dst_ok else "down"})
        else:
            if src_ok and dst_ok:
                status = "up"
            elif src_ok or dst_ok:
                status = "degraded"
            else:
                status = "unknown" if src.get("online") is None and dst.get("online") is None else "down"
            latencies = [x for x in (src.get("latency_ms"), dst.get("latency_ms")) if x is not None]
            path_health.append({**c, "status": status, "latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else None})

    return {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scanner": platform.node(),
        "ha_api": bool(ha_states),
        "ha_discovered": sum(1 for d in devices.values() if d.get("discovered")),
        "devices": devices,
        "connections": path_health,
    }


def write_device_note(path: Path, device_id: str, d: dict, devices: dict[str, dict], snapshot: dict) -> None:
    status = "online" if d.get("online") is True else "offline" if d.get("online") is False else "unknown"
    mode = d.get("mode", "unknown")
    conns = []
    for c in snapshot["connections"]:
        if c["from"] == device_id:
            peer = devices[c["to"]]["name"]
            meta = MEDIUM_META.get(c["medium"], {})
            conns.append(
                f"| → [[Devices/{safe_name(peer)}|{peer}]] | {meta.get('label', c['medium'])} | {c.get('direction', '—')} | {c.get('traffic', '—')} | {c.get('status', '—')} | {c.get('note', '')} |"
            )
        elif c["to"] == device_id and c.get("direction") == "bidirectional":
            peer = devices[c["from"]]["name"]
            meta = MEDIUM_META.get(c["medium"], {})
            conns.append(
                f"| ↔ [[Devices/{safe_name(peer)}|{peer}]] | {meta.get('label', c['medium'])} | bidirectional | {c.get('traffic', '—')} | {c.get('status', '—')} | {c.get('note', '')} |"
            )

    latency = d.get("latency_ms")
    loss = d.get("packet_loss_pct")
    ports = d.get("ports", {})
    port_block = "\n".join(f"- **{p}**: {'open' if v else 'closed'}" for p, v in sorted(ports.items())) if ports else ""
    links = [f"- [[Devices/{safe_name(t['name'])}|{t['name']}]]" for tid in d.get("links", []) if (t := devices.get(tid))]

    path.write_text(
        f"""---
type: device
status: {status}
mode: {mode}
latency_ms: {latency if latency is not None else 'null'}
packet_loss_pct: {loss if loss is not None else 'null'}
tags: [homelab, homeassistant]
generated: {snapshot['generated']}
---

# {d['name']}

> {d['role']}

| Field | Value |
|-------|-------|
| **Reachability** | **{status}** |
| **Mode** | **{mode}** |
| **Ping avg** | {f"{latency} ms" if latency is not None else '—'} |
| **Packet loss** | {f"{loss}%" if loss is not None else '—'} |
| **Address** | {', '.join(d.get('ips', [])) or '—'} |
| **Tailscale** | {', '.join(d.get('tailscale', [])) or '—'} |
| **HA state** | {d.get('ha_detail') or '—'} |

## Hardware
{d['hardware']}

## Services
"""
        + "\n".join(f"- {s}" for s in d.get("services", []))
        + (f"\n\n## Port check\n{port_block}\n" if port_block else "")
        + (
            "\n\n## Connections\n| Link | Medium | Direction | Traffic | Path | Notes |\n|------|--------|-----------|---------|------|-------|\n"
            + "\n".join(conns)
            if conns
            else "\n\n## Connections\n" + "\n".join(links)
        )
        + "\n",
        encoding="utf-8",
    )


def write_legend(path: Path) -> None:
    rows = "\n".join(
        f"| {m['label']} | `{key}` | {('dashed' if m.get('dashes') else 'solid')} |"
        for key, m in MEDIUM_META.items()
    )
    path.write_text(
        f"""# Connection Legend

How to read links in [[Network Map]] and [[network-graph.html]].

| Medium | Key | Line style |
|--------|-----|------------|
{rows}

## Traffic types
| Type | Meaning |
|------|---------|
| **routing** | IP packets to/from gateway |
| **management** | SSH, SMB, dashboards, admin |
| **control** | HA commands to devices |
| **data** | Media, game, or sensor payloads |
| **upstream** | Device → server (camera RTSP) |
| **downstream** | Server → device (dashboard, TTS) |

## Device modes
| Mode | Meaning |
|------|---------|
| **active** | Service running or device in use |
| **standby** | Reachable but idle |
| **playing / idle** | Cast speaker state (needs HA token) |
| **on / off / all_off** | Smart plug states (needs HA token) |
| **offline** | Ping/probe failed |
| **unknown** | Not probed or needs HA API token |

Set `HOMELAB_HA_TOKEN` for live plug/speaker/camera modes.
""",
        encoding="utf-8",
    )


def write_network_map(path: Path, snapshot: dict, devices: dict[str, dict]) -> None:
    live_note = "HA entity modes live" if snapshot["ha_api"] else "Set `HOMELAB_HA_TOKEN` for plug/speaker modes"
    hub = f"""# Homelab Network Map

Updated: **{snapshot['generated']}** from **{snapshot['scanner']}** · {live_note}

> **Not a live feed by default.** Obsidian Graph shows wiki-links (topology). Status refreshes when you run `python3 generate_network_map.py`. For auto-refresh, use `network-graph.html` with `--serve`.

## Quick views
- **Graph view** — Obsidian topology (static until refresh)
- **[[network-graph.html]]** — interactive map with medium colors, latency, path health
- **[[Connection Legend]]** — Wi-Fi vs Docker vs Cast explained

## Device status
| Device | Reachable | Mode | Ping |
|--------|-----------|------|------|
"""
    for d in devices.values():
        st = "online" if d.get("online") is True else "offline" if d.get("online") is False else "unknown"
        lat = f"{d['latency_ms']} ms" if d.get("latency_ms") is not None else "—"
        hub += f"| [[Devices/{safe_name(d['name'])}|{d['name']}]] | {st} | {d.get('mode', 'unknown')} | {lat} |\n"

    hub += "\n## Connection map\n| From | To | Medium | Traffic | Path | Notes |\n|------|----|--------|---------|------|-------|\n"
    for c in snapshot["connections"]:
        fr = devices[c["from"]]["name"]
        to = devices[c["to"]]["name"]
        medium = MEDIUM_META.get(c["medium"], {}).get("label", c["medium"])
        arrow = "↔" if c.get("direction") == "bidirectional" else "→"
        hub += f"| [[Devices/{safe_name(fr)}|{fr}]] | [[Devices/{safe_name(to)}|{to}]] | {medium} | {c.get('traffic', '—')} | {c.get('status', '—')} | {c.get('note', '')} |\n"

    hub += "\n```mermaid\nflowchart LR\n"
    for d in devices.values():
        nid = re.sub(r"[^a-zA-Z0-9]", "", d["name"])[:12]
        hub += f"  {nid}[{d['name']}]\n"
    seen: set[tuple[str, str]] = set()
    for c in snapshot["connections"][:16]:
        fr = re.sub(r"[^a-zA-Z0-9]", "", devices[c["from"]]["name"])[:12]
        to = re.sub(r"[^a-zA-Z0-9]", "", devices[c["to"]]["name"])[:12]
        key = tuple(sorted((fr, to)))
        if key in seen:
            continue
        seen.add(key)
        label = MEDIUM_META.get(c["medium"], {}).get("label", c["medium"])[:14]
        hub += f"  {fr} <-->|{label}| {to}\n"
    hub += "```\n"
    path.write_text(hub, encoding="utf-8")


POSITIONS_FILE = VAULT / "node-positions.json"


def load_positions() -> dict:
    if not POSITIONS_FILE.exists():
        return {}
    try:
        return json.loads(POSITIONS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_positions(data: dict) -> None:
    POSITIONS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# Capability model: RAM + storage + compute → sphere size (router is small; ZBook is largest).
DEVICE_CAPACITY: dict[str, dict] = {
    "router-gateway": {
        "ram_gb": 0.25, "storage_gb": 0.064, "compute": 0.08,
        "short": "Router", "personality": "hub",
        "capacity_note": "Gateway SoC · NAT/DHCP only",
    },
    "zbook-wifi": {
        "ram_gb": 32, "storage_gb": 1024, "compute": 1.0,
        "short": "ZBook", "personality": "workhorse",
        "capacity_note": "HP ZBook · Windows + WSL homelab host",
    },
    "wsl-ubuntu": {
        "ram_gb": 16, "storage_gb": 400, "compute": 0.82,
        "short": "WSL", "personality": "engine",
        "capacity_note": "Docker VM · shares ZBook silicon",
    },
    "homeassistant": {
        "ram_gb": 4, "storage_gb": 32, "compute": 0.35,
        "short": "Home Assistant", "personality": "service",
        "capacity_note": "Automation container · always-on hub",
    },
    "minecraft-server": {
        "ram_gb": 2, "storage_gb": 24, "compute": 0.4,
        "short": "Minecraft", "personality": "service",
        "capacity_note": "Paper + Geyser · 2 GB heap",
    },
    "minecraft-phantom": {
        "ram_gb": 0.128, "storage_gb": 0.01, "compute": 0.06,
        "short": "Phantom", "personality": "beacon",
        "capacity_note": "UDP LAN discovery proxy",
    },
    "mac-primary": {
        "ram_gb": 16, "storage_gb": 512, "compute": 0.78,
        "short": "This Mac", "personality": "edge",
        "capacity_note": "MF-MAC-905 daily driver",
    },
    "old-macbook": {
        "ram_gb": 8, "storage_gb": 256, "compute": 0.45,
        "short": "Old Mac", "personality": "edge",
        "capacity_note": "Legacy family Mac",
    },
    "w09n-frame": {
        "ram_gb": 0.5, "storage_gb": 4, "compute": 0.1,
        "short": "W09N Frame", "personality": "display",
        "capacity_note": "Android 4.4 kiosk panel",
    },
    "chromecast": {
        "ram_gb": 0.256, "storage_gb": 0.5, "compute": 0.12,
        "short": "Chromecast", "personality": "sensor",
        "capacity_note": "Cast receiver",
    },
    "kitchen-speaker": {
        "ram_gb": 0.128, "storage_gb": 0.05, "compute": 0.08,
        "short": "Kitchen Spk", "personality": "sensor",
        "capacity_note": "Cast speaker endpoint",
    },
    "smart-plugs": {
        "ram_gb": 0.016, "storage_gb": 0.008, "compute": 0.03,
        "short": "Tuya Plugs", "personality": "sensor",
        "capacity_note": "MCU · 3× Wi-Fi switches",
    },
    "zbook-webcam": {
        "ram_gb": 0.064, "storage_gb": 0.25, "compute": 0.14,
        "short": "Webcam", "personality": "sensor",
        "capacity_note": "RTSP stream via go2rtc",
    },
}

DEFAULT_CAPACITY = {
    "ram_gb": 0.5, "storage_gb": 1, "compute": 0.2,
    "short": None, "personality": "sensor", "capacity_note": "",
}

GLANCES_CONTAINER_MAP = {
    "homeassistant": "homeassistant",
    "minecraft_server": "minecraft-server",
}

PULSE_STRONG = frozenset({"active", "playing", "streaming"})
PULSE_SOFT = frozenset({"standby", "idle", "reachable", "all_off"})


def json_get(url: str, timeout: int = 8) -> dict | list | None:
    if not shutil.which("curl"):
        return None
    out = run(["curl", "-s", "--max-time", str(timeout), url])
    if not out.strip():
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def _bytes_to_gb(n: float) -> float:
    return round(n / (1024**3), 2)


def _glances_largest_fs(fs_rows: list) -> tuple[float, float]:
    best_size = 0.0
    best_pct = 0.0
    seen: set[float] = set()
    for row in fs_rows:
        if not isinstance(row, dict):
            continue
        size = float(row.get("size") or 0)
        if size <= 0 or size in seen:
            continue
        seen.add(size)
        if size > best_size:
            best_size = size
            best_pct = float(row.get("percent") or 0)
    return _bytes_to_gb(best_size), round(best_pct, 1)


def fetch_glances(host: str) -> dict | None:
    base = f"http://{host}:61208"
    for ver in (4, 3, 2):
        mem = json_get(f"{base}/api/{ver}/mem")
        cpu = json_get(f"{base}/api/{ver}/cpu")
        fs = json_get(f"{base}/api/{ver}/fs")
        quick = json_get(f"{base}/api/{ver}/quicklook")
        containers = json_get(f"{base}/api/{ver}/containers")
        if not isinstance(mem, dict) or not mem.get("total"):
            continue
        storage_gb, storage_used_pct = _glances_largest_fs(fs if isinstance(fs, list) else [])
        host_ram_gb = _bytes_to_gb(float(mem["total"]))
        payload: dict = {
            "api_version": ver,
            "host_ram_gb": host_ram_gb,
            "ram_used_pct": round(float(mem.get("percent") or 0), 1),
            "storage_gb": storage_gb,
            "storage_used_pct": storage_used_pct,
            "cpu_load_pct": round(float((cpu or {}).get("total") or (quick or {}).get("cpu") or 0), 1),
            "cpu_cores": int((cpu or {}).get("cpucore") or 0),
            "cpu_name": (quick or {}).get("cpu_name") if isinstance(quick, dict) else None,
            "containers": {},
        }
        if isinstance(containers, list):
            for c in containers:
                if not isinstance(c, dict):
                    continue
                name = c.get("name")
                if not name:
                    continue
                mem_u = float(c.get("memory_usage") or (c.get("memory") or {}).get("usage") or 0)
                mem_l = float(c.get("memory_limit") or (c.get("memory") or {}).get("limit") or 0)
                payload["containers"][name] = {
                    "cpu_load_pct": round(float(c.get("cpu_percent") or (c.get("cpu") or {}).get("total") or 0), 1),
                    "ram_used_pct": round(mem_u / mem_l * 100, 1) if mem_l else None,
                    "ram_gb": _bytes_to_gb(mem_u),
                    "status": c.get("status"),
                }
        return payload
    return None


def fetch_local_host_metrics() -> dict | None:
    if platform.system() != "Darwin":
        return None
    try:
        mem_bytes = int(run(["sysctl", "-n", "hw.memsize"]).strip() or "0")
        if mem_bytes <= 0:
            return None
        ram_gb = _bytes_to_gb(float(mem_bytes))
        df_out = run(["df", "-g", "/"]).strip().splitlines()
        storage_gb = 0.0
        storage_used_pct = 0.0
        if len(df_out) >= 2:
            parts = df_out[-1].split()
            if len(parts) >= 5:
                storage_gb = float(parts[1])
                storage_used_pct = float(parts[4].rstrip("%"))
        load = run(["sysctl", "-n", "vm.loadavg"]).strip()
        cpu_load_pct = 0.0
        if load:
            try:
                one_min = float(load.split()[1].strip("{,"))
                cores = int(run(["sysctl", "-n", "hw.logicalcpu"]).strip() or "4")
                cpu_load_pct = round(min(100.0, one_min / max(cores, 1) * 100), 1)
            except (ValueError, IndexError):
                pass
        ram_used_pct = None
        top_out = run(["top", "-l", "1", "-n", "0"])
        for line in top_out.splitlines():
            if "PhysMem" not in line:
                continue
            used_match = re.search(r"(\d+)([MG])\s+used", line)
            if used_match:
                used_val = float(used_match.group(1))
                used_gb = used_val if used_match.group(2) == "G" else used_val / 1024
                ram_used_pct = round(min(100.0, used_gb / max(ram_gb, 0.1) * 100), 1) if ram_gb else None
            break
        return {
            "source": "local",
            "ram_gb": ram_gb,
            "ram_used_pct": ram_used_pct,
            "storage_gb": storage_gb,
            "storage_used_pct": storage_used_pct,
            "cpu_load_pct": cpu_load_pct,
        }
    except (ValueError, OSError):
        return None


def apply_live_metrics(devices: dict[str, dict], glances: dict | None, local: dict | None) -> None:
    for d in devices.values():
        d.pop("metrics_live", None)

    if glances:
        host = {
            "source": f"glances:{glances['api_version']}",
            "ram_used_pct": glances["ram_used_pct"],
            "storage_used_pct": glances["storage_used_pct"],
            "cpu_load_pct": glances["cpu_load_pct"],
            "cpu_cores": glances.get("cpu_cores"),
            "cpu_name": glances.get("cpu_name"),
        }
        for did in ("zbook-wifi", "wsl-ubuntu"):
            if did in devices:
                devices[did]["metrics_live"] = dict(host)
        if glances["storage_gb"] > 0 and "zbook-wifi" in devices:
            static = DEVICE_CAPACITY.get("zbook-wifi", {})
            if glances["storage_gb"] > static.get("storage_gb", 0) * 0.5:
                devices["zbook-wifi"]["metrics_live"]["storage_gb_live"] = glances["storage_gb"]

        for cname, did in GLANCES_CONTAINER_MAP.items():
            c = glances.get("containers", {}).get(cname)
            if c and did in devices:
                devices[did]["metrics_live"] = {
                    "source": f"glances:container:{cname}",
                    "ram_used_pct": c.get("ram_used_pct"),
                    "cpu_load_pct": c.get("cpu_load_pct"),
                    "ram_gb_live": c.get("ram_gb"),
                    "container_status": c.get("status"),
                }

    if local and "mac-primary" in devices:
        devices["mac-primary"]["metrics_live"] = local


def pulse_level_for_mode(mode: str, status: str) -> str:
    if status == "offline":
        return "off"
    if mode in PULSE_STRONG or (mode.endswith("_on") and mode not in ("all_off",)):
        return "strong"
    if mode in PULSE_SOFT:
        return "soft"
    return "off"


def capability_score(spec: dict) -> float:
    ram = spec.get("ram_gb", 0.5)
    storage = spec.get("storage_gb", 1)
    compute = spec.get("compute", 0.2)
    ram_part = (ram + 0.15) ** 0.65 * 4.2
    storage_part = math.log10(storage + 1) * 9.5
    compute_part = compute * 14.0
    return ram_part + storage_part + compute_part


def val_from_capability(cap: float, max_cap: float) -> float:
    if max_cap <= 0:
        return 5.0
    ratio = cap / max_cap
    return round(3 + (ratio ** 0.82) * 18, 1)


def tier_from_ratio(ratio: float, personality: str) -> str:
    if personality == "hub":
        return "hub"
    if ratio >= 0.82:
        return "giant"
    if ratio >= 0.5:
        return "planet"
    if ratio >= 0.22:
        return "moon"
    return "asteroid"


def dynamic_layout_seeds(devices: dict[str, dict], base: dict[str, list]) -> dict[str, list]:
    seeds = dict(base)
    nest_offsets = {
        "wsl-ubuntu": ("zbook-wifi", 52, 0.0),
        "homeassistant": ("wsl-ubuntu", 34, 1.05),
        "minecraft-server": ("wsl-ubuntu", 40, 2.35),
        "minecraft-phantom": ("wsl-ubuntu", 36, 3.55),
        "zbook-webcam": ("wsl-ubuntu", 30, 4.75),
    }
    for child, (parent, radius, angle) in nest_offsets.items():
        if child not in devices or parent not in seeds:
            continue
        px, py, pz = seeds[parent]
        seeds[child] = [
            round(px + radius * math.cos(angle)),
            round(py + radius * 0.45 * math.sin(angle)),
            round(pz + radius * 0.35 * math.sin(angle * 0.9)),
        ]
    idx = 0
    for did in devices:
        if did in seeds:
            continue
        angle = idx * 0.85 + 1.2
        radius = 240 + (idx % 6) * 36
        seeds[did] = [
            round(radius * math.cos(angle)),
            round(radius * math.sin(angle) * 0.55),
            round(radius * math.sin(angle * 0.7) * 0.35),
        ]
        idx += 1
    return seeds


def nest_chain_label(did: str, devices: dict[str, dict]) -> str | None:
    chain: list[str] = []
    cur = did
    seen: set[str] = set()
    while True:
        parent = devices.get(cur, {}).get("runs_on")
        if not parent or parent in seen or parent not in devices:
            break
        seen.add(parent)
        spec = DEVICE_CAPACITY.get(parent, DEFAULT_CAPACITY)
        chain.insert(0, spec.get("short") or devices[parent]["name"])
        cur = parent
    return " → ".join(chain) if chain else None


def build_graph_payload(snapshot: dict, devices: dict[str, dict]) -> dict:
    type_colors = {
        "server": "#89b4fa",
        "service": "#cba6f7",
        "network": "#fab387",
        "client": "#94e2d5",
        "iot": "#f9e2af",
        "compute": "#74c7ec",
    }
    mode_border = {
        "active": "#a6e3a1",
        "streaming": "#a6e3a1",
        "playing": "#a6e3a1",
        "offline": "#f38ba8",
        "standby": "#f9e2af",
        "idle": "#89dceb",
        "all_off": "#89dceb",
        "reachable": "#74c7ec",
        "unknown": "#6c7086",
    }

    caps = {did: DEVICE_CAPACITY.get(did, DEFAULT_CAPACITY) for did in devices}
    scores = {did: capability_score(caps[did]) for did in devices}
    max_score = max(scores.values()) if scores else 1.0
    scanner_device_id = resolve_scanner_device_id(devices)

    nodes = []
    for did, d in devices.items():
        status = "online" if d.get("online") is True else "offline" if d.get("online") is False else "unknown"
        mode = d.get("mode", "unknown")
        spec = caps[did]
        cap = scores[did]
        ratio = cap / max_score if max_score else 0
        val = val_from_capability(cap, max_score)
        personality = spec.get("personality", "sensor")
        tier = tier_from_ratio(ratio, personality)
        short = spec.get("short") or d["name"]
        ram = spec.get("ram_gb", 0)
        storage = spec.get("storage_gb", 0)
        compute_pct = int(spec.get("compute", 0) * 100)
        runs_on = d.get("runs_on")
        nest_label = nest_chain_label(did, devices)
        title = "\\n".join(
            filter(
                None,
                [
                    d["name"],
                    d["role"],
                    f"Runs on: {nest_label}" if nest_label else None,
                    spec.get("capacity_note"),
                    f"Capability score: {cap:.1f} / {max_score:.1f}",
                    f"RAM {ram:g} GB · Storage {storage:g} GB · Compute {compute_pct}%",
                    f"Reachable: {status} · Mode: {mode}",
                    f"Ping: {d['latency_ms']} ms" if d.get("latency_ms") is not None else None,
                    d.get("ha_detail"),
                    ", ".join(d.get("ips", [])) or None,
                ],
            )
        )
        live = d.get("metrics_live") or {}
        live_bits = []
        if live.get("ram_used_pct") is not None:
            live_bits.append(f"RAM use {live['ram_used_pct']}%")
        if live.get("storage_used_pct") is not None:
            live_bits.append(f"Disk {live['storage_used_pct']}%")
        if live.get("cpu_load_pct") is not None:
            live_bits.append(f"CPU load {live['cpu_load_pct']}%")
        if live_bits:
            title += "\\nLive: " + " · ".join(live_bits)
            if live.get("source"):
                title += f" ({live['source']})"

        glow = 0.1 + spec.get("compute", 0.2) * 0.5
        if personality == "workhorse":
            glow = min(0.85, glow + 0.25)
        elif personality == "hub":
            glow = min(0.45, glow + 0.2)
        elif personality == "sensor":
            glow = min(0.18, glow)
        cpu_load = live.get("cpu_load_pct")
        if cpu_load is not None:
            glow = min(0.95, glow + (cpu_load / 100) * 0.12)

        pulse = pulse_level_for_mode(mode, status)
        nodes.append(
            {
                "id": did,
                "label": d["name"],
                "shortName": short,
                "group": d["type"],
                "status": status,
                "mode": mode,
                "tier": tier,
                "personality": personality,
                "title": title,
                "color": type_colors.get(d["type"], "#45475a"),
                "border": mode_border.get(mode.split("_")[0], mode_border.get(mode, "#6c7086")),
                "val": val,
                "capability": round(cap, 1),
                "capability_pct": round(ratio * 100),
                "ram_gb": ram,
                "storage_gb": storage,
                "compute": spec.get("compute", 0.2),
                "labelSize": round(3.8 + val * 0.22, 1),
                "glow": round(glow, 2),
                "pulse": pulse,
                "metrics": {
                    "ram_gb": ram,
                    "storage_gb": storage,
                    "compute_hw": spec.get("compute", 0.2),
                    "ram_used_pct": live.get("ram_used_pct"),
                    "storage_used_pct": live.get("storage_used_pct"),
                    "cpu_load_pct": live.get("cpu_load_pct"),
                    "source": live.get("source", "static"),
                },
                "ips": [ip for ip in d.get("ips", []) if re.match(r"^\d+\.\d+\.\d+\.\d+$", ip)],
                "discovered": bool(d.get("discovered")),
                "runs_on": runs_on,
                "nest_label": nest_label,
            }
        )

    edges = []
    seen: set[tuple[str, str, str]] = set()
    for i, c in enumerate(snapshot["connections"]):
        key = (c["from"], c["to"], c["medium"])
        if key in seen:
            continue
        seen.add(key)
        meta = MEDIUM_META.get(c["medium"], {})
        status = c.get("status", "unknown")
        edge_color = meta.get("color", "#78909c")
        if status == "down":
            edge_color = "#f38ba8"
        elif status == "degraded":
            edge_color = "#fab387"

        label_parts = [meta.get("label", c["medium"])]
        if c.get("latency_ms") is not None:
            label_parts.append(f"{c['latency_ms']}ms")
        label_parts.append(status)

        edge: dict = {
            "id": f"e{i}",
            "source": c["from"],
            "target": c["to"],
            "from": c["from"],
            "to": c["to"],
            "medium": c["medium"],
            "label": " · ".join(label_parts),
            "title": c.get("note", ""),
            "color": edge_color,
            "width": 2 if status == "up" else 1,
            "directed": c.get("direction") not in ("bidirectional", None),
        }
        edges.append(edge)

    base_seeds = {
        "router-gateway": [0, 0, 0],
        "zbook-wifi": [180, 0, 0],
        "wsl-ubuntu": [260, -80, 30],
        "homeassistant": [260, 60, -30],
        "mac-primary": [-160, 100, 50],
        "old-macbook": [-160, -100, 50],
        "w09n-frame": [80, 160, -80],
        "chromecast": [-80, 160, 80],
        "kitchen-speaker": [-200, 180, 0],
        "smart-plugs": [-200, -60, 100],
        "minecraft-server": [340, -100, -50],
        "minecraft-phantom": [400, -140, 0],
        "zbook-webcam": [240, -160, -80],
    }

    return {
        "generated": snapshot["generated"],
        "scanner": snapshot["scanner"],
        "scanner_device_id": scanner_device_id,
        "viewer_index": build_viewer_index(devices),
        "ha_api": snapshot["ha_api"],
        "ha_discovered": snapshot.get("ha_discovered", 0),
        "arp_discovered": snapshot.get("arp_discovered", 0),
        "glances": snapshot.get("glances"),
        "medium_legend": {k: v["label"] for k, v in MEDIUM_META.items()},
        "saved_positions": load_positions(),
        "layout_seeds": dynamic_layout_seeds(devices, base_seeds),
        "orbit_hubs": ["router-gateway", "zbook-wifi"],
        "nodes": nodes,
        "edges": edges,
    }


def write_html(path: Path, payload: dict) -> None:
    template_path = VAULT / "network-graph-template.html"
    template = template_path.read_text(encoding="utf-8") if template_path.exists() else "<html><body>Missing network-graph-template.html</body></html>"
    json_blob = json.dumps(payload, ensure_ascii=True).replace("</", "<\\/")
    path.write_text(template.replace("__NETWORK_DATA_JSON__", json_blob), encoding="utf-8")


def generate(zbook: str, ha_token: str | None) -> dict:
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ha_base = f"http://{zbook}:8123"
    ha_states = ha_fetch_states(ha_base, ha_token or "")
    connections = [dict(c) for c in CONNECTIONS]
    devices = {k: dict(v) for k, v in DEVICES.items()}
    load_extra_devices(devices, connections)
    arp_added, arp_unlabeled, active_arp = discover_lan_clients(devices, connections)
    ha_added = expand_ha_devices(devices, connections, ha_states)
    merged = consolidate_devices(devices, connections, ha_states, active_arp)
    device_links(devices, connections)
    snapshot = probe_devices(devices, zbook, ha_token, connections, ha_states)
    snapshot["generated"] = generated
    snapshot["ha_discovered"] = ha_added
    snapshot["arp_discovered"] = arp_added
    snapshot["arp_unlabeled"] = arp_unlabeled
    snapshot["active_arp_count"] = len(active_arp)
    snapshot["devices_merged"] = len(merged)
    glances = fetch_glances(zbook) if devices.get("zbook-wifi", {}).get("ports", {}).get("61208") else None
    if glances is None and tcp_probe(zbook, 61208):
        glances = fetch_glances(zbook)
    local_metrics = fetch_local_host_metrics()
    apply_live_metrics(devices, glances, local_metrics)
    snapshot["glances"] = bool(glances)
    snapshot["local_metrics"] = bool(local_metrics)

    dev_dir = VAULT / "Devices"
    dev_dir.mkdir(parents=True, exist_ok=True)
    for did, d in devices.items():
        write_device_note(dev_dir / f"{safe_name(d['name'])}.md", did, d, devices, snapshot)

    write_legend(VAULT / "Connection Legend.md")
    write_network_map(VAULT / "Network Map.md", snapshot, devices)
    payload = build_graph_payload(snapshot, devices)
    (VAULT / "network-data.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_html(VAULT / "network-graph.html", payload)
    if ha_states:
        print(f"[+] HA: {summarize_ha_trackers(ha_states)}")
        if ha_added:
            print(f"[+] Added {ha_added} device(s) from Home Assistant")
    if arp_added:
        print(f"[+] LAN ARP: added {arp_added} client(s) from Wi‑Fi scan")
    if merged:
        print(f"[+] Merged {len(merged)} duplicate node(s) · active LAN: {len(active_arp)} IP(s)")
    unlabeled = snapshot.get("arp_unlabeled") or []
    if unlabeled:
        print("[i] Unlabeled LAN clients (match in router DHCP, then add to known-clients.json):")
        for row in unlabeled[:12]:
            print(f"    {row}")
        if len(unlabeled) > 12:
            print(f"    … and {len(unlabeled) - 12} more")
    return snapshot


def serve(vault: Path, zbook: str, ha_token: str | None, interval: int, bind: str) -> None:
    generate(zbook, ha_token)
    viewer_state = {"index": json.loads((vault / "network-data.json").read_text())["viewer_index"]}

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(vault), **kwargs)

        def do_GET(self) -> None:
            path = self.path.split("?", 1)[0]
            if path == "/api/viewer":
                client_ip = self.client_address[0]
                hostname = platform.node()
                match = match_viewer_device(client_ip, hostname, viewer_state["index"])
                body = json.dumps(
                    {
                        "ip": client_ip,
                        "device_id": match["id"] if match else None,
                        "device_name": match["short"] if match else None,
                        "scanner": hostname,
                    }
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()

        def do_POST(self) -> None:
            if self.path != "/api/positions":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body.decode("utf-8"))
                save_positions(data)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            except (json.JSONDecodeError, OSError) as exc:
                self.send_error(400, str(exc))

        def do_DELETE(self) -> None:
            if self.path != "/api/positions":
                self.send_error(404)
                return
            if POSITIONS_FILE.exists():
                POSITIONS_FILE.unlink()
            self.send_response(200)
            self.end_headers()

        def log_message(self, fmt: str, *args) -> None:
            first = str(args[0]) if args else ""
            if "/api/" not in first:
                super().log_message(fmt, *args)

    def regen_loop() -> None:
        while True:
            time.sleep(interval)
            try:
                generate(zbook, ha_token)
                viewer_state["index"] = json.loads((vault / "network-data.json").read_text())["viewer_index"]
                print(f"[+] Refreshed {datetime.now():%H:%M:%S}")
            except Exception as exc:
                print(f"[!] Refresh failed: {exc}", file=sys.stderr)

    if interval > 0:
        threading.Thread(target=regen_loop, daemon=True).start()

    port = 8765
    local_ips = []
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect((zbook, 80))
        local_ips.append(probe.getsockname()[0])
        probe.close()
    except OSError:
        pass

    print(f"[*] Serving {vault} on {bind}:{port} (refresh every {interval}s)")
    if bind in ("0.0.0.0", "::"):
        print("[*] LAN viewers (no Python/Obsidian needed — just a browser link):")
        for lip in local_ips:
            print(f"    http://{lip}:{port}/network-graph.html")
        print(f"    Tailscale: http://<this-machine-tailscale-ip>:{port}/network-graph.html")
    print(f"[*] Local: http://127.0.0.1:{port}/network-graph.html")
    print("[*] Press Ctrl+C to stop")
    if bind in ("127.0.0.1", "localhost"):
        webbrowser.open(f"http://127.0.0.1:{port}/network-graph.html")
    server = ThreadingHTTPServer((bind, port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopped")


def main() -> int:
    ap = argparse.ArgumentParser(description="Homelab Obsidian + live network map")
    ap.add_argument("--zbook", default="10.0.0.169")
    ap.add_argument("--open", action="store_true", help="Open HTML graph in browser")
    ap.add_argument("--serve", action="store_true", help="Serve live dashboard on :8765")
    ap.add_argument("--bind", default="0.0.0.0", help="Bind address (0.0.0.0 = all LAN devices can open the link)")
    ap.add_argument("--interval", type=int, default=30, help="Auto-regenerate seconds when serving")
    ap.add_argument("--watch", type=int, metavar="SEC", help="Regenerate every N seconds (no server)")
    args = ap.parse_args()

    ha_token = resolve_ha_token()

    if args.serve:
        if not ha_token:
            print("[!] HA token missing — phones/tablets will NOT appear on the map")
            print(f"[i] Create {VAULT / 'ha-token.local'} with your long-lived token, or:")
            print("[i]   export HOMELAB_HA_TOKEN='your-token'")
        serve(VAULT, args.zbook, ha_token, args.interval, args.bind)
        return 0

    print("[*] Scanning LAN from this Mac...")
    if not ha_token:
        print("[!] HA token missing — phones/tablets will NOT be discovered")
        print(f"[i] Add token: {VAULT / 'ha-token.local'}  (see ha-token.local.example)")
    generate(args.zbook, ha_token)
    print(f"[+] Vault updated: {VAULT}")
    print(f"[+] Live dashboard: python3 {VAULT}/generate_network_map.py --serve")

    if args.watch:
        while True:
            time.sleep(args.watch)
            generate(args.zbook, ha_token)
            print(f"[+] Refreshed {datetime.now():%H:%M:%S}")

    if args.open:
        webbrowser.open((VAULT / "network-graph.html").as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
