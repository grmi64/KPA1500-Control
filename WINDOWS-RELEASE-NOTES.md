# KPA1500 Control - Windows prerelease notes

Application 0.1.25/build 26. Runtime/build source 9efe8c1; documentation-only packaging source main 8de9337 after PR #11. Local release preparation only; no public availability is announced.

This repackage reconciles bundled documentation and includes the validation report so its links resolve locally. Signed runtime files, config, licenses and third-party notices are unchanged. The archive has a new external checksum; earlier ZIP acceptance is retained only as historical payload evidence. New offline package checks are recorded externally after creation.

Normal double-click starts in Simulation. Read-only and Hardware control modes require explicit handoff and start disconnected. The operator supplies/stops RF and sets drive power; the app must not key the radio or set drive. Windows 11 x64 and Microsoft Edge WebView2 Evergreen Runtime are required.

Read [installation](WINDOWS-INSTALL.md), [support through GitHub Issues](WINDOWS-SUPPORT.md), [data handling](WINDOWS-DATA-HANDLING.md), [licensing](LICENSING.md) and [validation and limitations](WINDOWS-RELEASE-CANDIDATE.md).

Physical multiple-monitor and final signed-package hardware tests remain pending. Store certification, distribution/version decisions, public privacy-policy hosting and publication approval remain separate. Earlier no-warning Explorer observations are not guaranteed SmartScreen reputation on every PC.
