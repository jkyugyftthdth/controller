"""Forza Controller - starts the server and shows connection QR code + PIN."""
import atexit
import threading
import tkinter as tk
from tkinter import ttk

import qrcode
from PIL import ImageTk

from app import config, tls
from app.keyboard import Keyboard
from app.server import Server


BG, PANEL, LINE, TXT, MUTED, BLUE, GREEN, RED = "#050a1f", "#0f1d4d", "#25356b", "#eaf1ff", "#8fa3d4", "#2f7bff", "#35e0a1", "#ff5d73"


class App:
    """PS5-style navy window: connection QR, PIN, and which network the phone should join."""

    def __init__(self, root: tk.Tk, settings: dict, server: Server):
        self.root, self.s, self.srv = root, settings, server
        self.nets: list[tuple[str, str]] = []
        self.n = 0
        self._dirty = False
        root.title("Forza Controller")
        root.configure(bg=BG)
        root.resizable(False, False)
        st = ttk.Style(root)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure("TCombobox", fieldbackground=PANEL, background=PANEL, foreground=TXT, arrowcolor=TXT,
                     bordercolor=LINE, lightcolor=PANEL, darkcolor=PANEL, padding=6)
        st.map("TCombobox", fieldbackground=[("readonly", PANEL)], foreground=[("readonly", TXT)],
               selectbackground=[("readonly", PANEL)], selectforeground=[("readonly", TXT)])
        root.option_add("*TCombobox*Listbox.background", PANEL)
        root.option_add("*TCombobox*Listbox.foreground", TXT)
        root.option_add("*TCombobox*Listbox.selectBackground", BLUE)

        f = tk.Frame(root, bg=BG, padx=22, pady=18)
        f.grid()
        tk.Label(f, text="FORZA CONTROLLER", bg=BG, fg=TXT, font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        tk.Frame(f, bg=BLUE, height=3).grid(row=1, column=0, columnspan=2, sticky="we", pady=(4, 10))
        self.status = tk.Label(f, bg=BG, font=("Segoe UI", 12, "bold"), anchor="w")
        self.status.grid(row=2, column=0, columnspan=2, sticky="w")
        self.mode = tk.Label(f, bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w",
                             text="Mode: " + getattr(server.pad, "name", "Keyboard keys"))
        self.mode.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Label(f, text="Connect the phone over", bg=BG, fg=MUTED, font=("Segoe UI", 9)).grid(row=4, column=0, sticky="w")
        self.combo = ttk.Combobox(f, state="readonly", width=40, font=("Segoe UI", 10))
        self.combo.grid(row=5, column=0, sticky="we")
        self.combo.bind("<<ComboboxSelected>>", lambda e: self.render())
        self._btn(f, "Rescan", self.rescan).grid(row=5, column=1, padx=(8, 0))

        card = tk.Frame(f, bg=PANEL, highlightbackground=LINE, highlightthickness=1)
        card.grid(row=6, column=0, columnspan=2, pady=12, sticky="we")
        self.qr = tk.Label(card, bg="white", bd=8, relief="flat")
        self.qr.pack(pady=14)
        self.url = tk.Label(card, bg=PANEL, fg=TXT, font=("Consolas", 10))
        self.url.pack(pady=(0, 4))
        self.appline = tk.Label(card, bg=PANEL, fg=MUTED, font=("Segoe UI", 9))
        self.appline.pack(pady=(0, 12))

        self.pin = tk.Label(f, bg=BG, fg=TXT, font=("Consolas", 24, "bold"))
        self.pin.grid(row=7, column=0, sticky="w")
        self._btn(f, "New PIN", self.new_pin).grid(row=7, column=1, padx=(8, 0))
        tk.Label(f, justify="left", anchor="w", bg=BG, fg=MUTED, font=("Segoe UI", 9), wraplength=420,
                 text="Scan the QR code with the phone camera.\n"
                      "Works over Wi-Fi, this PC's Mobile Hotspot, Ethernet, Bluetooth tethering and USB tethering.\n"
                      "Bluetooth: pair the phone, turn on Bluetooth tethering on the phone, then pick it above."
                 ).grid(row=8, column=0, columnspan=2, sticky="w", pady=(12, 0))
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.scan()
        self.tick()

    @staticmethod
    def _btn(parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd, bg=BLUE, fg="white", activebackground="#1c54c9",
                         activeforeground="white", relief="flat", bd=0, padx=14, pady=6, font=("Segoe UI", 10, "bold"),
                         cursor="hand2")

    def rescan(self) -> None:
        threading.Thread(target=self._bg_refresh, daemon=True).start()

    def _bg_refresh(self) -> None:
        config.refresh_adapters()   # asks Windows which adapter owns each address (can take a second)
        self._dirty = True          # the Tk thread picks this up in tick()

    def scan(self, force: bool = False) -> None:
        nets = config.networks()
        if nets == self.nets and not force:
            return
        cur = self.combo.get()
        self.nets = nets
        vals = [f"{ip}   -   {label}" for ip, label in nets]
        self.combo["values"] = vals
        if cur in vals:
            self.combo.set(cur)
        elif vals:
            self.combo.current(0)
        else:
            self.combo.set("")
        self.render()

    def render(self) -> None:
        self.pin.config(text=f"PIN {self.s['pin']}")
        if not self.combo.get():
            self.url.config(text="No network - join Wi-Fi, plug in Ethernet or turn on Mobile Hotspot")
            self.qr.config(image="")
            self.appline.config(text="")
            return
        ip = self.combo.get().split()[0]
        url = f"https://{ip}:{self.s['port']}/?pin={self.s['pin']}"
        self.url.config(text=f"https://{ip}:{self.s['port']}")
        self.appline.config(text=f"Android app:  address {ip}   PIN {self.s['pin']}")
        q = qrcode.QRCode(border=1, box_size=5)
        q.add_data(url)
        q.make(fit=True)
        self._img = ImageTk.PhotoImage(q.make_image(fill_color="#050a1f", back_color="white").convert("RGB"))
        self.qr.config(image=self._img)

    def new_pin(self) -> None:
        self.s["pin"] = self.srv.pin = config.new_pin()
        config.save_settings(self.s)
        self.render()

    def tick(self) -> None:
        if self.srv.error:
            self.status.config(text=self.srv.error, fg=RED)
        elif self.srv.connected:
            ms = self.srv.latency
            self.status.config(text="Phone connected" + (f" - {ms} ms" if ms is not None else ""), fg=GREEN)
        else:
            self.status.config(text="Waiting for phone...", fg=MUTED)
        self.n += 1
        if self._dirty:
            self._dirty = False
            self.scan(force=True)
        if self.n % 17 == 0:  # rescan ~every 5 s (a hotspot or tether may start later)
            self.scan()
        if self.n % 100 == 0:  # refresh adapter names every ~30 s
            self.rescan()
        self.root.after(300, self.tick)

    def close(self) -> None:
        self.srv.stop()
        self.root.destroy()


def main() -> None:
    settings = config.load_settings()
    try:  # preferred: virtual Xbox controller (needs ViGEmBus driver); fallback: keyboard keys
        from app.gamepad import Gamepad
        keys = Gamepad()
    except Exception:
        keys = Keyboard()
        keys.name = "Keyboard keys (install ViGEmBus for controller mode)"
    atexit.register(keys.reset)
    config.refresh_adapters()   # find Bluetooth / USB / Ethernet links before the certificate is made
    server = Server(settings["pin"], settings["port"], keys, tls.context(config.local_ips()))
    server.start()
    root = tk.Tk()
    App(root, settings, server)
    root.mainloop()


if __name__ == "__main__":
    main()
