#!/usr/bin/env python3
"""Generate Obsidian vault + live HTML graph for ZBook home lab (run on Mac)."""
from __future__ import annotations

import argparse
import asyncio
import copy
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
from typing import Any, Awaitable, Callable

VAULT = Path(__file__).resolve().parent

HOME_ASSISTANT_HOST = "10.0.0.8"
ZBOOK_HOST = "10.0.0.169"

# Glances API per map node (Windows svchost owns :61208 on ZBook — use :61209).
GLANCES_HOSTS: dict[str, tuple[str, int]] = {
    "zbook-wifi": (ZBOOK_HOST, 61209),
    "old-macbook": (HOME_ASSISTANT_HOST, 61208),
}

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
        "kitchen-speaker",
        "smart-plugs",
    }
)

# Map HA device_tracker entity → one canonical graph node id.
HA_ENTITY_CANONICAL: dict[str, str] = {
    "device_tracker.mashall_spratts_iphone": "marshall-iphone",
    "device_tracker.stephanie_clerouxs_iphone": "wife-iphone",
    "device_tracker.homebase_macbook": "old-macbook",
    "device_tracker.home_panel_droid": "w09n-frame",
    "device_tracker.ipad": "family-ipad",
}

# Map router-clients.json canonical_id → existing graph node ids.
ROUTER_ID_ALIASES: dict[str, str] = {
    "mf-mac-905": "mac-primary",
    "zbook": "zbook-wifi",
    "stephanie-iphone": "wife-iphone",
    "fridge": "smart-fridge",
    "google-home-mini": "kitchen-speaker",
    "android-tablet": "w09n-frame",
}

# Same physical hardware, different discovery sources — merge into one graph node.
PHYSICAL_ALIASES: dict[str, str] = {
    "homebase-macbook": "old-macbook",
    "zbook-webcam": "zbook-wifi",
    "arp-10-0-0-182": "marshall-iphone",
    "fire-tablet": "marshall-iphone",
    "chromecast": "kitchen-speaker",
    "qca4002": "lg-washer",
    "qca4002-69": "lg-dryer",
}

SCANNER_DEVICE_ALIASES = {
    "mf-mac-905": "mac-primary",
    "tests-macbook-pro": "old-macbook",
    "desktop-d1h9i0p": "zbook-wifi",
}

EXTRA_DEVICES_FILE = VAULT / "extra-devices.json"
HA_TOKEN_FILES = (VAULT / "ha-token.local", VAULT / ".ha-token")
KNOWN_CLIENTS_FILE = VAULT / "known-clients.json"
ROUTER_CLIENTS_FILE = VAULT / "router-clients.json"
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
        "role": "Basement server (Windows · RTSP · media)",
        "ips": ["10.0.0.169"],
        "tailscale": ["100.97.161.68"],
        "hardware": "HP ZBook · DESKTOP-D1H9I0P",
        "services": ["Glances :61209", "Basement RTSP :8554", "SMB ZBookShare :445", "Ollama :11434"],
        "power_profile": "always_on",
        "probe_ports": [61209, 8554, 445],
        "ha_entities": ["camera.basement_webcam"],
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
        "role": "Automation hub · Docker on Home Base Mac",
        "runs_on": "old-macbook",
        "ips": ["10.0.0.8"],
        "tailscale": [],
        "hardware": "Docker Compose · Trusted Networks auth",
        "services": ["/live-kiosk", "/frame-panel", "Tuya plugs", "Cast", "Robot Intercom", "go2rtc :1984"],
        "power_profile": "always_on",
        "probe_http": f"http://{HOME_ASSISTANT_HOST}:8123/",
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
        "name": "HomeBase MacBook Pro",
        "type": "server",
        "role": "Primary HA host · Home Base Mac",
        "ips": ["10.0.0.8"],
        "tailscale": [],
        "hardware": "HomeBases-MBP · Tests-MacBook-Pro",
        "services": ["Home Assistant :8123", "go2rtc :1984", "Glances :61208", "Home Assistant Companion"],
        "power_profile": "always_on",
        "probe_ports": [8123, 61208, 1984],
        "ha_entity": "device_tracker.homebase_macbook",
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
        "probe_http": f"http://{HOME_ASSISTANT_HOST}:8123/frame-panel",
    },
    "kitchen-speaker": {
        "name": "Kitchen Speaker",
        "type": "iot",
        "role": "Google Home Mini · Cast media · Robot Intercom TTS",
        "ips": ["10.0.0.14"],
        "tailscale": [],
        "hardware": "Google Home Mini · media_player.kitchen_speaker",
        "services": ["Google Cast :8009", "TTS output"],
        "power_profile": "standby_capable",
        "ha_entity": "media_player.kitchen_speaker",
        "probe_ports": [(8009, "tcp")],
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
            "switch.plug_4_socket_1",
        ],
    },
}

CONNECTIONS: list[dict] = [
    {"from": "router-gateway", "to": "zbook-wifi", "medium": "wifi_5g", "traffic": "routing", "direction": "bidirectional", "note": "ZBook wireless uplink"},
    {"from": "router-gateway", "to": "mac-primary", "medium": "wifi", "traffic": "routing", "direction": "bidirectional", "note": "Daily driver Mac"},
    {"from": "router-gateway", "to": "old-macbook", "medium": "wifi", "traffic": "routing", "direction": "bidirectional", "note": "Family Mac"},
    {"from": "router-gateway", "to": "w09n-frame", "medium": "wifi_2g", "traffic": "routing", "direction": "bidirectional", "note": "Frame on 2.4 GHz SSID"},
    {"from": "router-gateway", "to": "kitchen-speaker", "medium": "wifi", "traffic": "routing", "direction": "bidirectional", "note": "Google Home Mini"},
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
    {"from": "zbook-wifi", "to": "homeassistant", "medium": "rtsp", "traffic": "upstream", "note": "Basement webcam via go2rtc"},
]

HA_ENTITIES = {
    "switch.plug_1_socket_1": "Plug 1 · Desk",
    "switch.plug_2_socket_1": "Plug 2 · Shed",
    "switch.plug_3_socket_1": "Plug 3 · Command Central",
    "switch.plug_4_socket_1": "Plug 4",
    "media_player.kitchen_speaker": "Kitchen Speaker",
    "camera.172_27_128_1": "Basement Webcam",
}

# Diagnostic fallback matrix — broad HA smart-plug / outlet entity matching (not Tuya-only).
PLUG_ENTITY_MATCH_RULES: list[dict[str, Any]] = [
    {"rule": "domain", "match": ("switch.", "light."), "weight": 1},
    {"rule": "device_class", "match": ("outlet",), "weight": 3},
    {"rule": "entity_regex", "match": (r"plug[_\-\d]", r"socket[_\-\d]", r"smart[_\-]?plug", r"outlet"), "weight": 3},
    {"rule": "keyword", "match": ("plug", "outlet", "strip", "socket", "smart_plug", "tuya", "gosund", "kasa"), "weight": 2},
]

