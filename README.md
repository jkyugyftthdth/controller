# Forza Controller

Use your phone as a PS5-style controller on Windows. The PC app turns your touches and tilt into a **virtual Xbox 360 controller**, so games (Forza Horizon, any XInput game) see a normal gamepad.

## Install (Windows 10/11)
1. Download **ForzaController-Setup.exe** from the [latest release](../../releases/latest) (or from Actions > latest run > `ForzaController-installer`).
2. Run it and keep the options ticked: the **gamepad driver (ViGEmBus)** and the **firewall rule**. Reboot if the driver asks.
3. Start *Forza Controller* (it runs as administrator). The window should say **Mode: Virtual Xbox controller**.
4. Scan the QR code with the phone camera, accept the one-time certificate warning (*Advanced > Proceed*), enter the PIN, tap CONNECT.

A portable `ForzaController.exe` (no installer) is attached to the same release; it still needs the ViGEmBus driver for controller mode.

## Two saved layouts (CAR / PAD switch in the phone's top bar)
| | CAR (racing) | PAD (normal games) |
|---|---|---|
| Steering | tilt the phone like a wheel (or the left stick) | left stick |
| Triggers | big BRAKE (LT) and ACCELERATE (RT) | L2 / R2 with L1 / R1 |
| Centre | steering wheel and tilt bar | brand panel, L3 / R3 |
| Always there | D-pad, both sticks, Create / PS / Options | same |

The phone remembers the last layout you used.

## Button map (PS symbols -> Xbox buttons the game sees)
| Phone | Xbox pad |
|---|---|
| L2 / BRAKE, R2 / ACCELERATE | LT, RT |
| L1, R1 | LB, RB |
| Left stick (or tilt in CAR) | left stick |
| Right stick | right stick |
| D-pad | D-pad |
| cross, circle, square, triangle | A, B, X, Y |
| L3, R3 | stick clicks |
| Create, PS, Options | Back, Guide, Start |

In CAR layout the cross is HANDBRAKE, square NITROS and triangle REWIND (Forza defaults for A, X, Y).

## Connecting: Wi-Fi, hotspot, Ethernet, Bluetooth, USB
The phone talks to the PC over the network, so any link that puts both on one network works. The app lists each address with its type; pick one and scan the QR code.
- **Wi-Fi / Ethernet:** PC and phone on the same router (PC can be wired).
- **PC Mobile Hotspot:** turn on the Windows hotspot, join it from the phone.
- **Phone hotspot:** join the phone's hotspot from the PC.
- **Bluetooth:** pair the phone, turn on *Bluetooth tethering* on the phone, connect the PC to it. It appears as "Bluetooth tethering". (A browser page cannot use classic Bluetooth directly, so Bluetooth works as a network link.)
- **USB cable:** turn on *USB tethering* on the phone. Lowest latency.

Press **Rescan** after turning a link on.

## Build from source
```
pip install -r requirements.txt
python -m app.main          # run
build.bat                   # dist\ForzaController.exe
iscc installer\ForzaController.iss   # dist\ForzaController-Setup.exe (needs Inno Setup 6)
```
GitHub Actions builds the exe and installer on every push and publishes them to the `latest` release.
Note: `pip install vgamepad` launches the ViGEmBus installer; the CI workflow unpacks the package without running it.

## Troubleshooting
- **Game ignores the pad:** make sure the window says "Mode: Virtual Xbox controller". If it says keyboard, install ViGEmBus and restart the app. In the game, pick the controller as the input device.
- **Page won't open on the phone:** allow the app in the firewall (the installer does this), and make sure the phone is on the network you picked.
- **"No motion sensor data":** Settings > Steering > Touch strip, or use the left stick.
- **Steers the wrong way:** Settings > Invert steering.
- **Keyboard fallback** (no driver) only supports accelerate, brake, handbrake, rewind and tilt steering.

## Security
Traffic is encrypted with a self-signed certificate and protected by a PIN. Use your own router, hotspot, cable or Bluetooth link, not public Wi-Fi.
