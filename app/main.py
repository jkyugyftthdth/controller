"""Forza Controller - starts the server and shows connection QR code + PIN."""
import atexit
import tkinter as tk
from tkinter import ttk

import qrcode
from PIL import ImageTk

from app import config, tls
from app.keyboard import Keyboard
from app.server import Server


class App:
    def __init__(self, root: tk.Tk, settings: dict, server: Server):
        self.root, self.s, self.srv = root, settings, server
        self.ips: list[str] = []
        self.n = 0
        root.title("Forza Controller")
        root.resizable(False, False)
        f = ttk.Frame(root, padding=16)
        f.grid()
        self.status = ttk.Label(f, font=("Segoe UI", 12, "bold"))
        self.status.grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(f, text="Network").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.combo = ttk.Combobox(f, state="readonly", width=34)
        self.combo.grid(row=2, column=0, sticky="we")
        self.combo.bind("<<ComboboxSelected>>", lambda e: self.render())
        ttk.Button(f, text="Rescan", command=self.scan).grid(row=2, column=1, padx=(6, 0))
        self.qr = tk.Label(f)
        self.qr.grid(row=3, column=0, columnspan=2, pady=10)
        self.url = ttk.Label(f, font=("Consolas", 10))
        self.url.grid(row=4, column=0, columnspan=2)
        self.pin = ttk.Label(f, font=("Consolas", 22, "bold"))
        self.pin.grid(row=5, column=0, sticky="w", pady=(8, 0))
        ttk.Button(f, text="New PIN", command=self.new_pin).grid(row=5, column=1, padx=(6, 0))
        ttk.Label(f, text="Scan the QR code with your phone camera.",
                  foreground="#666").grid(row=6, column=0, columnspan=2, pady=(10, 0))
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.scan()
        self.tick()

    def scan(self) -> None:
        ips = config.local_ips()
        if ips == self.ips:
            return
        cur = self.combo.get()
        self.ips = ips
        vals = [f"{ip}  ({config.ip_label(ip)})" for ip in ips]
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
            self.url.config(text="No network - join Wi-Fi or turn on Mobile Hotspot")
            self.qr.config(image="")
            return
        ip = self.combo.get().split()[0]
        url = f"https://{ip}:{self.s['port']}/?pin={self.s['pin']}"
        self.url.config(text=f"https://{ip}:{self.s['port']}")
        q = qrcode.QRCode(border=2, box_size=5)
        q.add_data(url)
        q.make(fit=True)
        self._img = ImageTk.PhotoImage(q.make_image(fill_color="black", back_color="white").convert("RGB"))
        self.qr.config(image=self._img)

    def new_pin(self) -> None:
        self.s["pin"] = self.srv.pin = config.new_pin()
        config.save_settings(self.s)
        self.render()

    def tick(self) -> None:
        if self.srv.error:
            self.status.config(text=self.srv.error, foreground="#c0392b")
        elif self.srv.connected:
            ms = self.srv.latency
            self.status.config(text=f"Phone connected" + (f" - {ms} ms" if ms is not None else ""),
                               foreground="#1e8449")
        else:
            self.status.config(text="Waiting for phone...", foreground="#555")
        self.n += 1
        if self.n % 17 == 0:  # rescan ~every 5 s (hotspot may start later)
            self.scan()
        self.root.after(300, self.tick)

    def close(self) -> None:
        self.srv.stop()
        self.root.destroy()


def main() -> None:
    settings = config.load_settings()
    keys = Keyboard()
    atexit.register(keys.reset)
    server = Server(settings["pin"], settings["port"], keys, tls.context(config.local_ips()))
    server.start()
    root = tk.Tk()
    App(root, settings, server)
    root.mainloop()


if __name__ == "__main__":
    main()
