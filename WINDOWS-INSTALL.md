# KPA1500 Control — Windows installation

Installation text for the local Windows 0.1.25/build 26 candidate. No public download or publication is announced here. See [candidate validation](WINDOWS-RELEASE-CANDIDATE.md) for exact artifacts and remaining acceptance.

## Requirements and download verification

- Windows 11 x64.
- Microsoft Edge WebView2 Evergreen Runtime. Python and Node are bundled or unnecessary on the target PC; neither needs a separate installation.
- A standard Windows user account is sufficient to run the portable application. Installing or repairing a prerequisite may separately require Windows administrator approval.

Use the complete approved Windows ZIP and the checksum records for that exact ZIP. The current signed candidate is named in WINDOWS-CANDIDATE.json. In PowerShell, `Get-FileHash -Algorithm SHA256 -LiteralPath '<path-to-zip>'` reports the ZIP checksum for comparison.

The repository records resolve their `dist/windows/...` paths from the repository root. Standalone companion records resolve `../...` paths from the companion documentation directory. Run checksum tools from the directory containing the selected checksum file; JSON consumers resolve artifact paths from the JSON file's directory and declared base. ZIP validation is available before extraction. The other checksum entries require the extracted app folder.

## Extract and launch

1. Use Explorer **Extract All**. For the standalone companion layout, choose the directory containing the ZIP as the destination. The archive already contains the top-level `KPA1500 Control/` folder; this keeps that folder beside the ZIP and companion documentation directory rather than inside an extra ZIP-named directory.
2. Keep the extracted folder intact. `KPA1500 Control.exe`, `KPA1500 Control.exe.config`, `_internal`, licenses and notices must remain together. Running from inside the ZIP or copying the EXE alone is unsupported.
3. In the EXE's Properties → Digital Signatures, check the publisher is **Gregory Miller** and Windows reports a valid signature. The tested candidate has a verified Microsoft timestamp. Cancel an unexpected security warning or publisher mismatch and report it through [support](WINDOWS-SUPPORT.md).
4. Open `KPA1500 Control.exe`. A normal double-click launch starts in **Simulation**, with a SIMULATOR badge and no-hardware warning. No amplifier connection is needed for simulation.

The `.exe.config` is required for the application's .NET host to load bundled managed assemblies from an Internet-marked ZIP. It does not remove downloaded-file markers or change machine-wide Windows/.NET policy. Do not replace it with a config from a different package.

If WebView2 is unavailable, the app displays installation/repair guidance before starting the local backend. Obtain Microsoft's official Evergreen Runtime installer on an Internet-connected PC and install or repair the prerequisite, then reopen the app. Simulation works offline once prerequisites are installed. This package does not silently download the runtime.

## Launch modes and preferences

Full/Compact views, appearance, stay-on-top, meter selection, callsign and section visibility are saved locally. The launch panel can reopen the app in Simulation, Read-only telemetry or Hardware control. A confirmed mode change reopens in the mode selected for that handoff; a later normal double-click launch starts in Simulation again. Hardware modes start disconnected and require manual Connect. No operating, power, tune or wake request is sent merely by switching modes.

For future authorized hardware use, the operator controls RF and drive power. The app does not key the radio or set drive power. An amplifier ATU request can interact with the station's existing physical radio connections; verify those connections will not automatically initiate transmission before a live tuning test. Final signed-package hardware acceptance remains pending.

## Updates and removal

Close the app before replacing files. Extract an updated complete package into a separate directory, verify its own checksum/signature, and avoid mixing files from different versions. Existing local preferences may be reused by the new app; keep review settings separate from normal settings.

To remove the portable app, close it and remove its extracted folder. Settings and the local WebView2 profile remain under `%LOCALAPPDATA%\KPA1500 Control\Windows` unless separately removed by the user. Back up settings before resetting them, and close all KPA1500 processes first. Do not remove the shared `%LOCALAPPDATA%\Station Instruments\port-locks` directory to reset KPA1500; it is also used for endpoint coordination by other compatible applications.

See [data handling](WINDOWS-DATA-HANDLING.md) for stored fields and [support](WINDOWS-SUPPORT.md) for reporting problems. Physical multiple-monitor testing remains pending.
