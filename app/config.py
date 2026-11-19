"""Settings, paths and network helpers."""
import json
import os
import secrets
import socket
import subprocess
import sys
from pathlib import Path

APP_NAME = "ForzaController"
DEFAULT_PORT = 8443


def resource_path(rel: str) -> Path:
    """Works from source and from a PyInstaller bundle."""
    base = getattr(sys, "_MEIPASS", None) or Path(__file__).resolve().parent.parent
    return Path(base) / rel


def data_dir() -> Path:
    """Portable: settings live next to the EXE. Source runs / read-only folders use %APPDATA%."""
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "ForzaController_data")
    candidates.append(Path(os.environ.get("APPDATA", Path.home())) / APP_NAME)
    for d in candidates:
        try:
            d.mkdir(parents=True, exist_ok=True)
            (d / ".w").write_text("")
            return d
        except OSError:
            continue
    raise OSError("No writable settings folder")


def _settings_file() -> Path:
    return data_dir() / "settings.json"


def new_pin() -> str:
    return f"{secrets.randbelow(10**6):06d}"


def save_settings(s: dict) -> None:
    _settings_file().write_text(json.dumps(s))


def load_settings() -> dict:
    try:
        s = json.loads(_settings_file().read_text())
    except (OSError, ValueError):
        s = {}
    s.setdefault("port", DEFAULT_PORT)
    if not str(s.get("pin", "")).isdigit():
        s["pin"] = new_pin()
    save_settings(s)
    return s


# ---- network discovery: Wi-Fi, Mobile hotspot, Ethernet, Bluetooth tethering, USB tethering ----------
_ADAPTERS: dict[str, tuple[str, str]] = {}   # ip -> (adapter name, adapter description), filled from Windows
_PS = ("Get-NetIPAddress -AddressFamily IPv4 | ForEach-Object { "
       "$a = Get-NetAdapter -InterfaceIndex $_.InterfaceIndex -ErrorAction SilentlyContinue; "
       "[pscustomobject]@{ip=$_.IPAddress;name=$_.InterfaceAlias;desc=$a.InterfaceDescription} } | ConvertTo-Json -Compress")


def _private(ip: str) -> bool:
    return not ip.startswith(("127.", "169.254.", "0."))


def refresh_adapters() -> None:
    """Ask Windows which adapter owns each IPv4 address (names like 'Bluetooth Network Connection')."""
    if os.name != "nt":
        return
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS],
                             capture_output=True, text=True, timeout=12, creationflags=0x08000000).stdout
        data = json.loads(out)
    except (OSError, ValueError, subprocess.SubprocessError):
        return
    if isinstance(data, dict):
        data = [data]
    found = {d["ip"]: (str(d.get("name") or ""), str(d.get("desc") or "")) for d in data if d.get("ip")}
    _ADAPTERS.clear()
    _ADAPTERS.update(found)


def classify(ip: str, name: str = "", desc: str = "") -> str:
    """Human label for the kind of link an address is on."""
    t = f"{name} {desc}".lower()
    if any(x in t for x in ("vmware", "virtualbox", "hyper-v", "vethernet", "wsl", "docker", "loopback", "tap-", "vpn", "tailscale", "zerotier")):
        return "Virtual adapter"
    if "bluetooth" in t:
        return "Bluetooth tethering"
    if ip.startswith("192.168.137."):
        return "Mobile hotspot (this PC)"
    if any(x in t for x in ("rndis", "remote ndis", "android", "iphone", "apple mobile")):
        return "USB tethering"
    if any(x in t for x in ("wi-fi", "wifi", "wireless", "wlan", "802.11")):
        return "Wi-Fi"
    if "ethernet" in t or "lan" in t:
        return "Ethernet"
    if not t.strip():   # no adapter info (non-Windows or PowerShell blocked): guess from well-known tether ranges
        if ip.startswith("192.168.44."):
            return "Bluetooth tethering"
        if ip.startswith("192.168.42.") or ip.startswith("192.168.43."):
            return "USB / phone hotspot"
        if ip.startswith("172.20.10."):
            return "iPhone hotspot"
    return "Network"


_ORDER = ["Mobile hotspot (this PC)", "Wi-Fi", "Ethernet", "USB tethering", "USB / phone hotspot", "iPhone hotspot",
          "Bluetooth tethering", "Network", "Virtual adapter"]


def _socket_ips() -> set[str]:
    ips = set()
    try:  # default-route address; no packet is actually sent
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    return ips


def local_ips() -> list[str]:
    """IPv4 addresses of this PC on any link: router LAN, hotspot, Ethernet, Bluetooth or USB tethering."""
    return sorted(i for i in (_socket_ips() | set(_ADAPTERS)) if _private(i))


def networks() -> list[tuple[str, str]]:
    """[(ip, label)] best link first. Real adapters before virtual ones."""
    out = [(ip, classify(ip, *_ADAPTERS.get(ip, ("", "")))) for ip in local_ips()]
    out.sort(key=lambda x: (_ORDER.index(x[1]) if x[1] in _ORDER else 99, x[0]))
    return out


def ip_label(ip: str) -> str:
    return classify(ip, *_ADAPTERS.get(ip, ("", "")))
