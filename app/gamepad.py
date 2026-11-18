"""Virtual Xbox 360 controller via ViGEmBus (vgamepad). Same interface as Keyboard."""
import threading

import vgamepad as vg

B = vg.XUSB_BUTTON
# Forza default gamepad layout: RT accelerate, LT brake/reverse, A handbrake, Y rewind, left stick steer
BUTTONS = {"hb": B.XUSB_GAMEPAD_A, "rw": B.XUSB_GAMEPAD_Y}


class Gamepad:
    name = "Virtual Xbox controller"

    def __init__(self):
        self.pad = vg.VX360Gamepad()  # raises if the ViGEmBus driver is not installed
        self._lock = threading.RLock()
        self.reset()

    def apply(self, s: dict) -> None:
        keys = set(s.get("k", []))
        try:
            st = max(-1.0, min(1.0, float(s.get("st", 0))))
        except (TypeError, ValueError):
            st = 0.0
        with self._lock:
            self.pad.left_joystick_float(x_value_float=st, y_value_float=0.0)
            self.pad.right_trigger_float(value_float=1.0 if "acc" in keys else 0.0)
            self.pad.left_trigger_float(value_float=1.0 if "brk" in keys else 0.0)
            for k, btn in BUTTONS.items():
                (self.pad.press_button if k in keys else self.pad.release_button)(button=btn)
            self.pad.update()

    def reset(self) -> None:
        with self._lock:
            self.pad.reset()
            self.pad.update()
