# KPA1500 Control — Windows support

Support channel: [KPA1500-Control GitHub Issues](https://github.com/grmi64/KPA1500-Control/issues). The owner selected this channel for KPA1500. No personal email address is listed. The signed Windows Preview is available through GitHub Releases.

## Reporting a problem

Search existing issues, then describe:

- Application version/build from About, and the package/source identifier if known.
- Windows version and whether you used Simulation, Read-only telemetry or Hardware control.
- Connection type if relevant, without posting private station addresses or device identifiers unnecessarily.
- Steps to reproduce, expected behavior, actual behavior and the exact error message.
- Whether the problem occurs in Full/Compact view, display scaling, reopening or missing-runtime handling.

Review screenshots and logs before posting: GitHub issues may be public. Remove private station/network details, local usernames/paths and anything unrelated. Do not attach credentials, Azure signing files/caches, `.instance.json` session files or entire WebView2 profiles. Share only the information needed to investigate. The app does not automatically submit a support report.

## Initial checks

- Verify the exact ZIP checksum and EXE publisher before running. Keep the complete signed payload and matching `.exe.config` together; an EXE signature alone does not validate the rest of the folder.
- Report any Windows security warning and exact .NET/CoreCLR error. A blocked bundled dependency can surface as a runtime error even when .NET is installed; do not disable security or remove download markers as a workaround.
- If WebView2 is unavailable, follow the app's Microsoft runtime repair guidance. Do not remove the host runtime as a troubleshooting step.
- Simulation is the first diagnostic mode and does not require hardware. Connection and operating tests require separate operator planning and authorization.
- Close other copies before diagnosing a busy-instance or endpoint-ownership message. Do not delete shared lock files while applications are running.
- A missing/stale reading or unavailable local backend should be reported with its exact status. Do not treat a disabled control as permission to retry equipment operations through another path.

Known candidate limitations and exact evidence are in [WINDOWS-RELEASE-CANDIDATE.md](WINDOWS-RELEASE-CANDIDATE.md). Physical two-monitor and final signed-package hardware acceptance passed for the recorded setup. Microsoft Store distribution remains deferred. No Elecraft affiliation or endorsement is asserted.