PLUG_ENTITY_EXCLUDE_KEYWORDS = (
    "flightradar",
    "api_data",
    "fetching",
    "dryer",
    "washer",
    "relay",
    "automation",
    "template",
    "integration",
    "rest_command",
    "input_boolean",
    "scene.",
)


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
        if did == "old-macbook":
            return "homebase" in name_l or "homebase" in entity_l
        if did == "home-panel-droid":
            return "panel" in name_l or "droid" in name_l or "home_panel" in entity_l
        return False

    for did in (
        "wife-iphone",
        "marshall-iphone",
        "family-ipad",
        "old-macbook",
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


def is_ha_smart_plug_entity(entity_id: str, attrs: dict | None) -> bool:
    """Return True when an HA switch/light entity represents a smart plug or outlet."""
    if not entity_id or "." not in entity_id:
        return False
    domain = entity_id.split(".", 1)[0] + "."
    if domain not in ("switch.", "light."):
        return False
    attrs = attrs or {}
    friendly = str(attrs.get("friendly_name") or "")
    device_class = str(attrs.get("device_class") or "").lower()
    blob = f"{entity_id} {friendly} {device_class}".lower()

    if any(ex in blob for ex in PLUG_ENTITY_EXCLUDE_KEYWORDS):
        if device_class != "outlet" and not re.search(r"plug[_\-\d]|socket[_\-\d]", entity_id, re.I):
            return False

    score = 0
    for rule in PLUG_ENTITY_MATCH_RULES:
        kind = rule["rule"]
        weight = int(rule.get("weight", 1))
        targets = rule["match"]
        if kind == "domain" and domain in targets:
            score += weight
        elif kind == "device_class" and device_class in targets:
            score += weight
        elif kind == "keyword" and any(kw in blob for kw in targets):
            score += weight
        elif kind == "entity_regex" and any(re.search(pat, entity_id, re.I) for pat in targets):
            score += weight

    if device_class == "outlet":
        return True
    if re.search(r"plug[_\-\d]|socket[_\-\d]", entity_id, re.I):
        return True
    return score >= 3


def canonical_plug_device_id(entity_id: str, friendly_name: str) -> str:
    match = re.search(r"plug[_\-]?(\d+)", entity_id, re.I)
    if match:
        return f"plug-{match.group(1)}"
    slug = slug_device_id(friendly_name or entity_id.split(".", 1)[-1])
    return f"plug-{slug}"


def format_plug_display_name(entity_id: str, attrs: dict | None) -> str:
    """Human-readable per-plug label for graph nodes (never the aggregate 'Tuya Plugs' string)."""
    if entity_id in HA_ENTITIES:
        return HA_ENTITIES[entity_id]
    attrs = attrs or {}
    raw = str(attrs.get("friendly_name") or entity_id.split(".", 1)[-1].replace("_", " "))
    match = re.search(r"plug[_\s\-]*(\d+)", raw, re.I)
    if match:
        plug_num = match.group(1)
        suffix = re.sub(r"plug[_\s\-]*\d+[_\s\-]*", "", raw, flags=re.I).strip(" -_")
        suffix = re.sub(r"socket\s*\d+", "", suffix, flags=re.I).strip(" -_")
        if suffix and suffix.lower() not in ("socket", "socket 1", ""):
            return f"Plug {plug_num} · {suffix.title()}"
        return f"Plug {plug_num}"
    return raw.title()


def resolve_plug_network_attachment(
    attrs: dict,
    by_ip: dict[str, dict],
    by_mac: dict[str, dict],
    arp: dict[str, str],
) -> tuple[str | None, str | None, str]:
    """IP/MAC match fallback matrix for cloud-only Tuya plugs."""
    ip = attrs.get("ip") or attrs.get("ipv4")
    if isinstance(ip, list):
        ip = ip[0] if ip else None
    ip = str(ip).strip() if ip else None
    mac = normalize_mac(attrs.get("mac") or attrs.get("mac_address"))

    if mac and mac in by_mac:
        reg_ip = str((by_mac[mac].get("ip") or "")).strip() or None
        return reg_ip or ip, mac, "router_mac_registry"
    if ip and ip in by_ip:
        return ip, mac or normalize_mac(by_ip[ip].get("mac")), "router_ip_registry"
    if mac:
        for arp_ip, arp_mac in arp.items():
            if normalize_mac(arp_mac) == mac:
                return arp_ip, mac, "arp_mac"
    if ip and ip in arp:
        return ip, normalize_mac(arp.get(ip)) or mac, "arp_ip"
    if ip:
        return ip, mac, "ha_attribute_ip"
    return None, mac or None, "ha_cloud_only"


def tether_plug_connections(
    did: str,
    connections: list[dict],
    *,
    attachment: str,
    note_suffix: str,
) -> None:
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
                "traffic": "control" if medium == "cloud_api" else "routing",
                "direction": "bidirectional",
                "note": note,
            }
        )
        existing.add(key)

    if attachment in ("router_mac_registry", "router_ip_registry", "arp_mac", "arp_ip", "ha_attribute_ip"):
        add("router-gateway", did, "wifi_2g", f"Smart plug · LAN Wi‑Fi · {note_suffix}")
    else:
        add("router-gateway", did, "wifi_2g", f"Smart plug · cloud IoT (no LAN IP) · {note_suffix}")
        add("homeassistant", did, "cloud_api", f"Tuya / HA cloud control · {note_suffix}")


def expand_ha_smart_plugs(
    devices: dict[str, dict],
    connections: list[dict],
    ha_states: dict[str, dict],
    arp: dict[str, str] | None = None,
) -> tuple[int, list[dict]]:
    """Discover every HA smart plug/outlet and materialize one graph node per plug."""
    if not ha_states:
        return 0, []

    arp = arp or {}
    by_ip, by_mac = load_client_labels()
    mapped_entities = {
        d.get("ha_entity")
        for d in devices.values()
        if d.get("ha_entity")
    }
    mapped_entities |= {e for d in devices.values() for e in d.get("ha_entities", [])}

    diagnostics: list[dict] = []
    discovered_ids: list[str] = []
    all_entities: list[str] = []

    plug_candidates = [
        (eid, row)
        for eid, row in ha_states.items()
        if is_ha_smart_plug_entity(eid, row.get("attributes") or {})
    ]

    for entity_id, row in sorted(plug_candidates):
        attrs = row.get("attributes") or {}
        friendly = format_plug_display_name(entity_id, attrs)
        state = str(row.get("state", "unknown"))
        did = canonical_plug_device_id(entity_id, friendly)
        ip, mac, attachment = resolve_plug_network_attachment(attrs, by_ip, by_mac, arp)
        all_entities.append(entity_id)

        diag = {
            "entity_id": entity_id,
            "node_id": did,
            "friendly_name": friendly,
            "state": state,
            "attachment": attachment,
            "ip": ip,
            "mac": mac,
            "included": True,
            "reason": "matched_plug_rules",
        }
        diagnostics.append(diag)

        if did in devices and devices[did].get("ha_entity") not in (None, entity_id):
            existing_ent = devices[did].get("ha_entity")
            did = f"{did}-{slug_device_id(entity_id.split('.', 1)[1])}"
            diag["node_id"] = did
            diag["reason"] = f"deduped_from_{existing_ent}"

        online: bool | None
        if state == "unavailable":
            online = False
        elif state in ("on", "off"):
            online = True
        else:
            online = None

        devices[did] = {
            "name": friendly,
            "type": "iot",
            "role": "Smart plug · Home Assistant outlet",
            "ips": [ip] if ip else [],
            "mac": mac,
            "tailscale": [],
            "hardware": " ".join(x for x in (attrs.get("manufacturer"), attrs.get("model")) if x)
            or "Wi‑Fi smart plug",
            "services": [entity_id],
            "power_profile": "switchable",
            "ha_entity": entity_id,
            "ha_plug": True,
            "discovered": True,
            "online": online,
            "mode": state if state in ("on", "off", "unavailable") else "unknown",
            "ha_detail": f"{friendly}: {state}",
        }
        DEVICE_CAPACITY[did] = {
            "ram_gb": 0.016,
            "storage_gb": 0.008,
            "compute": 0.03,
            "short": friendly[:16],
            "personality": "sensor",
            "capacity_note": f"Smart plug · {state} · {attachment}",
        }
        tether_plug_connections(did, connections, attachment=attachment, note_suffix=friendly)
        mapped_entities.add(entity_id)
        discovered_ids.append(did)

    if discovered_ids:
        if "smart-plugs" in devices:
            devices["smart-plugs"]["ha_entities"] = sorted(set(all_entities))
        connections[:] = [
            c for c in connections if c.get("from") != "smart-plugs" and c.get("to") != "smart-plugs"
        ]
        devices.pop("smart-plugs", None)
        DEVICE_CAPACITY.pop("smart-plugs", None)

    return len(discovered_ids), diagnostics


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


