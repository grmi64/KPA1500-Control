# KPA1500 Control 0.1.12 / build 13

Adds Ant 1 / Ant 2 selectors in Full and Compact views, highlighting the amplifier-reported selection. Unconfirmed antenna selections suggest checking the amplifier antenna configuration for the current band; commands are sent once and disabled antennas are not automatically enabled.

Cancel Tune now allows a bounded readback wait for tuning to stop without replaying the cancel command. Disconnect and readback errors stop confirmation; existing RF, stale-state and tuning command guards remain in place.

Offline validation: 38 Python tests completed (37 passed, one expected macOS pseudo-terminal exclusivity skip); all four JavaScript suites passed. Physical TCP/IP checks on firmware 03.06 confirmed ATU In/Bypass, successful operator-supplied-RF tuning, Cancel Tune with confirmed stopped state, and Ant 1 → Ant 2 → Ant 1 with operator front-panel agreement. Disabled antenna selections were refused by the amplifier, and the operator verified the new configuration warning. Final test state: Standby, Ant 1, ATU Bypass, 0 W, no faults. The app never keys the radio or changes drive power.

Fault recovery, physical Intel and clean-machine installation testing remain pending. See HARDWARE_TESTS.md for details. Distribution targets Apple Silicon, macOS 12+.
