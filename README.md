# KPA1500 Control 0.1.2

Standalone macOS amplifier monitor and operating panel. Open `dist/KPA1500 Control.app`.

## Getting started

The app starts disconnected by default. Enable **Automatically connect at startup** in Full view → Connection to use the selected USB port and baud rate on the next launch. The preference saves immediately and makes one bounded connection attempt per launch; failure leaves manual Connect available. It never changes Operate/Standby, antenna or ATU state. Choose **Simulator · no hardware** and Connect to explore both views without equipment. For USB, use the KPA1500 **Host PC** connector, select its `/dev/cu.*` port, and match the amplifier's **SERIAL SPEED HOST** baud setting before connecting. Do not select your radio or PowerMaster port.

**Full view** includes forward/reflected power, SWR, temperature, input power, voltage/current, frequency, LCD text, firmware, faults, connection settings and operation history. **Compact view** uses the same connection and controls, with optional native **Stay on top**. Light and Dark appearance are available in both.

Controls: Operate, Standby, next already-enabled antenna, ATU In/Bypass, Tune/Cancel tune, and clear fault. Tune requests can cause the amplifier to request RF through the station's existing hardware connections. The app does not issue radio CAT commands.

## Connection and control behavior

- One serial worker and one app instance; per-port locking and serial exclusivity protect against duplicate readers.
- USB commands are paced by waiting for replies. No automatic reconnect or replay of operating commands.
- Each operation rechecks amplifier transmit, power, tuning and fault status. Unknown/stale or transmitting state blocks controls; Cancel tune remains available during an active tune.
- Display values expire when readings go stale. Actions use amplifier readback, rather than assuming success.
- Fault history and command history are session-only. USB port/baud and display preferences are saved separately from DX Caliber.

## Architecture and future integration

`transport.py` owns the byte transport; a future TCP transport can implement the same write/read/close interface. `protocol.py` implements the documented Elecraft protocol and guarded operations. `engine.py` owns the amplifier worker and cached shared state. `server.py` exposes a loopback-only, token-protected service. `index.html`, `app.js`, and `app.css` provide both views; `App.swift` supplies the native window, singleton guard and stay-on-top support.

The compact panel can later be embedded by DX Caliber while this standalone service continues owning amplifier communication. That integration will require an explicit authenticated connection and embedding policy. TCP/IP and DX Caliber integration are architectural provisions, not enabled features in 0.1.2. There is no dependency on DX Caliber or its CAT scheduler.

Protocol source: [Elecraft KPA1500 Programming Reference](https://ftp.elecraft.com/KPA1500/Manuals%20Downloads/KPA1500ProgrammingReferenceV3.pdf). Implementation is independent; no QK4 source was incorporated.

## Validation and build

22 automated tests completed: 21 passed and one macOS pseudo-terminal exclusivity check was skipped because that test device does not enforce USB-style exclusivity. Tests cover framing, units, readbacks, transmit/fault/stale guards, connection generations, cached state, local API isolation, advisory locking and the hardware-observed idle Standby response. Native Full/Compact, Light/Dark and stay-on-top were visually checked with the simulator.

Initial physical USB tests on firmware 03.06 passed for monitoring, RF readings, Operate/Standby, ATU In/Bypass and ATU Tune. See [HARDWARE_TESTS.md](HARDWARE_TESTS.md) for evidence, limitations and remaining tests. The `dist` build uses an ad-hoc development signature. The separate 0.1.2 beta release is Developer ID signed, Apple-notarized and stapled; see RELEASE-0.1.2.md.

Run tests with `python3 -m unittest discover -s tests`. The local packaging script is `scripts/build.sh`; it requires Xcode command-line tools and the configured PyInstaller environment.

## Local 0.1.1 shutdown fix

The native window no longer blocks indefinitely waiting for its service during Quit. Shutdown is asynchronous with a five-second service timeout. The isolated worker uses a stop flag without a process-shared condition lock, releases its transport, and does not wait for undrained disposable state messages. Disconnect closes its queues and bounds worker termination.

Validation: 20 tests (19 passed, one pseudo-terminal skip); three connected simulator service shutdown cycles in the frozen package exited cleanly in about 0.04 seconds each. Native close-button test left no app/service processes or amplifier USB owner. This fix is included in the notarized 0.1.2 beta release.
