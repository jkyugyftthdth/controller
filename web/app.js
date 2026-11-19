"use strict";
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const cap = (el, id) => { try { el.setPointerCapture(id); } catch (e) {} };
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const load = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };
const store = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };

// ---- saved settings -------------------------------------------------------------
const cfg = { layout: "car", mode: "gyro", range: 40, dz: 3, steer: 1, invert: false, haptics: true };
try { Object.assign(cfg, JSON.parse(load("fc2.cfg"))); } catch (e) {}
const save = () => store("fc2.cfg", JSON.stringify(cfg));

// ---- state -----------------------------------------------------------------------------
const S = { st: 0, k: new Set(), ls: [0, 0], rs: [0, 0] };
const held = {};   // key -> number of fingers holding a button that sends it
let ws = null, ok = false, bad = false, pend = false, rtt = null, pin = "", timer = null, retry = null, lastSent = "";
const curve = (v, s) => Math.sign(v) * Math.pow(Math.abs(v), 1 / s);
const eff = () => Math.abs(S.ls[0]) > 0.02 ? S.ls[0] : S.st;   // left on-screen stick overrides tilt
const steer = v => { const d = cfg.dz / 100, a = Math.abs(v); return a < d ? 0 : curve(clamp((a - d) / (1 - d), 0, 1) * Math.sign(v), cfg.steer); };
const buzz = n => { if (cfg.haptics && navigator.vibrate) navigator.vibrate(n); };

function ui() {
  const v = eff();
  $("#sbi").style.left = 50 + v * 50 + "%";
  $("#wheel svg").style.transform = `rotate(${v * 90}deg)`;
}
function mark() { if (!pend) { pend = true; requestAnimationFrame(flush); } }
function flush() {   // send only when something changed (battery friendly)
  pend = false;
  if (!ok || !ws || ws.readyState !== 1) return;
  const r2 = v => Math.round(v * 100) / 100;
  const m = JSON.stringify({ t: "s", st: r2(S.st), k: [...S.k], ls: S.ls.map(r2), rs: S.rs.map(r2) });
  if (m !== lastSent) { lastSent = m; ws.send(m); }
}

// ---- hold buttons: hold on phone = key held on PC ------------------------------------
$$(".hold").forEach(el => {
  const k = el.dataset.k; let on = false;
  const set = v => {
    if (v === on) return; on = v;
    held[k] = (held[k] || 0) + (v ? 1 : -1);
    held[k] > 0 ? S.k.add(k) : S.k.delete(k);
    el.classList.toggle("on", v); mark();
  };
  el._release = () => set(false);
  el.addEventListener("pointerdown", e => { e.preventDefault(); cap(el, e.pointerId); set(true); buzz(12); });
  el.addEventListener("pointerup", () => set(false)); el.addEventListener("pointercancel", () => set(false));
  el.addEventListener("lostpointercapture", () => set(false));
});

// ---- on-screen thumb sticks (left = steer + Y axis, right = camera) ------------------
function stick(el, key) {
  const knob = el.querySelector("i"); let id = null;
  const move = e => {
    const r = el.getBoundingClientRect(), R = r.width / 2;
    let dx = (e.clientX - r.left - R) / R, dy = (e.clientY - r.top - R) / R;
    const m = Math.hypot(dx, dy); if (m > 1) { dx /= m; dy /= m; }
    S[key] = [dx, -dy];   // screen-down is negative on an Xbox stick
    knob.style.transform = `translate(${dx * R * 0.5}px,${dy * R * 0.5}px)`; ui(); mark();
  };
  const end = e => {
    if (e && e.pointerId !== id) return;
    id = null; S[key] = [0, 0]; knob.style.transform = ""; el.classList.remove("on"); ui(); mark();
  };
  el._release = () => end();
  el.addEventListener("pointerdown", e => { if (id !== null) return; e.preventDefault(); id = e.pointerId; cap(el, id); el.classList.add("on"); buzz(8); move(e); });
  el.addEventListener("pointermove", e => { if (e.pointerId === id) move(e); });
  el.addEventListener("pointerup", end); el.addEventListener("pointercancel", end);
}
stick($("#ls"), "ls"); stick($("#rs"), "rs");

// ---- gyro steering ----------------------------------------------------------------------------
let ang = 0, off = 0, lastMotion = 0;
addEventListener("devicemotion", e => {
  const a = e.accelerationIncludingGravity;
  if (!a || a.x == null || a.y == null) return;
  lastMotion = performance.now();
  const o = (screen.orientation && screen.orientation.angle) || 90;
  let d = (o === 270 ? Math.atan2(-a.y, -a.x) : Math.atan2(a.y, a.x)) * 180 / Math.PI;   // wheel rotation in landscape
  if (cfg.invert) d = -d;
  ang = ang * .7 + d * .3;
  if (cfg.layout === "car" && cfg.mode === "gyro") { S.st = steer(clamp((ang - off) / cfg.range, -1, 1)); ui(); mark(); }
});
const calibrate = () => { off = ang; buzz(30); };
$("#cal").onclick = calibrate;

// ---- touch-strip steering (fallback if gyro unavailable) ---------------------------------
const Z = $("#zone"); let zid = null;
const zset = e => { const r = Z.getBoundingClientRect(); S.st = steer(clamp(((e.clientX - r.left) / r.width - .5) * 2, -1, 1)); ui(); mark(); };
Z.onpointerdown = e => { if (cfg.layout !== "car" || cfg.mode !== "touch" || e.target.closest("button")) return; zid = e.pointerId; cap(Z, zid); zset(e); };
Z.onpointermove = e => { if (e.pointerId === zid) zset(e); };
Z.onpointerup = Z.onpointercancel = e => { if (e.pointerId === zid) { zid = null; S.st = 0; ui(); mark(); } };

