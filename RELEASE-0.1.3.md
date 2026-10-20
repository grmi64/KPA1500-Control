# KPA1500 Control 0.1.3 / build 4

October 20, 2026: added the graphite/mint gauge icon with amber needle and RF waveform. macOS ICNS is wired through CFBundleIconFile; a seven-size transparent PNG-backed Windows ICO is included for future Windows packaging. PowerMaster II artwork remains deferred.

User explicitly authorized uploading the app to Apple and replacing Applications. Developer ID signing and Apple notarization accepted (d8a36eb8-f814-4668-821f-4e403cc5cc7a). Ticket stapled and validated. Installed through Finder after macOS blocked direct overwrite. Installed app signature, Gatekeeper, version 0.1.3 and AppIcon.icns resource verified before launch.

Backup of previous Applications copy: backups/installed-before-0.1.3/KPA1500 Control.app. Original notarized 0.1.2 DMG is also retained for rollback.

Launched /Applications/KPA1500 Control.app; saved auto-connect reached LIVE. OS inspection confirmed exactly one amplifier USB owner and one app/service/worker tree, with no DEV reader. No operating controls issued during installation. The initial local installation preceded the separate beta packaging below.

## Signed beta DMG

Built from clean source commit 10158f7; includes icon assets for macOS and future Windows packaging. App regression checks: 22 tests, 21 passed and one pseudo-terminal exclusivity skip. JavaScript syntax and embedded icon/version checks passed.

Developer ID signed clean app notarization: `a90711d5-f8a9-499a-8d6e-a7450229f7d6`. Signed DMG notarization: `0f137bc2-1466-4e4c-96e9-db9d8d340355`. Apple accepted both; tickets stapled and validated. App/DMG signatures, Gatekeeper, disk image checksum and mounted app/icon checks passed.

Filename: `KPA1500-Control-0.1.3-arm64.dmg`
Size: 7,099,179 bytes
SHA-256: `bad9fb12e3d4dceadff321871f4865ffbf53a6131f35ab134098984b3a74e25a`

Published at https://dxcaliber.com/beta/download-amplifier . Full private R2 and approved-tester Safari downloads match the final original. Downloaded DMG ticket validation and Gatekeeper passed. All 48 beta service tests passed; anonymous GET, HEAD, Range and forged-token requests denied. Signed-in listing verified 0.1.3. Existing combined and meter-only releases unchanged; 0.1.2 retained in private storage for rollback. Deployment: `32d36c41-537a-4a12-a6ad-c2b362a56ae2`.

The running Applications app and USB reader were not restarted for beta packaging. Physical Windows and clean-machine installation testing remain pending.
