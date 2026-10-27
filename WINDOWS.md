# KPA1500 Control Windows review

This unsigned development build runs **offline simulation only**. Its backend rejects USB/TCP amplifier connections and startup auto-connect/sharing. The interface retains connection fields so the shared Mac UI can be reviewed; choosing hardware cannot bypass the backend guard. No radio keying or drive-control feature exists.

## Run

Extract the entire review ZIP, then open `KPA1500 Control Review/KPA1500 Control Review.exe`. Keep `_internal` beside the EXE. Python and native UI libraries are bundled. Windows 11 x64 and Microsoft Edge WebView2 Evergreen Runtime are required. If WebView2 is missing, the app gives installation/repair guidance before starting its backend. No administrator privileges are requested.

Review settings and view preferences use `%LOCALAPPDATA%/KPA1500 Control/Windows Review`, separate from OM and Mac settings. Explicit test launches use `--demo --settings <new-file> --http-port 0`. No production settings should be supplied to a review session. Full/Compact, Light/Dark, meter, callsign, section visibility and stay-on-top preferences persist independently of the UI's random HTTP origin. Window size/position recover into the current display work area. About reports version/build and review mode. A second normal launch activates the existing window and creates no second reader. Deliberately isolated settings files define separate review identities for automated tests; endpoint leases protect hardware ownership independently.

The default loopback port remains 51980 and the shared telemetry endpoint remains `/api/v1/telemetry`; sharing stays disabled in this offline review. The tokenized UI remains loopback-only with Host/Origin validation. The additional activation endpoint requires the same per-process token, accepts no equipment action, and uses only its validated 127.0.0.1 address.

## Discovery

In this review, Disconnect then Auto Discovery demonstrates synthetic progress, cancellation and selecting a simulated amplifier. Selection never connects or saves hardware settings; Connect is separate. No interfaces, COM devices or amplifier addresses are probed by simulated discovery.

The implemented Windows hardware discovery provider (not exercised live) passively enumerates COM ports for explicit user selection, without serial identity probes. Its TCP provider reads the default IPv4 route and directly attached interface, rejects invalid/routed gateway data, limits larger networks to the current /24, preserves smaller subnets, excludes the PC itself and caps TCP targets at 254. It provides bounded identity-only probes, cancellation and manual-IP fallback. Actual hardware discovery/connection needs separate approval and a future explicitly enabled hardware session.

## Develop and build

Use Python 3.12. `scripts/setup-windows.ps1` creates this project's own `.venv` and installs `requirements-windows.lock.txt`. Setup downloads dependencies; offline tests and simulator execution do not need Internet.

Run `scripts/test-windows.ps1`, then `scripts/build-windows.ps1`. The build includes pyserial's Windows implementation and port-listing module, pywebview/pythonnet runtime metadata, the DPI/asInvoker manifest, and dependency notices. The build runs `scripts/check-windows-notices.py`, verifying all notice/source hashes, all frozen module roots and every dependency DLL/PYD/JAR against the reviewed inventory. Changes to dependencies require inventory review.

Dependency notices are version-specific. The application currently has no confirmed root distribution license; third-party notices do not grant a KPA application release license. This is a local review artifact, not a signed release or Store submission. See WINDOWS-PORT-STATUS.md for evidence and remaining acceptance.

Closing waits asynchronously for pending preference saves. If saving fails or times out, the window remains open and reports the error. Correct the storage problem and close again to retry the preference save. This mechanism does not retry any amplifier commands.

For isolated Mac cross-platform review, see MAC-REVIEW.md. Its stable review-origin solution applies only to the generated review wrapper; production Mac behavior is unchanged.
