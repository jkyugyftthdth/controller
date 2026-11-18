"""Settings, paths and network helpers."""
import json
import os
import secrets
import socket
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


def local_ips() -> list[str]:
    """Private IPv4 addresses of this PC (router LAN and/or Windows hotspot)."""
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
    return sorted(i for i in ips if not i.startswith(("127.", "169.254.", "0.")))


def ip_label(ip: str) -> str:
    return "Mobile hotspot" if ip.startswith("192.168.137.") else "Wi-Fi / LAN"

