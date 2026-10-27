# KPA1500 Control — Windows release notes draft

Local draft for the signed Windows 0.1.25/build 26 candidate from main 51c3106.
This document does not announce availability or authorize publication.

## Installation and first launch

1. Obtain the complete Windows x64 ZIP and its matching checksum from the approved distribution location when available. The current candidate is local only.
2. Compare the ZIP's SHA-256 with the matching WINDOWS-CANDIDATE-SHA256SUMS.txt. The repository copy resolves paths from the repository root; the standalone companion copy resolves its `../...` paths from the companion documentation folder. Keep that folder beside the ZIP and, after extraction, beside `KPA1500 Control/`. Run checksum tools from the selected checksum file's directory. The ZIP can be checked before extraction; the other entries require the extracted app. In PowerShell, use `Get-FileHash -Algorithm SHA256 -LiteralPath '<path-to-zip>'`.
3. Use Explorer **Extract All**. For standalone checksum verification, choose the directory containing the ZIP as the extraction destination; the archive already contains its top-level `KPA1500 Control/` folder. This puts that folder beside the ZIP and companion documentation folder, instead of inside an additional ZIP-named subfolder. Keep the entire extracted folder together, including `_internal`, `KPA1500 Control.exe.config`, licenses and notices. Opening the EXE from inside the ZIP or copying only the EXE is unsupported.
4. Verify the EXE's Digital Signatures tab shows Gregory Miller and a valid signature. The candidate's timestamp was verified. If Windows presents an unexpected warning or publisher, cancel and report it for review.
5. Open KPA1500 Control.exe. Normal Windows launches start in **Simulation**. No administrator prompt, Python installation or Node installation is required.

Windows 11 x64 and Microsoft Edge WebView2 Evergreen Runtime are required. If the runtime is unavailable, the app shows installation/repair guidance before starting its local backend. Install/repair the runtime through Microsoft's official installer on an Internet-connected PC, then reopen the app. Simulation itself works offline once prerequisites are installed.

## Windows behavior

Full and Compact views, Light/Dark appearance, native stay-on-top and saved display preferences are available. Simulation provides synthetic readings and controls without opening amplifier transports. The launch panel offers separate Read-only and Hardware control modes; both require an explicit mode change/reopen and manual Connect. Normal reopening starts in Simulation. No app radio-keying or drive-power commands exist; the operator controls RF and drive.

The downloaded-file startup fix adds an EXE-specific CLR configuration so the bundled managed runtime can load from a properly extracted Internet-marked ZIP. It does not remove file markers or alter machine-wide security policy. Keep the matching `.exe.config` beside its EXE.

## Settings, support and data-handling review notes

Settings and display preferences are local under `%LOCALAPPDATA%\KPA1500 Control\Windows`, with separate mode identities. Port-lock metadata is under `%LOCALAPPDATA%\Station Instruments\port-locks`. Keep review settings separate from normal settings. To remove the portable app, close it and remove its extracted folder; local settings remain unless the user separately removes them. No automatic settings deletion is provided.

The app's UI service listens on token-protected loopback. Sharing readings with another local application is optional; Simulation forces sharing and auto-connect off. Hardware connections and real discovery are explicit features outside Simulation. There is no developer analytics/update endpoint identified in the reviewed application source; this is a source observation, not a network audit or a policy covering Microsoft Windows/WebView2 services.

Proposed public support channel for owner approval: [KPA1500-Control GitHub Issues](https://github.com/grmi64/KPA1500-Control/issues). When reporting a problem, include app version/build, Windows version, launch mode and reproduction steps. Review screenshots/logs for private station/network details before sharing; never include credentials. No developer-account email is designated as a public contact by this draft. A public privacy-policy URL has not been approved or published for KPA1500.

## Known limitations and validation

Physical multiple-monitor acceptance remains pending. Final signed-package hardware acceptance remains separate from earlier live tests. Microsoft Store identity/MSIX/WACK work has not been completed for KPA1500. The current EXE remains prerelease, despite its valid signature. SmartScreen showed no warning in the Internet-enabled guest test; this does not guarantee reputation on other machines.

See WINDOWS-RELEASE-CANDIDATE.md for exact artifact hashes, passed tests, the Internet-enabled marker-check qualification and remaining release decisions. The tested ZIP's build-time documentation has not been modified to include these newer consolidation drafts.

Application code and project-owned artwork use MIT; see LICENSE and LICENSING.md. Third-party notices are bundled separately. This project is an independent implementation; no Elecraft endorsement is asserted.
