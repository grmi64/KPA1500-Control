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
