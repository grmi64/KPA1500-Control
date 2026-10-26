# KPA1500 Control 0.1.8 / build 9

Adds TCP/IP (Ethernet) alongside USB and Simulator. Enter the amplifier IP address and command port (normally 1500); Connect saves the hardware selection. USB port/baud remain saved when switching, and optional startup connection follows the selected transport. DX Caliber sharing works over either connection.

Uses the same paced protocol, readback checks and operating guards as USB. TCP requests are never automatically replayed; connection loss requires an explicit reconnect. Only one TCP client can connect to the amplifier at a time. IPv4 and IPv6 addresses are supported; hostnames and URLs are not accepted.

Allow macOS Local Network access when prompted. If the initial connection fails while permission is being granted, restart the app and click Connect. Access can be checked in System Settings → Privacy & Security → Local Network.

Validation: 30 Python tests completed (29 passed, one expected pseudo-terminal exclusivity skip), both JavaScript suites and native placement checks passed. Tests cover fragmented replies, timeout/EOF, duplicate endpoint ownership, saved connection settings, reconnects, existing operating guards and USB behavior.

Live Mac verification on firmware 03.06: three GET-only TCP sessions, installed-app monitoring and DXC sharing, twenty consecutive fresh LIVE samples, released USB port, and automatic TCP connection after app restart. Amplifier remained Standby at 0 W; no operating, tuning, power, radio-keying or drive-power commands were issued during these checks. Operating controls over TCP, prolonged network-loss testing and clean-machine installation remain pending.

Apple Silicon; macOS 12 or later. Separate signed release packaging preserves the running application and production settings.
