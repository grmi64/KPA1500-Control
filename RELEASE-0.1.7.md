# KPA1500 Control 0.1.7 / build 8

- Optional read-only sharing with DX Caliber through the existing amplifier connection.
- Full and Compact meter colors, anchored scales and Light/Dark contrast.
- Optional saved station callsign badge in both display sizes.
- Window recovery after screen changes, reopening and display-size changes.

USB connection remains supported; TCP/IP is not included in this release. The application does not issue radio CAT commands. ATU Tune may request RF through existing station hardware connections.

Offline validation: 22 Python tests completed, 21 passed and one expected pseudo-terminal exclusivity skip; meter color suite and native window-placement checks passed. Previously recorded USB hardware checks remain in HARDWARE_TESTS.md. No new amplifier commands were sent during release preparation. Physical Intel and clean-machine installation testing remain pending.

Packaged backend checked in explicit simulation using a new temporary settings file: Full/Compact views and Light appearance rendered correctly; simulator warning remained visible. Native stay-on-top remains covered by prior manual checks; this release used the native placement test without launching another hardware wrapper. App notarization accepted: 61e5f3b0-2962-4884-8633-338e79de3e0b.