def normalize_mac(mac: str | None) -> str:
    if not mac:
        return ""
    return str(mac).lower().replace("-", ":")


def resolve_router_canonical_id(raw_id: str | None) -> str:
    cid = slug_device_id(raw_id or "unknown")
    return ROUTER_ID_ALIASES.get(cid, cid)


def router_personality(hostname: str, canonical_id: str) -> str:
    host = hostname.lower()
    cid = canonical_id.lower()
    if any(x in host or x in cid for x in ("esp_", "esp-", "ct-", "bulb", "led", "plug", "fridge", "refrigerator", "qca")):
        return "sensor"
    if any(x in host or x in cid for x in ("iphone", "ipad", "mac", "xbox", "galaxy", "android", "tablet")):
        return "edge"
    if "mini" in host or "speaker" in cid:
        return "sensor"
    return "edge"


def load_router_client_entries() -> list[dict]:
    if not ROUTER_CLIENTS_FILE.exists():
        return []
    try:
        data = json.loads(ROUTER_CLIENTS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    rows = data.get("devices") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict) and row.get("mac")]


def load_router_client_labels() -> tuple[dict[str, dict], dict[str, dict]]:
    """Build by_mac / by_ip lookup tables from router-clients.json (authoritative)."""
    by_ip: dict[str, dict] = {}
    by_mac: dict[str, dict] = {}
    helix = load_helix_hints()
    for row in load_router_client_entries():
        mac = normalize_mac(row.get("mac"))
        ip = str(row.get("ip") or "").strip()
        if not mac:
            continue
        hostname = str(row.get("hostname") or mac)
        did = resolve_router_canonical_id(row.get("canonical_id") or hostname)
        hint = helix.get(hostname, {}) if isinstance(helix.get(hostname), dict) else {}
        name = hint.get("name") or hostname.replace("_", " ").replace("-", " ")
        short = hint.get("short") or name[:16]
        personality = hint.get("personality") or router_personality(hostname, did)
        band = row.get("band")
        band_label = f"{band} GHz" if band else "Wi‑Fi"
        spec = {
            "id": did,
            "name": name,
            "short": short,
            "personality": personality,
            "hardware": f"Helix: {hostname} · {mac.upper()}",
            "role": f"Helix · {hostname} · {band_label}",
            "router_registry": True,
            "router_online": bool(row.get("online")),
            "router_hostname": hostname,
            "router_export": row.get("exported"),
        }
        if not row.get("online"):
            spec["stale"] = True
        by_mac[mac] = spec
        if ip:
            by_ip[ip] = spec
    return by_ip, by_mac


def load_client_labels() -> tuple[dict[str, dict], dict[str, dict]]:
    """Router registry first; known-clients.json fills gaps only."""
    by_ip, by_mac = load_router_client_labels()
    leg_ip, leg_mac = load_known_client_labels()
    for mac, spec in leg_mac.items():
        by_mac.setdefault(normalize_mac(mac), spec)
    for ip, spec in leg_ip.items():
        by_ip.setdefault(str(ip), spec)
    return by_ip, by_mac


def apply_router_registry(devices: dict[str, dict], connections: list[dict]) -> int:
    """Seed / update graph nodes from router-clients.json before ARP discovery."""
    entries = load_router_client_entries()
    if not entries:
        return 0
    helix = load_helix_hints()
    touched: set[str] = set()
    merged_rows: dict[str, list[dict]] = {}
    for row in entries:
        did = resolve_router_canonical_id(row.get("canonical_id") or row.get("hostname"))
        merged_rows.setdefault(did, []).append(row)

    for did, rows in merged_rows.items():
        online_rows = [r for r in rows if r.get("online")]
        primary = online_rows[0] if online_rows else rows[0]
        hostname = str(primary.get("hostname") or did)
        hint = helix.get(hostname, {}) if isinstance(helix.get(hostname), dict) else {}
        name = hint.get("name") or devices.get(did, {}).get("name") or hostname.replace("_", " ")
        mac = normalize_mac(primary.get("mac"))
        ip = str(primary.get("ip") or "").strip()
        router_online = any(r.get("online") for r in rows)
        personality = hint.get("personality") or router_personality(hostname, did)

        if did not in devices:
            devices[did] = {
                "name": name,
                "type": "client" if personality == "edge" else "iot",
                "role": f"Helix · {hostname}",
                "ips": [ip] if ip else [],
                "mac": mac,
                "tailscale": [],
                "hardware": f"Helix: {hostname} · {mac.upper()}",
                "services": [],
                "power_profile": "standby_capable",
                "discovered": True,
                "router_registry": True,
            }
            DEVICE_CAPACITY[did] = {
                **DEFAULT_CAPACITY,
                "short": hint.get("short") or name[:16],
                "personality": personality,
                "capacity_note": "Helix router registry",
            }
        else:
            target = devices[did]
            if ip and ip not in target.setdefault("ips", []):
                target["ips"].append(ip)
            if mac and not target.get("mac"):
                target["mac"] = mac
            target["router_registry"] = True
            if hint.get("name"):
                target["name"] = hint["name"]

        d = devices[did]
        d["router_registry"] = True
        d["router_online"] = router_online
        d["router_hostname"] = hostname
        d["router_macs"] = sorted({normalize_mac(r.get("mac")) for r in rows if r.get("mac")})
        if not router_online:
            d["stale"] = True

        has_router = any(c.get("from") == "router-gateway" and c.get("to") == did for c in connections)
        if not has_router:
            connections.append(
                {
                    "from": "router-gateway",
                    "to": did,
                    "medium": "wifi_5g" if str(primary.get("band")) == "5" else "wifi",
                    "traffic": "routing",
                    "direction": "bidirectional",
                    "note": "Helix router registry",
                }
            )
        touched.add(did)

    return len(touched)


def enrich_devices_from_router_mac(devices: dict[str, dict], arp: dict[str, str]) -> None:
    """Attach current ARP IP when MAC matches router registry, even if DHCP changed."""
    mac_to_ip = {normalize_mac(mac): ip for ip, mac in arp.items()}
    _, by_mac = load_router_client_labels()
    for mac, spec in by_mac.items():
        did = spec.get("id")
        if not did or did not in devices:
            continue
        ip = mac_to_ip.get(mac)
        if ip and ip not in devices[did].setdefault("ips", []):
            devices[did]["ips"].append(ip)
        if ip:
            devices[did]["lan_arp"] = True
            devices[did]["mac"] = mac


