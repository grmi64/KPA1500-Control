# DXC power sharing — Build 34

Based on exact Build 33 source, preserving the Windows Build 31 baseline and the bounded, non-evicting request receipt fix. Version 0.1.27 / Build 34.

Connection offers a separate Share power controls with DX Caliber checkbox, default off, dependent on reading sharing. Mode and power sharing can be enabled independently; disabling readings revokes both. Offline/read-only sessions cannot send shared controls. Existing saved settings are preserved; power sharing is not enabled automatically.

GET /api/v1/power reports cached, scoped capabilities; POST requires exact loopback Host, no Origin, backend token, unique ID, explicit confirmation, current generation and expected status. Mode and power routes share a single bounded receipt map and include route identity in duplicate comparison. No eviction, retry or reconnect replay. New IDs fail closed at capacity while existing receipts remain.

Power Off requires live fresh known RX/tuning-free <=0.5W state. Existing worker preflight checks remain authoritative. Power On is offered only for confirmed powered_off state plus an eligible saved USB port, Ethernet wake MAC, or simulator. Disconnected/error/stale never mean off. USB/TCP wake uses the existing companion path; DXC opens no new device connection. Existing DXC power adapter, confirmation dialog and state-driven button are reused.

Mac source regressions: 330 run, 304 passed / 26 platform skips. All 12 JavaScript suites and Swift placement checks passed. Actual frozen companion through DXC adapter and simulator worker confirmed Off then On; sharing revocation and clean exit verified. Physical hardware power commands were not tested. Windows compilation and secure ephemeral-port discovery / DXC integration remain pending. No public package, merge or publication.

Local Mac companion is arm64, ad-hoc signed, not a notarized release. Native target retains the previously qualified host-target baseline. DXC 0.6.166 / 766 is Developer ID signed and preserves the personal Digital Loggers integration, which remains private.
