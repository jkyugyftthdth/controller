Forza Controller
Use your Android phone as a controller for Forza Horizon 4 on Windows 11 - no driver needed.
The Windows app receives your touches/tilt over the local network and presses keyboard keys.
Phone	PC key (FH4 default)
ACCELERATE (hold)	W
BRAKE / reverse (hold)	S
HANDBRAKE (hold)	Space
REWIND (hold)	R
Tilt phone like a wheel	A / D (pulsed for partial steering)
Check these against FH4 > Settings > Controls > Keyboard; change `SCAN` in `app/keyboard.py` if you remapped.
Use
Run `ForzaController.exe`. It shows a QR code and a PIN.
Phone and PC on the same network: home Wi-Fi router, or the Windows 11 Mobile Hotspot (join it from
the phone). Pick the matching network in the dropdown.
Scan the QR code. First time only: Chrome warns "connection is not private" (the app uses its own
certificate so that motion sensors are allowed). Tap Advanced > Proceed.
Tap CONNECT, hold the phone landscape like a wheel (it auto-calibrates; use Calibrate to re-centre).
Click into the Forza window once so it has keyboard focus, then drive.
Settings (on the phone, saved automatically)
Gyro or touch-strip steering, full-lock angle, steering sensitivity, deadzone, invert, vibration, fullscreen.
How steering works
Keyboards are digital, so the app turns A/D on and off ~100 times a second; the share of time a key is
down matches your tilt, and Forza's own keyboard steering smoothing averages it. It is smoother than plain
A/D but not identical to a real analog stick.
Portable EXE
`ForzaController.exe` is a single file: no installer, no Python, no driver. Put it anywhere (Desktop, USB stick);
its PIN, settings and certificate are stored in a `ForzaController_data` folder next to it.
Get the EXE either way:
GitHub (no Python needed): push this project to GitHub, open Actions > Build portable EXE > Run workflow,
then download `ForzaController-portable` from the finished run.
Locally on Windows: double-click `build.bat` -> `dist\ForzaController.exe`.
Run from source / build
```
pip install -r requirements.txt
python -m app.main        # or: build.bat  ->  dist\ForzaController.exe
```
Troubleshooting
Game ignores keys: if Forza runs as administrator, run this app as administrator too.
Page won't open: allow the app in Windows Firewall, or run once as admin:
`netsh advfirewall firewall add rule name="ForzaController" dir=in action=allow protocol=TCP localport=8443 profile=any`
"No motion sensor data": switch Steering to Touch strip in Settings.
Car steers the wrong way: tick Invert steering.
Hotspot not listed: turn it on, then press Rescan.
Security
Traffic is encrypted but the certificate is self-signed; use your own router or the PC hotspot, not public Wi-Fi.
Controller mode (recommended for Forza)
If the game ignores keyboard keys, install the free ViGEmBus driver once (https://github.com/nefarius/ViGEmBus/releases, run the installer, reboot). On start, the app then shows "Mode: Virtual Xbox controller" and appears to Forza as a real Xbox 360 pad. Without the driver it falls back to keyboard keys (only ACCELERATE, BRAKE, HAND BRAKE, REWIND and tilt steering work in that mode). In Forza, set the controller input to the gamepad (unplug/disable other pads if it picks the wrong one).
The phone screen is a full on-screen Xbox controller:
Phone	Xbox pad
BRAKE	LT
ACCELERATE	RT
LB / RB	LB / RB
Phone tilt (or left on-screen stick)	left stick, analog
Right on-screen stick	right stick (camera)
D-pad	D-pad
A (HAND BRAKE)	A
B	B
X (NITROS)	X
Y / REWIND button	Y
BACK / START	Back / Start
Multi-touch works, so you can steer, accelerate and hit buttons at the same time.