def report_router_validation(devices: dict[str, dict], ha_states: dict[str, dict]) -> list[str]:
    warnings: list[str] = []
    entries = load_router_client_entries()
    if not entries:
        warnings.append("router-clients.json not found — using ARP + known-clients only")
        return warnings
    by_mac, _ = load_router_client_labels()
    for row in entries:
        if not row.get("online"):
            continue
        did = resolve_router_canonical_id(row.get("canonical_id"))
        if did not in devices:
            warnings.append(f"Router online device {row.get('hostname')} ({did}) missing from graph")
    for did, d in devices.items():
        ent = d.get("ha_entity") or ""
        if not ent.startswith("device_tracker."):
            continue
        if d.get("router_registry") and not d.get("ips"):
            label = d.get("name", did)
            warnings.append(f"HA tracker {label} has no LAN IP — Companion/GPS only")
    return warnings


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
    by_ip, by_mac = load_client_labels()
    arp = parse_arp_table()
    arp = load_router_active_ips(arp)
    apply_helix_mac_hints(arp, by_ip, by_mac)
    enrich_ha_ips_from_arp(devices, arp)
    enrich_devices_from_router_mac(devices, arp)
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
        spec = by_mac.get(mac) or by_ip.get(ip)
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
            role = "Unlabeled LAN client · add to router-clients.json"
            hardware = f"MAC {mac}"
            unlabeled.append(f"{ip}  {mac}")

        if did in devices:
            devices[did].setdefault("ips", [])
            if ip not in devices[did]["ips"]:
                devices[did]["ips"].append(ip)
            devices[did]["lan_arp"] = True
            if mac and not devices[did].get("mac"):
                devices[did]["mac"] = mac
            has_router = any(
                c.get("from") == "router-gateway" and c.get("to") == did for c in connections
            )
            if not has_router:
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
        return "old-macbook"
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

    for alias, canonical in PHYSICAL_ALIASES.items():
        if alias not in devices or alias == canonical:
            continue
        if canonical not in devices:
            devices[canonical] = dict(devices[alias])
            devices[canonical].pop("_id", None)
        else:
            _merge_into_canonical(devices[canonical], devices[alias], ha_states)
        id_remap[alias] = canonical

    for old, new in id_remap.items():
        if old in devices:
            del devices[old]

    for did, d in devices.items():
        d["_id"] = did
        ent = d.get("ha_entity")
        if ent and ent in ha_states:
            attrs = ha_states[ent].get("attributes", {}) or {}
            if d.get("ha_plug"):
                display = format_plug_display_name(ent, attrs)
                d["name"] = display
                if did in DEVICE_CAPACITY:
                    DEVICE_CAPACITY[did]["short"] = display[:18]
            else:
                fn = attrs.get("friendly_name")
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
        if d.get("router_registry"):
            continue
        if d.get("stale") or did.endswith("-stale") or "stale arp" in d.get("name", "").lower():
            remove.add(did)
            continue
        if d.get("runs_on"):
            continue
        if d.get("ha_plug"):
            continue
        if not (d.get("discovered") or d.get("lan_arp") or did.startswith("arp-")):
            continue
        ips = [ip for ip in d.get("ips", []) if ip]
        if not ips:
            if d.get("ha_entity") and did in ("marshall-iphone", "wife-iphone", "family-ipad", "old-macbook"):
                continue
            remove.add(did)
            continue
        if not any(ip in active_ips for ip in ips):
            if d.get("ha_entity"):
                continue
            if d.get("stale") or did.endswith("-stale") or "stale" in d.get("name", "").lower():
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

        if d.get("ha_plug") and "homeassistant" in devices:
            add("homeassistant", did, "cloud_api", f"HA smart plug · {d.get('ha_entity', did)}")

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
        elif d.get("ha_plug") and "router-gateway" in devices:
            has_router = any(
                c.get("from") == "router-gateway" and c.get("to") == did for c in connections
            )
            if not has_router:
                add("router-gateway", did, "wifi_2g", "Smart plug · cloud IoT fallback")


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
    if device.get("ha_plug"):
        entity = device.get("ha_entity")
        if entity and entity in ha_states:
            state = ha_states[entity].get("state", "unknown")
            if state == "unavailable":
                return "offline"
            if state in ("on", "off"):
                return state
        return "unknown"

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
    *,
    ha_host: str = HOME_ASSISTANT_HOST,
) -> dict:
    conns = connections if connections is not None else CONNECTIONS
    ha_base = f"http://{ha_host}:8123"
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

    for did, d in devices.items():
        ports_cfg = d.get("probe_ports", [])
        if not ports_cfg:
            continue
        if did == "zbook-wifi":
            host_ip = zbook
        else:
            host_ip = next(
                (ip for ip in d.get("ips", []) if re.match(r"^\d+\.\d+\.\d+\.\d+$", ip)),
                None,
            )
        if not host_ip:
            continue
        for port in ports_cfg:
            if isinstance(port, tuple):
                port = port[0]
            if isinstance(port, int):
                d.setdefault("ports", {})[str(port)] = tcp_probe(host_ip, port)
        if d.get("ports"):
            d["ports_open"] = any(d["ports"].values())

    for key in ("homeassistant", "w09n-frame"):
        url = devices[key].get("probe_http")
        if url:
            http = http_probe(url)
            devices[key]["http_ok"] = http["online"]
            devices[key]["http_code"] = http["code"]
            if http["online"]:
                devices[key]["online"] = True

    for key in ("minecraft-server", "kitchen-speaker"):
        if key not in devices:
            continue
        d = devices[key]
        for spec in d.get("probe_ports", []):
            if isinstance(spec, tuple):
                port, _ = spec
            else:
                port = spec
            host = zbook if key != "kitchen-speaker" else (d.get("ips") or [None])[0]
            if not host:
                continue
            open_ = tcp_probe(host, port)
            d.setdefault("ports", {})[str(port)] = open_
            if open_:
                d["ports_open"] = True
                d["online"] = True

    for d in devices.values():
        infer = d.get("infer_from", [])
        if not infer:
            continue
        if all(devices[s].get("online") for s in infer if s in devices):
            d["online"] = True
        elif d.get("online") is None:
            d["online"] = False

    for d in devices.values():
        if d.get("online") is not None:
            continue
        ent = d.get("ha_entity") or ""
        if not ent.startswith("device_tracker.") or not ha_states:
            continue
        row = ha_states.get(ent)
        if not row:
            continue
        state = row.get("state")
        if state in ("home", "not_home", "work", "office", "away"):
            d["online"] = True

    for d in devices.values():
        if d.get("online") is not None:
            continue
        if d.get("router_registry") and d.get("router_online") is False:
            d["online"] = False

    for d in devices.values():
        if d.get("online") is not None or not d.get("ha_plug"):
            continue
        ent = d.get("ha_entity") or ""
        row = ha_states.get(ent) if ha_states else None
        if not row:
            continue
        state = row.get("state")
        if state == "unavailable":
            d["online"] = False
        elif state in ("on", "off"):
            d["online"] = True

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
            if c["to"] in ("wsl-ubuntu", "homeassistant", "minecraft-server", "minecraft-phantom"):
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
        "short": "HomeBase Mac", "personality": "edge",
        "capacity_note": "HomeBase family Mac · HA Companion",
    },
    "w09n-frame": {
        "ram_gb": 0.5, "storage_gb": 4, "compute": 0.1,
        "short": "W09N Frame", "personality": "display",
        "capacity_note": "Android 4.4 kiosk panel",
    },
    "kitchen-speaker": {
        "ram_gb": 0.256, "storage_gb": 0.5, "compute": 0.12,
        "short": "Kitchen Spk", "personality": "sensor",
        "capacity_note": "Google Home Mini · Cast + TTS",
    },
    "smart-plugs": {
        "ram_gb": 0.016, "storage_gb": 0.008, "compute": 0.03,
        "short": "Tuya Plugs", "personality": "sensor",
        "capacity_note": "MCU · 3× Wi-Fi switches",
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

PULSE_STRONG = frozenset({"active", "playing", "streaming", "on"})
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


def fetch_glances(host: str, port: int = 61208, timeout: int = 8) -> dict | None:
    base = f"http://{host}:{port}"
    for ver in (4, 3, 2):
        mem = json_get(f"{base}/api/{ver}/mem", timeout=timeout)
        cpu = json_get(f"{base}/api/{ver}/cpu", timeout=timeout)
        fs = json_get(f"{base}/api/{ver}/fs", timeout=timeout)
        quick = json_get(f"{base}/api/{ver}/quicklook", timeout=timeout)
        containers = json_get(f"{base}/api/{ver}/containers", timeout=timeout)
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


def fetch_glances_for_devices(
    devices: dict[str, dict],
    *,
    timeout: int = 8,
) -> dict[str, dict]:
    """Fetch Glances metrics for each hub in GLANCES_HOSTS when the port is open."""
    out: dict[str, dict] = {}
    for did, (host, port) in GLANCES_HOSTS.items():
        if did not in devices:
            continue
        ports = devices[did].get("ports", {})
        port_key = str(port)
        if port_key in ports:
            if not ports[port_key]:
                continue
        elif not tcp_probe(host, port):
            continue
        payload = fetch_glances(host, port=port, timeout=timeout)
        if payload:
            out[did] = payload
    return out


def apply_live_metrics(
    devices: dict[str, dict],
    glances_by_device: dict[str, dict] | None,
    local: dict | None,
) -> None:
    for d in devices.values():
        d.pop("metrics_live", None)

    if glances_by_device:
        for did, glances in glances_by_device.items():
            if did not in devices:
                continue
            host = {
                "source": f"glances:{glances['api_version']}",
                "ram_used_pct": glances["ram_used_pct"],
                "storage_used_pct": glances["storage_used_pct"],
                "cpu_load_pct": glances["cpu_load_pct"],
                "cpu_cores": glances.get("cpu_cores"),
                "cpu_name": glances.get("cpu_name"),
            }
            devices[did]["metrics_live"] = dict(host)
            if glances["storage_gb"] > 0:
                static = DEVICE_CAPACITY.get(did, {})
                if glances["storage_gb"] > static.get("storage_gb", 0) * 0.5:
                    devices[did]["metrics_live"]["storage_gb_live"] = glances["storage_gb"]

        zbook_glances = glances_by_device.get("zbook-wifi")
        if zbook_glances:
            for cname, target_did in GLANCES_CONTAINER_MAP.items():
                c = zbook_glances.get("containers", {}).get(cname)
                if c and target_did in devices:
                    devices[target_did]["metrics_live"] = {
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


def spread_plug_constellation(
    seeds: dict[str, list],
    devices: dict[str, dict],
    *,
    hub_id: str = "router-gateway",
    radius: float = 96.0,
) -> None:
    """Fan individual smart plugs into a visible sub-cluster so they do not stack."""
    plug_ids = sorted(
        did for did in devices if did.startswith("plug-") or devices[did].get("ha_plug")
    )
    if not plug_ids:
        return
    hub = seeds.get(hub_id, [0, 0, 0])
    count = len(plug_ids)
    for i, did in enumerate(plug_ids):
        angle = -math.pi / 2 + (2 * math.pi * i / max(count, 1))
        seeds[did] = [
            round(hub[0] + radius * math.cos(angle)),
            round(hub[1] + radius * 0.44 * math.sin(angle)),
            round(hub[2] + radius * 0.62 * math.cos(angle * 0.7 + 0.35)),
        ]


def dynamic_layout_seeds(devices: dict[str, dict], base: dict[str, list]) -> dict[str, list]:
    seeds = dict(base)
    nest_offsets = {
        "wsl-ubuntu": ("zbook-wifi", 52, 0.0),
        "homeassistant": ("wsl-ubuntu", 34, 1.05),
        "minecraft-server": ("wsl-ubuntu", 40, 2.35),
        "minecraft-phantom": ("wsl-ubuntu", 36, 3.55),
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
    spread_plug_constellation(seeds, devices)
    return seeds


HOMELAB_CORE_IDS = frozenset(
    {"zbook-wifi", "wsl-ubuntu", "homeassistant", "minecraft-server", "minecraft-phantom", "mac-primary"}
)
HA_NETWORK_IDS = frozenset(
    {
        "zbook-wifi",
        "homeassistant",
        "smart-plugs",
        "kitchen-speaker",
        "w09n-frame",
        "marshall-iphone",
        "wife-iphone",
        "family-ipad",
        "old-macbook",
    }
)
HA_MOBILE_IDS = frozenset({"marshall-iphone", "wife-iphone", "family-ipad", "old-macbook", "w09n-frame"})
VIRTUAL_IDS = frozenset({"wsl-ubuntu", "homeassistant", "minecraft-server", "minecraft-phantom"})
HARDWARE_IDS = frozenset(
    {
        "zbook-wifi",
        "mac-primary",
        "old-macbook",
        "macbook-air",
        "marshall-iphone",
        "wife-iphone",
        "family-ipad",
        "w09n-frame",
        "kitchen-speaker",
        "xbox-one",
        "smart-fridge",
        "lg-washer",
        "lg-dryer",
        "galaxy-tab",
    }
)
IOT_BELT_EXCLUDE = frozenset({"w09n-frame"})
IOT_BELT_PREFIXES = ("esp-", "ct-", "lg-", "qca")


def node_layer(did: str, device: dict) -> str:
    if did == "router-gateway" or device.get("type") == "network":
        return "network"
    if device.get("runs_on") or did in VIRTUAL_IDS:
        return "virtual"
    return "physical"


def node_clusters(did: str, device: dict, personality: str) -> list[str]:
    clusters: list[str] = []
    if did in HOMELAB_CORE_IDS:
        clusters.append("homelab-core")
    if did in HA_NETWORK_IDS or (device.get("ha_entity") or "").startswith("device_tracker."):
        clusters.append("ha-network")
    if did in HA_MOBILE_IDS or (device.get("ha_entity") or "").startswith("device_tracker."):
        clusters.append("ha-mobile")
    if did in HARDWARE_IDS:
        clusters.append("hardware")
    if (
        did not in IOT_BELT_EXCLUDE
        and (
            personality == "sensor"
            or device.get("type") == "iot"
            or did.startswith(IOT_BELT_PREFIXES)
            or did in ("smart-plugs", "smart-fridge", "xbox-one", "lg-washer", "lg-dryer")
            or did.startswith("plug-")
        )
    ):
        clusters.append("iot")
    if device.get("type") == "client" and personality in ("edge", "display"):
        clusters.append("personal")
    if device.get("stale") or device.get("router_online") is False or did.endswith("-stale"):
        clusters.append("stale")
    return clusters or ["other"]


def node_view_flags(did: str, device: dict, clusters: list[str]) -> dict[str, bool]:
    layer = node_layer(did, device)
    ha_ent = device.get("ha_entity") or ""
    ha_ents = device.get("ha_entities") or []
    return {
        "hardware": did in HARDWARE_IDS or "hardware" in clusters,
        "iot_belt": "iot" in clusters and did not in IOT_BELT_EXCLUDE,
        "ha_network": "ha-network" in clusters
        or did in HA_NETWORK_IDS
        or did.startswith("plug-")
        or device.get("ha_plug")
        or ha_ent.startswith("device_tracker."),
        "homelab_core": "homelab-core" in clusters,
        "is_virtual": layer == "virtual",
        "is_network": layer == "network",
    }


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
    individual_plug_ids = {
        did for did in devices if did.startswith("plug-") or devices[did].get("ha_plug")
    }
    for did, d in devices.items():
        if did == "smart-plugs" and individual_plug_ids:
            continue
        status = "online" if d.get("online") is True else "offline" if d.get("online") is False else "unknown"
        mode = d.get("mode", "unknown")
        spec = caps.get(did, DEFAULT_CAPACITY)
        cap = scores.get(did, capability_score(spec))
        ratio = cap / max_score if max_score else 0
        val = val_from_capability(cap, max_score)
        personality = spec.get("personality", "sensor")
        tier = tier_from_ratio(ratio, personality)
        if d.get("ha_plug"):
            short = d["name"]
            label = d["name"]
        else:
            short = spec.get("short") or d["name"]
            label = d["name"]
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
        layer = node_layer(did, d)
        clusters = node_clusters(did, d, personality)
        views = node_view_flags(did, d, clusters)
        nodes.append(
            {
                "id": did,
                "label": label,
                "shortName": short,
                "group": d["type"],
                "status": status,
                "mode": mode,
                "tier": tier,
                "personality": personality,
                "layer": layer,
                "cluster": clusters,
                "views": views,
                "router_online": d.get("router_online"),
                "stale_registry": bool(
                    d.get("stale") or d.get("router_online") is False or did.endswith("-stale")
                ),
                "ha_tracked": bool((d.get("ha_entity") or "").startswith("device_tracker.")),
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
        if individual_plug_ids and (c["from"] == "smart-plugs" or c["to"] == "smart-plugs"):
            continue
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
        "kitchen-speaker": [-80, 160, 80],
        "smart-plugs": [-200, -60, 100],
        "plug-1": [-180, -90, 95],
        "plug-2": [-210, -55, 105],
        "plug-3": [-240, -20, 115],
        "plug-4": [-270, 15, 125],
        "minecraft-server": [340, -100, -50],
        "minecraft-phantom": [400, -140, 0],
    }

    return {
        "generated": snapshot["generated"],
        "scanner": snapshot["scanner"],
        "scanner_device_id": scanner_device_id,
        "viewer_index": build_viewer_index(devices),
        "ha_api": snapshot["ha_api"],
        "ha_discovered": snapshot.get("ha_discovered", 0),
        "ha_plugs_discovered": snapshot.get("ha_plugs_discovered", 0),
        "plug_diagnostics": snapshot.get("plug_diagnostics", []),
        "arp_discovered": snapshot.get("arp_discovered", 0),
        "glances": snapshot.get("glances"),
        "glances_hosts": snapshot.get("glances_hosts", []),
        "medium_legend": {k: v["label"] for k, v in MEDIUM_META.items()},
        "saved_positions": load_positions(),
        "layout_seeds": dynamic_layout_seeds(devices, base_seeds),
        "nodes": nodes,
        "edges": edges,
    }


def write_html(path: Path, payload: dict) -> None:
    template_path = VAULT / "network-graph-template.html"
    template = template_path.read_text(encoding="utf-8") if template_path.exists() else "<html><body>Missing network-graph-template.html</body></html>"
    json_blob = json.dumps(payload, ensure_ascii=True).replace("</", "<\\/")
    path.write_text(template.replace("__NETWORK_DATA_JSON__", json_blob), encoding="utf-8")


def generate(
    zbook: str,
    ha_token: str | None,
    *,
    ha_host: str = HOME_ASSISTANT_HOST,
    glances_timeout: int = 8,
) -> dict:
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ha_base = f"http://{ha_host}:8123"
    ha_states = ha_fetch_states(ha_base, ha_token or "")
    connections = [dict(c) for c in CONNECTIONS]
    devices = {k: dict(v) for k, v in DEVICES.items()}
    load_extra_devices(devices, connections)
    router_seeded = apply_router_registry(devices, connections)
    arp_added, arp_unlabeled, active_arp = discover_lan_clients(devices, connections)
    ha_added = expand_ha_devices(devices, connections, ha_states)
    plugs_added, plug_diagnostics = expand_ha_smart_plugs(devices, connections, ha_states, active_arp)
    merged = consolidate_devices(devices, connections, ha_states, active_arp)
    device_links(devices, connections)
    snapshot = probe_devices(devices, zbook, ha_token, connections, ha_states, ha_host=ha_host)
    snapshot["generated"] = generated
    snapshot["ha_discovered"] = ha_added
    snapshot["ha_plugs_discovered"] = plugs_added
    snapshot["plug_diagnostics"] = plug_diagnostics
    snapshot["arp_discovered"] = arp_added
    snapshot["arp_unlabeled"] = arp_unlabeled
    snapshot["active_arp_count"] = len(active_arp)
    snapshot["devices_merged"] = len(merged)
    snapshot["router_registry"] = router_seeded
    glances_by_device = fetch_glances_for_devices(devices, timeout=glances_timeout)
    local_metrics = fetch_local_host_metrics()
    apply_live_metrics(devices, glances_by_device, local_metrics)
    snapshot["glances"] = bool(glances_by_device)
    snapshot["glances_hosts"] = sorted(glances_by_device.keys())
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
    if plugs_added:
        print(f"[+] Smart plugs: {plugs_added} individual node(s) from Home Assistant")
        for row in plug_diagnostics:
            ip_note = row.get("ip") or "no LAN IP"
            print(
                f"    · {row.get('friendly_name')} ({row.get('entity_id')}) "
                f"→ {row.get('node_id')} · {row.get('state')} · {row.get('attachment')} · {ip_note}"
            )
    elif plug_diagnostics:
        print("[!] Smart plug diagnostics: candidates found but none materialized")
        for row in plug_diagnostics:
            print(f"    · {row}")
    if arp_added:
        print(f"[+] LAN ARP: added {arp_added} client(s) from Wi‑Fi scan")
    if router_seeded:
        print(f"[+] Router registry: {router_seeded} device(s) from router-clients.json")
    if merged:
        print(f"[+] Merged {len(merged)} duplicate node(s) · active LAN: {len(active_arp)} IP(s)")
    if glances_by_device:
        for did in snapshot["glances_hosts"]:
            host, port = GLANCES_HOSTS[did]
            g = glances_by_device[did]
            print(
                f"[+] Glances {did}: {host}:{port} · "
                f"CPU {g['cpu_load_pct']}% · RAM {g['ram_used_pct']}%"
            )
    else:
        print("[!] Glances: no hosts responded (check ports 61209 ZBook, 61208 Home Base)")
    for note in report_router_validation(devices, ha_states):
        print(f"[!] {note}")
    unlabeled = snapshot.get("arp_unlabeled") or []
    if unlabeled:
        print("[i] Unlabeled LAN clients (add to router-clients.json):")
        for row in unlabeled[:12]:
            print(f"    {row}")
        if len(unlabeled) > 12:
            print(f"    … and {len(unlabeled) - 12} more")
    return snapshot


LIVE_WS_PORT_DEFAULT = 8766


def devices_for_live_registry() -> dict[str, dict]:
    devices = copy.deepcopy(DEVICES)
    connections = copy.deepcopy(CONNECTIONS)
    load_extra_devices(devices, connections)
    return devices


def build_entity_node_index(devices: dict[str, dict]) -> dict[str, str]:
    index: dict[str, str] = dict(HA_ENTITY_CANONICAL)
    for did, device in devices.items():
        entity = device.get("ha_entity")
        if entity:
            index[entity] = did
        for ent in device.get("ha_entities", []):
            index[ent] = did
    return index


def resolve_live_node_for_entity(entity_id: str, index: dict[str, str]) -> str | None:
    if entity_id in index:
        return index[entity_id]
    lowered = entity_id.lower()
    if lowered.startswith("device_tracker."):
        return index.get(entity_id) or HA_ENTITY_CANONICAL.get(entity_id)
    if "plug_" in lowered or lowered.startswith(("switch.plug", "sensor.plug")):
        match = re.search(r"plug[_\-]?(\d+)", entity_id, re.I)
        if match:
            return f"plug-{match.group(1)}"
        return "smart-plugs"
    if lowered.startswith("media_player."):
        return index.get(entity_id) or "kitchen-speaker"
    if lowered.startswith("camera."):
        return index.get(entity_id) or "zbook-wifi"
    return None


def tracker_status_from_ha_state(state: str) -> str:
    if state in ("unavailable", "unknown"):
        return "offline"
    return "online"


def tracker_mode_from_ha_state(state: str) -> str:
    if state == "home":
        return "active"
    if state == "not_home":
        return "standby"
    if state in ("unavailable", "unknown"):
        return "offline"
    return state


def extract_power_watts(state: str, attributes: dict) -> float | None:
    unit = (attributes.get("unit_of_measurement") or "").strip()
    if unit in ("W", "w", "kW"):
        try:
            watts = float(state)
            return watts * 1000.0 if unit == "kW" else watts
        except (TypeError, ValueError):
            pass
    for key in ("current_power_w", "power", "wattage", "load_power"):
        if key in attributes:
            try:
                return float(attributes[key])
            except (TypeError, ValueError):
                pass
    return None


def build_live_event_from_ha_change(
    entity_id: str,
    new_state: dict,
    devices: dict[str, dict],
    entity_index: dict[str, str],
    live_ha_states: dict[str, dict],
) -> list[dict]:
    node_id = resolve_live_node_for_entity(entity_id, entity_index)
    if not node_id or node_id not in devices:
        return []

    state_val = str(new_state.get("state", "unknown"))
    attrs = new_state.get("attributes") or {}
    if not isinstance(attrs, dict):
        attrs = {}
    live_ha_states[entity_id] = {"state": state_val, "attributes": attrs}

    device = devices[node_id]
    events: list[dict] = []

    if entity_id.startswith("device_tracker."):
        status = tracker_status_from_ha_state(state_val)
        mode = tracker_mode_from_ha_state(state_val)
        pulse = pulse_level_for_mode(mode, status)
        events.append(
            {
                "type": "node_update",
                "node_id": node_id,
                "entity_id": entity_id,
                "status": status,
                "mode": mode,
                "pulse": pulse,
                "state": state_val,
            }
        )
        return events

    if entity_id.startswith("switch."):
        mode = resolve_mode(device, live_ha_states)
        status = "online" if mode != "offline" else "offline"
        pulse = pulse_level_for_mode(mode, status)
        events.append(
            {
                "type": "node_update",
                "node_id": node_id,
                "entity_id": entity_id,
                "status": status,
                "mode": mode,
                "pulse": pulse,
                "state": state_val,
            }
        )
        if state_val == "on":
            events.append(
                {
                    "type": "link_telemetry",
                    "node_id": node_id,
                    "entity_id": entity_id,
                    "boost": 2.8,
                    "duration_ms": 2800,
                    "value": 1.0,
                }
            )
        return events

    if entity_id.startswith("media_player."):
        mode = resolve_mode(device, live_ha_states)
        status = "offline" if state_val in ("unavailable", "unknown") else "online"
        pulse = pulse_level_for_mode(mode, status)
        events.append(
            {
                "type": "node_update",
                "node_id": node_id,
                "entity_id": entity_id,
                "status": status,
                "mode": mode,
                "pulse": pulse,
                "state": state_val,
            }
        )
        if state_val == "playing":
            events.append(
                {
                    "type": "link_telemetry",
                    "node_id": node_id,
                    "entity_id": entity_id,
                    "boost": 2.2,
                    "duration_ms": 4000,
                    "value": 1.0,
                }
            )
        return events

    if entity_id.startswith("sensor."):
        watts = extract_power_watts(state_val, attrs)
        if watts is None:
            return []
        mode = resolve_mode(device, live_ha_states)
        status = "online" if device.get("online") is not False else "offline"
        pulse = "strong" if watts >= 5 else pulse_level_for_mode(mode, status)
        events.append(
            {
                "type": "node_update",
                "node_id": node_id,
                "entity_id": entity_id,
                "status": status,
                "mode": mode,
                "pulse": pulse,
                "state": state_val,
                "value": round(watts, 2),
            }
        )
        boost = min(4.5, 1.5 + watts / 40.0)
        events.append(
            {
                "type": "link_telemetry",
                "node_id": node_id,
                "entity_id": entity_id,
                "boost": round(boost, 2),
                "duration_ms": 3200,
                "value": round(watts, 2),
            }
        )
        return events

    if entity_id.startswith("camera."):
        mode = resolve_mode(device, live_ha_states)
        status = "online" if state_val not in ("unavailable", "unknown") else "offline"
        pulse = pulse_level_for_mode(mode, status)
        events.append(
            {
                "type": "node_update",
                "node_id": node_id,
                "entity_id": entity_id,
                "status": status,
                "mode": mode,
                "pulse": pulse,
                "state": state_val,
            }
        )
        if mode == "streaming":
            events.append(
                {
                    "type": "link_telemetry",
                    "node_id": node_id,
                    "entity_id": entity_id,
                    "boost": 2.0,
                    "duration_ms": 5000,
                    "value": 1.0,
                }
            )
        return events

    mode = resolve_mode(device, live_ha_states)
    status = "offline" if state_val in ("unavailable", "unknown", "off") else "online"
    pulse = pulse_level_for_mode(mode, status)
    events.append(
        {
            "type": "node_update",
            "node_id": node_id,
            "entity_id": entity_id,
            "status": status,
            "mode": mode,
            "pulse": pulse,
            "state": state_val,
        }
    )
    return events


class LiveBroadcastHub:
    def __init__(self) -> None:
        self._clients: set[Any] = set()
        self._lock = asyncio.Lock()

    async def register(self, websocket: Any) -> None:
        async with self._lock:
            self._clients.add(websocket)

    async def unregister(self, websocket: Any) -> None:
        async with self._lock:
            self._clients.discard(websocket)

    async def broadcast(self, payload: dict) -> None:
        message = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
        dead: list[Any] = []
        async with self._lock:
            clients = list(self._clients)
        for websocket in clients:
            try:
                await websocket.send(message)
            except Exception:
                dead.append(websocket)
        if dead:
            async with self._lock:
                for websocket in dead:
                    self._clients.discard(websocket)


async def _ha_state_changed_listener(
    ha_ws_url: str,
    token: str,
    hub: LiveBroadcastHub,
    devices: dict[str, dict],
    entity_index: dict[str, str],
    live_ha_states: dict[str, dict],
) -> None:
    import websockets

    backoff = 2.0
    msg_id = 1
    while True:
        try:
            async with websockets.connect(
                ha_ws_url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=5,
                max_size=2**20,
            ) as ws:
                raw = await asyncio.wait_for(ws.recv(), timeout=15)
                hello = json.loads(raw)
                if hello.get("type") != "auth_required":
                    raise RuntimeError(f"Unexpected HA hello: {hello.get('type')}")

                await ws.send(json.dumps({"type": "auth", "access_token": token}))
                auth_raw = await asyncio.wait_for(ws.recv(), timeout=15)
                auth_msg = json.loads(auth_raw)
                if auth_msg.get("type") != "auth_ok":
                    raise RuntimeError("Home Assistant WebSocket auth failed")

                msg_id += 1
                await ws.send(
                    json.dumps(
                        {
                            "id": msg_id,
                            "type": "subscribe_events",
                            "event_type": "state_changed",
                        }
                    )
                )
                sub_raw = await asyncio.wait_for(ws.recv(), timeout=15)
                sub_msg = json.loads(sub_raw)
                if not sub_msg.get("success", False):
                    raise RuntimeError(f"HA subscribe_events failed: {sub_msg}")

                print("[+] Home Assistant live event stream connected")
                backoff = 2.0

                async for raw_event in ws:
                    try:
                        envelope = json.loads(raw_event)
                    except json.JSONDecodeError:
                        continue
                    if envelope.get("type") != "event":
                        continue
                    event = envelope.get("event") or {}
                    if event.get("event_type") != "state_changed":
                        continue
                    data = event.get("data") or {}
                    entity_id = data.get("entity_id")
                    new_state = data.get("new_state") or {}
                    if not entity_id or not isinstance(new_state, dict):
                        continue
                    for live_event in build_live_event_from_ha_change(
                        entity_id,
                        new_state,
                        devices,
                        entity_index,
                        live_ha_states,
                    ):
                        await hub.broadcast(live_event)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"[i] HA WebSocket reconnect in {backoff:.0f}s: {exc}")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2.0, 60.0)


async def _live_broadcast_server(
    hub: LiveBroadcastHub,
    bind: str,
    port: int,
    on_client: Callable[[], Awaitable[None]] | None = None,
) -> None:
    import websockets

    backoff = 2.0
    while True:
        server = None
        try:

            async def client_handler(websocket: Any) -> None:
                await hub.register(websocket)
                if on_client:
                    await on_client()
                try:
                    await websocket.wait_closed()
                finally:
                    await hub.unregister(websocket)

            server = await websockets.serve(
                client_handler,
                bind,
                port,
                ping_interval=20,
                ping_timeout=20,
            )
            print(f"[+] Live event WebSocket broadcast on {bind}:{port}")
            backoff = 2.0
            await server.wait_closed()
        except asyncio.CancelledError:
            if server is not None:
                server.close()
                await server.wait_closed()
            raise
        except Exception as exc:
            print(f"[i] Live broadcast server restart in {backoff:.0f}s: {exc}")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2.0, 60.0)
        finally:
            if server is not None:
                server.close()
                await server.wait_closed()


async def _live_event_matrix_main(
    ha_host: str,
    ha_token: str,
    ws_bind: str,
    ws_port: int,
) -> None:
    devices = devices_for_live_registry()
    entity_index = build_entity_node_index(devices)
    live_ha_states: dict[str, dict] = {}
    ha_base = f"http://{ha_host}:8123"
    for entity_id, row in ha_fetch_states(ha_base, ha_token).items():
        live_ha_states[entity_id] = {
            "state": row.get("state", "unknown"),
            "attributes": row.get("attributes") or {},
        }
    hub = LiveBroadcastHub()
    ha_ws_url = f"ws://{ha_host}:8123/api/websocket"

    client_count = 0

    async def on_client_connected() -> None:
        nonlocal client_count
        client_count += 1
        if client_count == 1:
            print("[+] Dashboard live stream client connected")

    await asyncio.gather(
        _ha_state_changed_listener(ha_ws_url, ha_token, hub, devices, entity_index, live_ha_states),
        _live_broadcast_server(hub, ws_bind, ws_port, on_client_connected),
    )


def start_live_event_matrix(
    ha_host: str,
    ha_token: str | None,
    *,
    ws_bind: str = "0.0.0.0",
    ws_port: int = LIVE_WS_PORT_DEFAULT,
) -> None:
    if not ha_token:
        print("[!] Live WebSocket stream disabled — HA token required for real-time events")
        return
    try:
        import websockets  # noqa: F401
    except ImportError:
        print("[!] Live WebSocket stream disabled — install dependency: pip3 install websockets")
        return

    def run_async_loop() -> None:
        try:
            asyncio.run(_live_event_matrix_main(ha_host, ha_token, ws_bind, ws_port))
        except Exception as exc:
            print(f"[!] Live event matrix stopped: {exc}", file=sys.stderr)

    threading.Thread(
        target=run_async_loop,
        daemon=True,
        name="homelab-live-ws",
    ).start()


def serve(
    vault: Path,
    zbook: str,
    ha_token: str | None,
    interval: int,
    bind: str,
    *,
    ha_host: str = HOME_ASSISTANT_HOST,
    ws_port: int = LIVE_WS_PORT_DEFAULT,
    ws_bind: str = "0.0.0.0",
) -> None:
    viewer_state: dict = {"index": []}
    gen_lock = threading.Lock()

    def load_viewer_index() -> None:
        data_path = vault / "network-data.json"
        if not data_path.exists():
            return
        try:
            viewer_state["index"] = json.loads(data_path.read_text())["viewer_index"]
        except (json.JSONDecodeError, KeyError, OSError):
            pass

    load_viewer_index()
    cached = (vault / "network-graph.html").exists()

    def run_generate(label: str, *, glances_timeout: int = 8) -> None:
        acquired = gen_lock.acquire(blocking=False)
        if not acquired:
            print(f"[i] Scan already running — skipped {label.lower()}")
            return
        try:
            print(f"[*] {label}…")
            generate(zbook, ha_token, ha_host=ha_host, glances_timeout=glances_timeout)
            load_viewer_index()
            print(f"[+] {label} complete · {datetime.now():%H:%M:%S}")
        except Exception as exc:
            print(f"[!] {label} failed: {exc}", file=sys.stderr)
        finally:
            gen_lock.release()

    if cached:
        stamp = ""
        data_path = vault / "network-data.json"
        if data_path.exists():
            stamp = datetime.fromtimestamp(data_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[*] Serving cached map{f' from {stamp}' if stamp else ''} — refresh runs in background")
        threading.Thread(
            target=lambda: run_generate("Background refresh", glances_timeout=3),
            daemon=True,
        ).start()
    else:
        print("[*] No cached map yet — dashboard opens now; first scan runs in background (~1–2 min)")
        threading.Thread(
            target=lambda: run_generate("Initial scan", glances_timeout=3),
            daemon=True,
        ).start()

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
            run_generate("Scheduled refresh", glances_timeout=3)

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

    start_live_event_matrix(ha_host, ha_token, ws_bind=ws_bind, ws_port=ws_port)

    print(f"[*] Serving {vault} on {bind}:{port} (topology refresh every {interval}s)")
    print(f"[*] Live HA event stream WebSocket on {ws_bind}:{ws_port}")
    if bind in ("0.0.0.0", "::"):
        print("[*] LAN viewers (no Python/Obsidian needed — just a browser link):")
        for lip in local_ips:
            print(f"    http://{lip}:{port}/network-graph.html")
            print(f"    ws://{lip}:{ws_port}  (live events)")
        print(f"    Tailscale: http://<this-machine-tailscale-ip>:{port}/network-graph.html")
    print(f"[*] Local: http://127.0.0.1:{port}/network-graph.html")
    print(f"[*] Live WS: ws://127.0.0.1:{ws_port}")
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
    ap.add_argument("--zbook", default=ZBOOK_HOST, help="ZBook LAN IP (Glances :61209, RTSP)")
    ap.add_argument("--ha-host", default=HOME_ASSISTANT_HOST, help="Home Assistant host IP")
    ap.add_argument("--open", action="store_true", help="Open HTML graph in browser")
    ap.add_argument("--serve", action="store_true", help="Serve live dashboard on :8765")
    ap.add_argument("--bind", default="0.0.0.0", help="Bind address (0.0.0.0 = all LAN devices can open the link)")
    ap.add_argument("--interval", type=int, default=30, help="Topology rescan interval when serving (live WS handles instant HA events)")
    ap.add_argument("--ws-port", type=int, default=LIVE_WS_PORT_DEFAULT, help="Live event WebSocket broadcast port")
    ap.add_argument("--ws-bind", default="0.0.0.0", help="Live event WebSocket bind address")
    ap.add_argument("--watch", type=int, metavar="SEC", help="Regenerate every N seconds (no server)")
    args = ap.parse_args()

    ha_token = resolve_ha_token()

    if args.serve:
        if not ha_token:
            print("[!] HA token missing — phones/tablets will NOT appear on the map")
            print("[!] Live WebSocket event stream will NOT start without a token")
            print(f"[i] Create {VAULT / 'ha-token.local'} with your long-lived token, or:")
            print("[i]   export HOMELAB_HA_TOKEN='your-token'")
        serve(
            VAULT,
            args.zbook,
            ha_token,
            args.interval,
            args.bind,
            ha_host=args.ha_host,
            ws_port=args.ws_port,
            ws_bind=args.ws_bind,
        )
        return 0

    print("[*] Scanning LAN from this Mac...")
    if not ha_token:
        print("[!] HA token missing — phones/tablets will NOT be discovered")
        print(f"[i] Add token: {VAULT / 'ha-token.local'}  (see ha-token.local.example)")
    generate(args.zbook, ha_token, ha_host=args.ha_host)
    print(f"[+] Vault updated: {VAULT}")
    print(f"[+] Live dashboard: python3 {VAULT}/generate_network_map.py --serve")

    if args.watch:
        while True:
            time.sleep(args.watch)
            generate(args.zbook, ha_token, ha_host=args.ha_host)
            print(f"[+] Refreshed {datetime.now():%H:%M:%S}")

    if args.open:
        webbrowser.open((VAULT / "network-graph.html").as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
