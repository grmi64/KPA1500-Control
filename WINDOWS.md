# KPA1500 Control Windows development candidate

This Windows development candidate starts in **Simulation** by default. The Windows launch panel offers Simulation, Read-only amplifier telemetry and Hardware control. These local changes have only offline validation; no hardware-enabled packaged acceptance or release approval is implied. No radio keying or drive-control feature exists.

## Launch modes

In Full view, Disconnect before switching modes. In the existing Connection section, select USB or TCP/IP. For TCP/IP, enter the address and command port; for USB, select a baud rate and choose the COM port after reopening (simulation does not enumerate devices). Choose the desired Windows launch mode, click Apply mode and reopen, and confirm. Reopening flushes preferences and closes the old service/reader before starting the replacement. Cancel leaves the current session unchanged. Mode changes are rejected while a reader or discovery scan exists or an action is queued.

- **Simulation:** simulated readings, controls and discovery; all hardware connections, startup auto-connect and sharing are blocked by the backend.
- **Read-only:** explicit USB/TCP telemetry connections; every control, power and wake action is rejected by the controller and worker. The transport accepts only an exact allowlist of 26 telemetry/identity query frames, rejecting mixed frames, setters and the USB wake handshake.
- **Hardware control:** explicit USB/TCP connection and existing guarded amplifier controls. The operator supplies/stops RF and sets drive power. Before ATU tuning, verify that the amplifier's existing hardware connections will not unexpectedly request radio transmission.

A mode handoff or endpoint-specific launch refuses to activate an already-open window for the target mode. Close that target window and retry; the existing connection is neither activated nor changed. Ordinary duplicate launches without a new endpoint still activate their existing window. After a reader error or terminal exit, Disconnect remains available while the local service is responsive, so its ownership can be released before changing modes. Abrupt reader termination does not break the state API or replay controls.

Both hardware modes start disconnected, even when saved settings request auto-connect; the operator must click Connect. Discovery also requires an explicit click and performs identification only. There is no automatic mode, tuning, power or wake action during reopen. A persistent mode notice stays visible in Full and Compact, including service failure. Normal launches always start in Simulation; choosing a mode does not silently change the next normal launch.

For explicit command-line launches, mutually exclusive `--demo`, `--read-only` and `--hardware` are available. Hardware endpoints require an explicit hardware access mode. Automated `--smoke-test` launches reject both hardware modes. Never use a hardware access flag for an offline test without mocking all physical transports.

## Run

For the review identity, extract the complete review folder and open `KPA1500 Control Review/KPA1500 Control Review.exe`. The production-named development candidate uses `KPA1500 Control/KPA1500 Control.exe` with the same default Simulation launch policy. Keep `_internal` beside the EXE. Python and native UI libraries are bundled. Windows 11 x64 and Microsoft Edge WebView2 Evergreen Runtime are required. If WebView2 is missing, the app gives installation/repair guidance before starting its backend. No administrator privileges are requested.

Windows settings and view preferences use `%LOCALAPPDATA%/KPA1500 Control/Windows`, separate from earlier Windows Review, OM and Mac settings. Simulation, Read-only and Hardware control have distinct settings, geometry and instance identities derived from the launch base path. Explicit test launches use `--demo --settings <new-file> --http-port 0`. No production settings should be supplied to a review session. Full/Compact, Light/Dark, meter, callsign, section visibility and stay-on-top preferences persist independently of the UI's random HTTP origin. Window size/position recover into the current display work area. About reports version/build and review mode. A second normal launch activates the existing window and creates no second reader. Deliberately isolated settings files define separate review identities for automated tests; endpoint leases protect hardware ownership independently.

The Windows loopback service uses an ephemeral port by default and the shared telemetry endpoint remains `/api/v1/telemetry`; sharing stays disabled in this offline review. The tokenized UI remains loopback-only with Host/Origin validation. The additional activation endpoint requires the same per-process token, accepts no equipment action, and uses only its validated 127.0.0.1 address.

## Discovery

In Simulation, Disconnect then Auto Discovery demonstrates synthetic progress, cancellation and selecting a simulated amplifier. Selection never connects or saves hardware settings; Connect is separate. No interfaces, COM devices or amplifier addresses are probed by simulated discovery.

The implemented Windows hardware discovery provider (not exercised live) passively enumerates COM ports for explicit user selection, without serial identity probes. Its TCP provider reads the default IPv4 route and directly attached interface, rejects invalid/routed gateway data, limits larger networks to the current /24, preserves smaller subnets, excludes the PC itself and caps TCP targets at 254. It provides bounded identity-only probes, cancellation and manual-IP fallback. This candidate has not been connected to hardware. Any live validation requires separate approval; offline tests use simulation or mocked transports only.

The complete folder also includes an EXE-specific `.exe.config` file beside the EXE. Keep that file with the package: it configures this application's .NET host to load its bundled managed assemblies when the ZIP retains Windows' downloaded-file marker. It does not remove those markers or change Windows, SmartScreen, or machine-wide .NET settings. The packaging audit rejects a missing or modified config.

## Develop and build

Use Python 3.12. `scripts/setup-windows.ps1` creates this project's own `.venv` and installs `requirements-windows.lock.txt`. Setup downloads dependencies; offline tests and simulator execution do not need Internet.

Run `scripts/test-windows.ps1`, then `scripts/build-windows.ps1` for the review identity, or `scripts/build-windows.ps1 -ProductionIdentity` for a separate production-named local candidate. See WINDOWS-RELEASE-IDENTITY.md for metadata and version mapping. The build includes pyserial's Windows implementation and port-listing module, pywebview/pythonnet runtime metadata, the DPI/asInvoker manifest, and dependency notices. The build runs `scripts/check-windows-notices.py`, verifying all notice/source hashes, all frozen module roots and every dependency DLL/PYD/JAR against the reviewed inventory. Changes to dependencies require inventory review.

Dependency notices are version-specific. The owner selected the MIT License for project-owned application code and artwork; see LICENSE and LICENSING.md. Third-party components retain their separate notices. Source builds are unsigned until separately signed. The current signed candidate and exact test scope are recorded in WINDOWS-RELEASE-CANDIDATE.md; signing does not authorize release or Store submission. See WINDOWS-PORT-STATUS.md for historical evidence.

Closing waits asynchronously for pending preference saves. If saving fails or times out, the window remains open and reports the error. Correct the storage problem and close again to retry the preference save. This mechanism does not retry any amplifier commands.

For isolated Mac cross-platform review, see MAC-REVIEW.md. Its stable review-origin solution applies only to the generated review wrapper; production Mac behavior is unchanged.

For finalized local user documentation, see [installation](WINDOWS-INSTALL.md), [support](WINDOWS-SUPPORT.md) and [data handling](WINDOWS-DATA-HANDLING.md). These newer source documents have not replaced the build-time documents inside the tested signed ZIP.
