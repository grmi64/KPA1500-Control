# KPA1500 Control — Windows candidate release notes

Finalized local installation, support and data-handling text for Windows 0.1.25/build 26, based on the signed candidate from main 51c3106. These documents do not announce public availability or authorize repackaging/publication.

- [Installation, verification, launch modes, updates and removal](WINDOWS-INSTALL.md)
- [Support through KPA1500-Control GitHub Issues](WINDOWS-SUPPORT.md)
- [Local storage, optional sharing and data handling](WINDOWS-DATA-HANDLING.md)
- [Candidate validation, checksums and remaining acceptance](WINDOWS-RELEASE-CANDIDATE.md)

The owner selected GitHub Issues as the public support channel, without a personal email listing. The data-handling statement is local text; no public privacy-policy URL has been published or assigned.

## Candidate changes and validation

The Windows port provides the shared amplifier UI in a native window with Full/Compact views, appearance and stay-on-top controls, saved preferences, separate Simulation/Read-only/Hardware launch modes, and bundled Python/native dependencies. Normal double-click launches start in Simulation. Hardware mode changes reopen in the explicitly selected mode and start disconnected.

The downloaded-file fix supplies a matching `.exe.config` for the application's .NET host, allowing its bundled managed assemblies to load from a properly extracted Internet-marked ZIP. Downloaded-file markers and machine-wide security settings are not changed by that configuration. Keep it beside the EXE.

The exact signed candidate passed identity/license/dependency audits, offline marked-file shell launch, standard-user persistence and missing-WebView2/recovery checks. An Internet-enabled Explorer launch reached Simulation and showed no warning to agent or user. The raw post-launch marker-check qualification is retained in the validation report; this result does not guarantee SmartScreen behavior on other PCs.

## Pending release work

The EXE remains prerelease. Physical multiple-monitor and final signed-package hardware acceptance remain pending. KPA1500 Store identity/MSIX/WACK, release-version decisions and publication approval remain separate. No hardware test or publication is authorized by finalizing this text.

The tested ZIP remains unchanged and contains its original build-time documentation. The finalized text is held separately for a later reviewed repackaging. A regenerated ZIP must receive new checksums and artifact-specific validation; it must not inherit the old ZIP's hash or be presented as already tested.

Application code and project-owned artwork use MIT; see LICENSE and LICENSING.md. Bundled third-party components retain their own notices. No Elecraft affiliation or endorsement is asserted.