function hint() {
  $("#hint").textContent = cfg.mode === "gyro" ? "Tilt the phone like a steering wheel" : "Slide your finger left / right to steer";
  S.st = 0; ui(); mark();
}

// ---- safety: release everything ------------------------------------------------------------------
function releaseAll() {
  S.st = 0; S.k.clear(); S.ls = [0, 0]; S.rs = [0, 0];
  $$(".hold").forEach(b => { b.classList.remove("on"); if (b._release) b._release(); });
  $$(".stick").forEach(b => { b.classList.remove("on"); b.querySelector("i").style.transform = ""; });
  ui(); mark();
}
document.addEventListener("visibilitychange", () => { if (document.hidden) releaseAll(); });
addEventListener("pagehide", releaseAll); addEventListener("blur", releaseAll);
addEventListener("contextmenu", e => e.preventDefault());

// ---- connection -----------------------------------------------------------------------------------------
const setOn = v => $("#dot").classList.toggle("on", v);
const ping = () => { if (ws && ws.readyState === 1) ws.send(JSON.stringify({ t: "p", c: performance.now(), l: rtt })); };   // heartbeat
function connect() {
  clearTimeout(retry); bad = false;
  if (ws) { ws.onclose = null; try { ws.close(); } catch (e) {} }
  ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
  ws.onopen = () => ws.send(JSON.stringify({ t: "auth", pin }));
  ws.onmessage = e => {
    const d = JSON.parse(e.data);
    if (d.t === "ok") {
      ok = true; lastSent = ""; setOn(true); $("#start").classList.add("hide"); store("fc.pin", pin);
      clearInterval(timer); timer = setInterval(ping, 250); buzz([20, 40, 20]);
      setTimeout(calibrate, 700);
      setTimeout(() => { if (cfg.layout === "car" && cfg.mode === "gyro" && performance.now() - lastMotion > 2000) $("#hint").textContent = "No motion sensor data - switch to Touch strip in Settings"; }, 2500);
    } else if (d.t === "err") { bad = true; $("#msg").textContent = d.m; $("#start").classList.remove("hide"); }
    else if (d.t === "q") { rtt = Math.round(performance.now() - d.c); $("#ms").textContent = rtt; }
  };
  ws.onclose = () => { ok = false; clearInterval(timer); setOn(false); $("#ms").textContent = "--"; releaseAll(); if (!bad) retry = setTimeout(connect, 1000); };
}
function fullscreen() {
  const d = document.documentElement;
  Promise.resolve(d.requestFullscreen && d.requestFullscreen()).then(() => screen.orientation && screen.orientation.lock("landscape")).catch(() => {});
}
$("#go").onclick = () => {
  pin = $("#pin").value.trim();
  if (!/^\d{6}$/.test(pin)) { $("#msg").textContent = "Enter the 6-digit PIN shown on your PC"; return; }
  $("#msg").textContent = "";
  if (window.DeviceMotionEvent && DeviceMotionEvent.requestPermission) DeviceMotionEvent.requestPermission().catch(() => {});
  fullscreen(); connect();
};
$("#disc").onclick = () => { bad = true; if (ws) ws.close(); $("#cfg").classList.add("hide"); $("#start").classList.remove("hide"); };

// ---- settings UI ------------------------------------------------------------------------------------------------
$("#info").onclick = () => alert("Two layouts (saved): CAR and PAD.\nCAR: tilt steers, BRAKE=LT, ACCELERATE=RT, cross=HANDBRAKE, square=NITROS, triangle=REWIND.\nPAD: normal dual-stick gamepad with L1/L2/R1/R2, L3/R3, D-pad, Create/PS/Options.\nPS symbols map to Xbox: cross=A, circle=B, square=X, triangle=Y."); $("#gear").onclick = () => $("#cfg").classList.remove("hide"); $("#cfgx").onclick = () => $("#cfg").classList.add("hide");
$("#fs").onclick = fullscreen;
[["range", "#c-range"], ["steer", "#c-steer"], ["dz", "#c-dz"]].forEach(([k, s]) => {
  const el = $(s), o = $(s + "v"); el.value = cfg[k]; o.textContent = cfg[k];
  el.oninput = () => { cfg[k] = +el.value; o.textContent = el.value; save(); };
});
$("#c-mode").value = cfg.mode; $("#c-mode").onchange = e => { cfg.mode = e.target.value; save(); hint(); };
$("#c-inv").checked = cfg.invert; $("#c-inv").onchange = e => { cfg.invert = e.target.checked; save(); };
$("#c-hap").checked = cfg.haptics; $("#c-hap").onchange = e => { cfg.haptics = e.target.checked; save(); buzz(30); };

const q = new URLSearchParams(location.search).get("pin");
$("#pin").value = q || load("fc.pin") || ""; if (q) history.replaceState(null, "", "/");

// ---- layouts (saved): car games vs normal games -----------------------------------------------
function applyLayout(l) {
  cfg.layout = l === "pad" ? "pad" : "car"; save();
  document.documentElement.dataset.layout = cfg.layout;
  $$("#lay button").forEach(b => b.classList.toggle("act", b.dataset.l === cfg.layout));
  releaseAll(); hint();
}
$$("#lay button").forEach(b => b.onclick = () => applyLayout(b.dataset.l));
applyLayout(cfg.layout);
