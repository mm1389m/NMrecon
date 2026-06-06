"""
NightMare Recon — modules/geo_ip.py
IP Geolocation via ip-api.com (free, no key required).
Developed by mm1389m  |  v1.0.0
"""

import socket
import json
import re
from typing import Any

import requests
from requests.exceptions import RequestException

from core.banner import print_success, print_error, print_warning, print_info
from core.config import DEFAULT_USER_AGENT
from utils.ui import print_kv_table, make_spinner

_HEADERS = {"User-Agent": DEFAULT_USER_AGENT}
_API_URL  = (
    "http://ip-api.com/json/{ip}"
    "?fields=status,message,country,countryCode,regionName,city,"
    "zip,lat,lon,timezone,isp,org,as,query"
)
_IP_RE = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$"
)


def run_geo_ip(target: str) -> dict[str, Any]:
    print_info(f"IP Geolocation  →  [bold white]{target}[/bold white]")

    ip = _resolve_ip(target)
    if not ip:
        print_error(f"Could not resolve '{target}' to an IP address.")
        return {"error": f"resolution failed: {target}"}

    if ip != target:
        print_success(f"  Resolved: {target}  →  [bold bright_green]{ip}[/bold bright_green]")

    return _query_geo(ip)


def _resolve_ip(target: str) -> str | None:
    if _IP_RE.match(target):
        return target

    old = socket.getdefaulttimeout()
    socket.setdefaulttimeout(6.0)
    try:
        info = socket.getaddrinfo(target, None, socket.AF_INET)
        if info:
            return info[0][4][0]
    except (socket.gaierror, OSError):
        pass
    finally:
        socket.setdefaulttimeout(old)
    return None


def _query_geo(ip: str) -> dict[str, Any]:
    url = _API_URL.format(ip=ip)
    try:
        with make_spinner(f"Geolocating {ip}...") as sp:
            sp.add_task("g", total=None)
            resp = requests.get(url, timeout=10, headers=_HEADERS)
        data = resp.json()
    except RequestException as exc:
        print_error(f"Geolocation API error: {exc}")
        return {"error": str(exc)}
    except (json.JSONDecodeError, ValueError):
        print_error("Geolocation API returned invalid JSON.")
        return {"error": "invalid response"}

    if data.get("status") != "success":
        msg = data.get("message", "unknown error")
        print_warning(f"Geolocation failed: {msg}")
        return {"error": msg}

    result = {
        "IP Address":   data.get("query", ip),
        "Country":      f"{data.get('country', '—')}  ({data.get('countryCode', '—')})",
        "Region":       data.get("regionName", "—"),
        "City":         data.get("city", "—"),
        "ZIP":          data.get("zip", "—"),
        "Timezone":     data.get("timezone", "—"),
        "Coordinates":  f"{data.get('lat', '—')}, {data.get('lon', '—')}",
        "ISP":          data.get("isp", "—"),
        "Organization": data.get("org", "—"),
        "AS Number":    data.get("as", "—"),
    }

    print_kv_table(f"Geolocation — {ip}", result)
    print_success("Geolocation complete.")
    return result
