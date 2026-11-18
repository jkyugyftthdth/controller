"""Local web server: serves the phone UI and receives controls over WebSocket."""
import asyncio
import hmac
import json
import threading
import time

from aiohttp import WSMsgType, web

from app.config import resource_path

MAX_FAILS, LOCK_SECONDS, STALE_SECONDS = 5, 60, 1.0


class Server:
    def __init__(self, pin: str, port: int, pad, ssl_context=None):
        self.pin, self.port, self.pad, self.ssl = pin, port, pad, ssl_context
        self.connected = False
        self.latency = None
        self.error = None
        self._client = None
        self._last = 0.0
        self._fails: dict[str, list] = {}
        self._loop = None

    # lifecycle -------------------------------------------------------------
    def start(self) -> None:
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self) -> None:
        self.pad.reset()
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            runner = web.AppRunner(self._app())
            self._loop.run_until_complete(runner.setup())
            self._loop.run_until_complete(web.TCPSite(runner, "0.0.0.0", self.port, ssl_context=self.ssl).start())
        except OSError as e:
            self.error = f"Port {self.port} unavailable: {e}"
            return
        self._loop.create_task(self._watchdog())
        self._loop.run_forever()

    def _app(self) -> web.Application:
        web_dir = resource_path("web")
        app = web.Application()
        app.router.add_get("/", lambda r: web.FileResponse(web_dir / "index.html"))
        app.router.add_get("/ws", self._ws)
        app.router.add_static("/static", web_dir)
        return app

    # safety: if the phone goes silent (screen off, Wi-Fi drop) release everything
    async def _watchdog(self) -> None:
        while True:
            await asyncio.sleep(0.25)
            if self._client is not None and time.monotonic() - self._last > STALE_SECONDS:
                self.pad.reset()

    async def _ws(self, req: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse(heartbeat=5, max_msg_size=4096)
        await ws.prepare(req)
        fail = self._fails.setdefault(req.remote, [0, 0.0])
        authed = False
        try:
            async for m in ws:
                if m.type != WSMsgType.TEXT:
                    continue
                try:
                    d = json.loads(m.data)
                except ValueError:
                    continue
                if not authed:
                    if time.time() < fail[1]:
                        await ws.send_json({"t": "err", "m": f"Too many attempts. Wait {LOCK_SECONDS}s."})
                        break
                    good = d.get("t") == "auth" and hmac.compare_digest(
                        str(d.get("pin", "")).encode(), self.pin.encode())
                    if not good:
                        fail[0] += 1
                        if fail[0] >= MAX_FAILS:
                            fail[0], fail[1] = 0, time.time() + LOCK_SECONDS
                        await ws.send_json({"t": "err", "m": "Wrong PIN"})
                        break
                    fail[0] = 0
                    old, self._client, authed = self._client, ws, True
                    if old is not None and not old.closed:
                        await old.close()  # only one phone controls the game
                    self._last, self.connected = time.monotonic(), True
                    await ws.send_json({"t": "ok"})
                    continue
                self._last = time.monotonic()
                t = d.get("t")
                if t == "s":
                    self.pad.apply(d)
                elif t == "p":
                    self.latency = d.get("l")
                    await ws.send_json({"t": "q", "c": d.get("c")})
        finally:
            if self._client is ws:  # disconnect protection
                self._client, self.connected, self.latency = None, False, None
                self.pad.reset()
        return ws
