# KPA1500 Control 0.1.9 / build 10

Connection-loss, stale-reading and reconnect messages now take priority over feedback from earlier operating commands. A previous “Standby confirmed” message no longer hides a newer connection error. Existing USB/TCP transport, command guards, manual reconnect behavior and DX Caliber sharing are unchanged.

Offline validation: 30 Python checks completed (29 passed, one expected pseudo-terminal exclusivity skip), and all three JavaScript suites passed. The new regression test first reproduced the old confirmation masking a disconnect error, then passed after the priority fix. It also checks stale, startup and local-service errors while preserving live action confirmation/failure feedback.

Existing TCP hardware validation includes monitoring, automatic startup, Operate/Standby, operator-controlled power/SWR comparison with the front panel, and manual recovery after cable loss. No ATU controls were exercised over TCP. Physical Intel and clean-machine installation testing remain pending.

Live 0.1.9 retest passed: stale readings cleared and controls disabled at approximately 2.6 seconds after the last fresh sample; connection-closed/reconnect error appeared at approximately 9.5 seconds. Correct error text was visible. Restoring LAN did not reconnect automatically; explicit Connect restored LIVE Standby/0 W readings in the app and DXC without operating-command replay. No operating or tuning commands were sent during this test.
