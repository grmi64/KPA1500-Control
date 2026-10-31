# Windows Preview 0.1.25/build 27 — published beta

[Download signed build 27](https://github.com/grmi64/KPA1500-Control/releases/tag/v0.1.25-windows-preview-build27) and its `SHA256SUMS.txt` release asset. Normal launch opens **Hardware control, disconnected**, with blank readings until Connect. Optional Simulation and Read-only telemetry are under Connection → Application mode. Hardware mode has no simulation banner or simulated-transmit control.

Source/tag commit: `3e19bcb89c2f0dd77982399374ca868a01752da8`; PR #23 merge: `02e2f0d06529e60faaa2aa291a0566ccf44902d3` (identical source tree). ZIP SHA256: `53bda17ce7f7c5ab765e116e0cd95a01242a6ab07238917af72b84993a83e0bf`. EXE SHA256: `56b3d1dc30bf235816e0a792e1a9c386696d1227e22dfdd9c48d553fd4c38e48`. Numeric Windows version: 0.1.25.27; Windows Preview/prerelease retained.

Publication was authorized October 30, 2026 with **hardware testing to be done manually by the owner; no build 27 full hardware acceptance is claimed**. The owner approved Full and Compact views. Validation passed: 306 Python tests/two expected skips, all 12 JavaScript suites, two exact signed offline smoke runs (19 checks each), 78 native signatures, 24 frozen source-module comparisons, and the ordinary disconnected/blank-reading launch check. Independent Mac execution was not performed for this change; no CI pass claimed.

The published ZIP/checksum were downloaded anonymously and hash-verified. No installation was performed. Raw evidence and the Mac review bundle remain local. This publication does not modify the signed ZIP or its older bundled documents. Microsoft Store distribution remains deferred.

## Previous build 26 records — historical

The records below describe build 26 and its completed acceptance. They do not establish build 27 hardware acceptance, and unversioned manifest/checksum links now identify the current build 27 beta.

# KPA1500 Control — Windows Preview release notes

Publication update: [Windows Preview 0.1.25/build 26](https://github.com/grmi64/KPA1500-Control/releases/tag/v0.1.25-windows-preview-build26) is published on GitHub with the unchanged accepted signed ZIP and checksum. No installation was performed. Statements below about no publication describe the acceptance or earlier preparation milestones.

Accepted merge: `a400cfe04a09ac7c007186b0c7c1ab0d164b50cf` ([PR #20](https://github.com/grmi64/KPA1500-Control/pull/20)). Application **0.1.25/build 26, Windows Preview**, numeric Windows version 0.1.25.26; prerelease flag retained. Portable ZIP first; Microsoft Store deferred.

- ZIP: `KPA1500-Control-0.1.25-build26-startup-a400cfe-Windows-x64-signed.zip`.
- ZIP SHA256: `09d4796044eff347e55499d91c2faab503fcfccba9411f76f1f39387db608ddd`.
- EXE SHA256: `a719fd27942cb83f4534c2f8a9191016701085b9d4a9d4539498981d32a48e27`.
- Evidence: [full acceptance report](dist/windows/startup-a400cfe-2026-10-30/FULL-ACCEPTANCE.txt), [structured results](dist/windows/startup-a400cfe-2026-10-30/FULL-ACCEPTANCE.json), [current manifest](WINDOWS-CANDIDATE.json), and [checksums](WINDOWS-CANDIDATE-SHA256SUMS.txt).

Evidence links under `dist/windows/` refer to preserved local acceptance files; those artifacts are not committed or uploaded by this documentation PR.

This accepted merge includes the USB timeout reconfiguration guard, fresh power observations, window geometry/recovery corrections, activation readiness and native startup fixes. Native geometry property access now uses managed dispatch to avoid the reproduced sizing stall. Offline Simulation permits one bounded startup-only recovery for the reviewed invalid-handle failure; later failures remain visible and hardware recovery requires explicit Connect.

USB hub monitoring, Ethernet monitoring, controls, power cycling, USB loss/recovery, tuning and RF meter comparison passed on the exact signed package. Physical two-monitor resize/reopen and missing-display recovery passed. The RF comparison was about 550 W/SWR 1.10; the operator confirmed app agreement, RF off and Standby. See the acceptance report for setup and retained qualifications.

Normal double-click starts in Simulation. Read-only and Hardware control modes require explicit handoff and start disconnected. The operator supplies/stops RF and sets drive power. Windows 11 x64 and Microsoft Edge WebView2 Evergreen Runtime are required.

Read [installation](WINDOWS-INSTALL.md), [support through GitHub Issues](WINDOWS-SUPPORT.md), [data handling](WINDOWS-DATA-HANDLING.md), [licensing](LICENSING.md) and [validation and limitations](WINDOWS-RELEASE-CANDIDATE.md).

Nothing was installed or published. Publication authorization, Store certification and public privacy-policy hosting remain separate. These updated repository records do not modify the accepted ZIP or its bundled build-time document copies. Earlier security, clean-PC and private MSIX tests retain their original package attribution; earlier no-warning Explorer observations are not a universal SmartScreen reputation guarantee.
