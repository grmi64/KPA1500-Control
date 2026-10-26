# KPA1500 Control 0.1.15 / build 16

Adds Power Off / Power On on a separate row beneath the ATU controls in Full and Compact views. Power Off requires confirmation and fresh RF-off/tuning checks. USB startup uses the documented wake preamble and explicit power command. Ethernet startup uses one Wake-on-LAN packet and bounded connection/readback attempts; the connected amplifier’s MAC is discovered and saved automatically. NET WAKE on LAN, rear power switch and AC must be enabled for Ethernet wake. First-time startup while already off allows manual MAC entry. Startup mode follows the amplifier’s own POWER ON MODE setting.

Power requests are never automatically replayed. A lost connection alone does not prove shutdown. Readings clear when power is off, and unavailable operating controls disable. Successful network wake now says “Wake-on-LAN startup confirmed” rather than “already powered on.”

Also includes the top operating-mode badge (OPERATE / STANDBY / MODE UNKNOWN), driven by fresh telemetry, and clearer platform-neutral wording for same-computer DX Caliber sharing. Sharing between computers remains a future feature.

Validation: 55 Python tests completed (54 passed, one expected macOS pseudo-terminal exclusivity skip), all six JavaScript suites passed, and the packaged simulator completed off/on transitions. USB and Ethernet power cycles passed on firmware 03.06 with operator front-panel confirmations and subsequent manual testing. Existing TCP telemetry, ATU, antenna-selection and reconnect hardware results are documented in HARDWARE_TESTS.md. No radio keying or drive-power control is provided. Windows port, clean-machine installation and physical Intel validation remain pending. Distribution targets Apple Silicon, macOS 12+.
