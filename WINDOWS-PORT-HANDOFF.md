# Windows agent handoff — KPA1500 Control

## Starting point

Repository: https://github.com/grmi64/KPA1500-Control

Branch: review/windows-port-baseline-0.1.25

Mac baseline: 0.1.25/build 26. Prior committed release source: 8f9bd8e177d820986929b96588c8c534fcd387cf. Verify the exact baseline commit supplied with the draft PR. GitHub main is older; do not substitute main until this baseline has been reviewed and merged.

Read BASELINE-AUDIT-2026-10-26.md, README.md, HARDWARE_TESTS.md, Sources/protocol.py, engine.py, transport.py, port_lock.py, power.py, discovery.py, server.py, App.swift and scripts/build.sh first.

Clone outside OneDrive/cloud storage, for example under your user profile's source/repos directory. Preserve existing work. Do not reset an existing checkout, merge this draft, publish binaries or replace a working installation during initial port work.

## Invariants

Keep USB and TCP/IP as explicit alternatives. Share amplifier protocol, telemetry and command guards; adapt operating-system plumbing instead of forking the protocol. The standalone app owns one amplifier connection and DX Caliber consumes cached loopback telemetry.

The operator alone supplies/stops RF and sets radio drive power. Never add CAT, radio keying or drive-setting commands. An amplifier Tune request may invoke the station's existing hardware tuning setup; that is not authorization for software to key the radio. Any real amplifier connection, discovery, mode, power, ATU, antenna or fan test needs separate operator approval. Begin entirely offline.

Preserve fresh pre-command RF/tuning/fault checks, unknown/stale blocking, generation checks, three-second request expiry, one pending command and no operating-command replay. Keep one-shot setters with bounded readback, Cancel Tune confirmation timing, antenna-configuration guidance and amplifier-reported fan settings. Do not restore a local fan preference on reconnect. Preserve stale clearing, powered-off states and connection-error priority.

Power is explicit: Power Off requires confirmation. Ethernet Power On sends one WOL packet, makes bounded connection attempts and verifies the saved amplifier MAC against the hardware-reported identity. Never hard-code a user's IP/MAC. USB uses its documented power-on protocol. No wake on startup or ordinary reconnect. Preserve truthful unconfirmed outcomes and wake prerequisites.

## Implementation order

1. Reuse proven OM Power Windows patterns for the native webview, singleton/IPC, settings, COM handling, frozen multiprocessing and packaging. Reference OM commit 3953a947b3ff688f63e1c50c2d6880dc9ef472ba and its Windows-specific files. Review licenses/dependencies; do not copy OM wire commands, settings, identities or status framing.
2. Introduce platform adapters for serial transport, port enumeration/validation, endpoint locks and settings directories. Retain Mac implementations on Mac. Windows imports must not load termios, fcntl, Darwin or Mac commands. TCP requires portable endpoint leases as well as portable sockets. Do not weaken exclusivity to pass tests. Pin serial dependencies and handle COM10+, timeouts, driver/busy/disconnect errors.
3. Use an app-specific Windows settings directory and separate review settings with startup auto-connect and DXC sharing disabled. Preserve port 51980 and /api/v1/telemetry for same-computer DXC. Keep the UI's per-process token and loopback Host/Origin checks. Simulator automation must use --demo --settings with a new file and --http-port 0. Never copy production settings or expose the service to LAN clients. Cross-computer sharing remains future work.
4. Implement native equivalents for Full/Compact, Stay on top, display preferences, About/version, window recovery, graceful shutdown and single instance. Use Python 3.12 and PyInstaller 6.22.3 initially, including freeze_support and required hidden imports. End users must not need developer tools/Python. Prepare a pinned dependency and license/notice inventory before distribution.
5. Start USB discovery with passive COM listing and explicit user selection. Current Mac discovery sends identity queries to unowned ports; do not reproduce blind probing across all COM ports. Actual probes require hardware approval. For TCP discovery, implement bounded local-subnet enumeration before enabling it; preserve cancellation, no auto-connect or settings writes during scanning, visible progress/completion and manual fallback. No arbitrary/routed network scans.

## Validation and acceptance

Run python -m unittest discover -s tests -v and every tests/*.cjs suite. Baseline Mac results: 72 Python tests (71 passed, one expected pseudo-terminal skip), nine JavaScript suites and native placement tests passed. Add Windows alternatives for POSIX transport tests; document platform skips accurately and retain all command-guard coverage. Add regressions for Windows imports, COM exclusivity/validation, settings isolation, native startup/single instance/DPI and clean shutdown. Use fake USB transports and local TCP servers, not amplifier endpoints.

Exercise the frozen Windows simulator with new isolated settings, sharing/startup auto-connect off, Full/Compact, Light/Dark, meter choices, fan controls, power labels, stale/error displays, fake-provider discovery progress/cancel and process exit. Simulation controls must never reach hardware transports. Passing simulation or reusing Mac hardware evidence is not Windows hardware acceptance.

Report tested commit, OS/architecture, pinned dependencies, exact test counts/skips, packaged simulator results, artifact paths, unresolved issues and production-app/settings preservation. Stop before real hardware checks and request separate approval. Plan read-only USB/TCP checks before separately authorized mode, power, antenna, ATU, RF or fan tests.

Do not change Mac packaging, deployment minimum or command guards merely to enable Windows. OM's unique-UUID build option and Mac review guidance must be retained if editing that separate repository. KPA Mac build hygiene findings are listed in the audit for a separate Mac change.
