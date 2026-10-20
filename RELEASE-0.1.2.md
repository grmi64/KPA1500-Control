# KPA1500 Control 0.1.2 / build 3

Released October 20, 2026 for Apple Silicon, macOS 12+. Built from clean source commit c4b92e1.

- Fixes Quit/close hanging while waiting for amplifier service exit. Native shutdown is asynchronous and bounded; worker stop signaling and disposable state queue cleanup avoid stranded shutdown waits.
- Adds **Automatically connect at startup** in Full view → Connection. Off by default; saves selected USB port and baud immediately. One bounded USB attempt on launch, with manual Connect available after failure. No automatic retry loop or replay of operating commands.
- Retains the Standby parser fix, single-reader protection, transmit guards and independent amplifier worker. No radio CAT commands added.

## Release verification

22 app tests: 21 passed, one pseudo-terminal exclusivity test skipped. JavaScript syntax check passed. Three clean release simulator shutdowns exited in approximately 0.04 seconds; saved startup with an absent test port failed cleanly. Developer ID signed service smoke test verified simulator LIVE, new checkbox assets and clean exit. Earlier native close-button and checkbox save tests are documented in README.md.

Apple accepted app submission `10d17a59-b931-4d8f-9f29-d24f02f6559b` and DMG submission `ed451381-ac00-450b-b144-64f4e68e8c1f`. App/DMG tickets stapled and validated. Signatures, Gatekeeper, disk-image checksum and mounted app version/build passed. Installer includes the Applications shortcut.

Filename: `KPA1500-Control-0.1.2-arm64.dmg`  
Size: 4,745,319 bytes  
SHA-256: `29b2736ab33c54ec540f37ff277df41f37d4daa0b2c8be457e9b2f632db6bbb9`

Private R2 full-download and approved-tester Safari download both match the final notarized original. Safari-downloaded DMG passes stapler validation and Gatekeeper. All 48 beta service tests passed; live anonymous GET, HEAD, Range and forged-token downloads were blocked.

Published separately at https://dxcaliber.com/beta/download-amplifier . Existing combined and meter-only downloads unchanged; 0.1.0 retained in private storage for rollback. Worker deployment: `8763bf82-2667-4448-be23-9af499a30a89`.

Hardware validation and pending Cancel Tune/fault/multiple-antenna checks remain in HARDWARE_TESTS.md. Clean-machine installation and a new live-USB auto-connect cycle remain pending. Release packaging did not replace or restart the running station apps.
