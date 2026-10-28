# KPA1500 Control — Windows data handling

Prepared October 27, 2026 for the Windows 0.1.25/build 26 candidate. This statement describes application behavior checked against the local source. It is finalized locally for release preparation; a public privacy-policy URL has not been published or assigned. It does not describe Microsoft's or GitHub's services as if they were part of this application's own data handling.

## Local data

The application processes amplifier readings, status, faults and requested operations to display and control the amplifier in an explicitly selected hardware mode. Simulation uses synthetic readings and blocks amplifier connections, real discovery, sharing and startup auto-connect.

Windows stores settings and display preferences under `%LOCALAPPDATA%\KPA1500 Control\Windows` by default. Separate mode files can contain:

- USB port and baud rate, amplifier host/command port, saved amplifier MAC/broadcast settings and sharing/startup choices.
- A callsign entered by the user, selected meter, theme, Full/Compact view, section visibility, stay-on-top and window geometry.
- A local WebView2 profile and browser storage for the embedded UI. The profile can retain local UI data beyond a single session.

The application also creates temporary instance metadata containing a loopback address and session token under the Windows LocalLow known folder, normally `%USERPROFILE%\AppData\LocalLow\Station Instruments\instances`, with a compatibility sidecar beside the selected settings file. This lets packaged and portable copies activate the same existing window. Normal close releases ownership and removes its instance metadata; a crash may leave files behind. Windows ownership uses per-user named OS objects with hashed identity names. Supplemental endpoint lock files remain under `%LOCALAPPDATA%\Station Instruments\port-locks` for compatibility; this shared coordination directory is not a KPA1500-only settings store. Settings are ordinary local files, not an encrypted secret vault. Avoid placing credentials in settings or support attachments.

Recent action and fault history is held in application memory for the session rather than written as a persistent operational log by the controller. Automated smoke-test modes can write result, failure and diagnostic trace files beside their explicitly selected test settings. Support captures made by a user or testing tools are separate files and can include private information.

## Local UI and optional sharing

The embedded UI communicates with a loopback-only HTTP service on `127.0.0.1`, normally using an ephemeral port. UI state/actions use a per-session token and Host/Origin checks. This service does not listen on the LAN interface.

If the user enables **Share readings with DX Caliber** outside Simulation, the separate loopback telemetry endpoint exposes cached model/status, reading age, forward/reflected power, SWR, temperature, Operate state, antenna, ATU state and simulation indication. That read-only endpoint does not require the private UI token: other local software able to reach the port may request these readings while sharing is enabled. It accepts no amplifier-control action and performs no hardware read just to serve a request. Sharing is disabled by default and forced off in Simulation. It is not a developer-operated cloud feed.

## Network activity and third parties

Outside Simulation, explicit hardware connections use the selected USB port or amplifier TCP/IP endpoint. Real discovery and Wake-on-LAN are optional hardware features invoked by the operator; they can send identification probes or a wake packet on the local network. Windows hardware modes start disconnected and do not automatically replay operations after connection failure.

No developer-operated analytics, advertising, account sign-in or automatic update endpoint was identified in the reviewed application source. This is a source observation, not a packet-capture audit or a promise that the operating system and its components never communicate externally. Windows security/reputation checks and WebView2 runtime servicing or diagnostics are governed by the user's Windows/WebView2 configuration and Microsoft's terms and policies. Downloading prerequisites and publishing software are separate activities from amplifier simulation.

Opening or posting to [GitHub Issues](https://github.com/grmi64/KPA1500-Control/issues) uses GitHub's service. The user chooses what to share; the application does not automatically send screenshots, settings, telemetry or logs to that support channel. Review and redact attachments as described in [support](WINDOWS-SUPPORT.md).

## Retention and removal

Local settings and WebView2 data can remain after the portable application folder is removed. Close the app and any remaining KPA1500 processes before backing up or resetting its local settings/profile directory. Removing it loses saved preferences and connection information. Do not clear the shared Station Instruments lock directory to remove KPA1500 data. Closing a process releases its active OS-held lock even when an empty lock file remains.

See [installation](WINDOWS-INSTALL.md) for removal/update instructions and [support](WINDOWS-SUPPORT.md) for data-handling questions. No hardware connection or publication was performed to prepare this statement. Physical multiple-monitor and final signed-package hardware acceptance remain pending.
