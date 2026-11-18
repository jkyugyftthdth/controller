"""Keyboard emulation via SendInput. Edit SCAN to match your Forza key bindings."""
import ctypes
import threading
import time
from ctypes import wintypes

# Forza Horizon 4 default keyboard layout (scan codes): W/S/Space/R + A/D steering
SCAN = {"acc": 0x11, "brk": 0x1F, "hb": 0x39, "rw": 0x13, "left": 0x1E, "right": 0x20}
BUTTON_KEYS = ("acc", "brk", "hb", "rw")
TICK = 0.01  # steering pulse resolution (seconds)

KEYEVENTF_KEYUP, KEYEVENTF_SCANCODE = 0x0002, 0x0008


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class _U(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


def _send(scan: int, down: bool) -> None:
    flags = KEYEVENTF_SCANCODE | (0 if down else KEYEVENTF_KEYUP)
    i = INPUT(type=1)
    i.ki = KEYBDINPUT(0, scan, flags, 0, 0)
    ctypes.windll.user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INPUT))


class Keyboard:
    def __init__(self):
        if hasattr(ctypes, "windll"):
            ctypes.windll.winmm.timeBeginPeriod(1)  # 1 ms timer so pulses are accurate
        self._lock = threading.RLock()
        self.down: set[str] = set()
        self.steer = 0.0
        self._acc = 0.0
        threading.Thread(target=self._pwm, daemon=True).start()

    def _set(self, name: str, down: bool) -> None:
        if down and name not in self.down:
            _send(SCAN[name], True)
            self.down.add(name)
        elif not down and name in self.down:
            _send(SCAN[name], False)
            self.down.discard(name)

    def apply(self, s: dict) -> None:
        want = {k for k in s.get("k", []) if k in BUTTON_KEYS}
        try:
            st = max(-1.0, min(1.0, float(s.get("st", 0))))
        except (TypeError, ValueError):
            st = 0.0
        with self._lock:
            for k in BUTTON_KEYS:
                self._set(k, k in want)
            self.steer = st

    def _pwm(self) -> None:
        """Pulse A/D so the share of time pressed equals the tilt (pseudo-analog steering)."""
        while True:
            time.sleep(TICK)
            with self._lock:
                v = self.steer
                side, other = ("left", "right") if v < 0 else ("right", "left")
                a = abs(v)
                self._set(other, False)
                if a < 0.03:
                    self._acc = 0.0
                    self._set(side, False)
                elif a > 0.97:
                    self._set(side, True)
                else:
                    self._acc += a
                    if self._acc >= 1:
                        self._acc -= 1
                        self._set(side, True)
                    else:
                        self._set(side, False)

    def reset(self) -> None:
        """Release every key."""
        with self._lock:
            self.steer, self._acc = 0.0, 0.0
            for k in list(self.down):
                self._set(k, False)
