"""Virtual Xbox 360 controller via ViGEmBus (vgamepad). Same interface as Keyboard."""
import threading

import vgamepad as vg

B = vg.XUSB_BUTTON
# Phone key -> Xbox button. Triggers (acc = RT, brk = LT) and the sticks are analog and handled in apply().
BUTTONS = {
    "a": B.XUSB_GAMEPAD_A, "b": B.XUSB_GAMEPAD_B, "x": B.XUSB_GAMEPAD_X, "y": B.XUSB_GAMEPAD_Y,
    "lb": B.XUSB_GAMEPAD_LEFT_SHOULDER, "rb": B.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "up": B.XUSB_GAMEPAD_DPAD_UP, "down": B.XUSB_GAMEPAD_DPAD_DOWN,
    "left": B.XUSB_GAMEPAD_DPAD_LEFT, "right": B.XUSB_GAMEPAD_DPAD_RIGHT,
    "start": B.XUSB_GAMEPAD_START, "back": B.XUSB_GAMEPAD_BACK,
    # old names, kept so an older cached phone page still works
    "hb": B.XUSB_GAMEPAD_A, "rw": B.XUSB_GAMEPAD_Y, "nt": B.XUSB_GAMEPAD_X,
}


def _num(v, default=0.0) -> float:
    try:
        return max(-1.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return default


def _axes(v):
    """[x, y] from the phone -> two floats in -1..1 (y positive = up)."""
    if isinstance(v, (list, tuple)) and len(v) == 2:
        return _num(v[0]), _num(v[1])
    return 0.0, 0.0


class Gamepad:
    name = "Virtual Xbox controller"

    def __init__(self):
        self.pad = vg.VX360Gamepad()  # raises if the ViGEmBus driver is not installed
        self._lock = threading.RLock()
        self.reset()

    def apply(self, s: dict) -> None:
        keys = {k for k in s.get("k", []) if isinstance(k, str)}
        tilt = _num(s.get("st", 0))
        lx, ly = _axes(s.get("ls"))
        rx, ry = _axes(s.get("rs"))
        if abs(lx) < 0.02:      # tilt steers unless the on-screen left stick is being used
            lx = tilt
        down = {BUTTONS[k] for k in keys if k in BUTTONS}
        with self._lock:
            self.pad.left_joystick_float(x_value_float=lx, y_value_float=ly)
            self.pad.right_joystick_float(x_value_float=rx, y_value_float=ry)
            self.pad.right_trigger_float(value_float=1.0 if "acc" in keys else 0.0)
            self.pad.left_trigger_float(value_float=1.0 if "brk" in keys else 0.0)
            for btn in set(BUTTONS.values()):
                (self.pad.press_button if btn in down else self.pad.release_button)(button=btn)
            self.pad.update()

    def reset(self) -> None:
        with self._lock:
            self.pad.reset()
            self.pad.update()
