# KPA1500 Control 0.1.7

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

DX Caliber 0.6.67 can display a read-only accessory widget using the optional local feed while this standalone service continues owning amplifier communication. Embedding an operational panel later would require an explicit authenticated connection and embedding policy. TCP/IP remains planned. There is no dependency on DX Caliber or its CAT scheduler.

Protocol source: [Elecraft KPA1500 Programming Reference](https://ftp.elecraft.com/KPA1500/Manuals%20Downloads/KPA1500ProgrammingReferenceV3.pdf). Implementation is independent; no QK4 source was incorporated.

## Validation and build

22 automated tests completed: 21 passed and one macOS pseudo-terminal exclusivity check was skipped because that test device does not enforce USB-style exclusivity. Tests cover framing, units, readbacks, transmit/fault/stale guards, connection generations, cached state, local API isolation, advisory locking and the hardware-observed idle Standby response. Native Full/Compact, Light/Dark and stay-on-top were visually checked with the simulator.

Initial physical USB tests on firmware 03.06 passed for monitoring, RF readings, Operate/Standby, ATU In/Bypass and ATU Tune. See [HARDWARE_TESTS.md](HARDWARE_TESTS.md) for evidence, limitations and remaining tests. The `dist` build uses an ad-hoc development signature. The separate 0.1.3 beta release is Developer ID signed, Apple-notarized and stapled; see RELEASE-0.1.3.md.

Run tests with `python3 -m unittest discover -s tests`. The local packaging script is `scripts/build.sh`; it requires Xcode command-line tools and the configured PyInstaller environment.

## Local 0.1.1 shutdown fix

The native window no longer blocks indefinitely waiting for its service during Quit. Shutdown is asynchronous with a five-second service timeout. The isolated worker uses a stop flag without a process-shared condition lock, releases its transport, and does not wait for undrained disposable state messages. Disconnect closes its queues and bounds worker termination.

Validation: 20 tests (19 passed, one pseudo-terminal skip); three connected simulator service shutdown cycles in the frozen package exited cleanly in about 0.04 seconds each. Native close-button test left no app/service processes or amplifier USB owner. This fix is included in the notarized 0.1.2 beta release.

## Application icon

0.1.3 adds the custom graphite/mint gauge icon with amber needle and RF waveform. Assets contains the high-resolution PNG, macOS ICNS and seven-size Windows ICO; Windows packaging remains future work. Run `python3 scripts/build_icons.py` on macOS to regenerate icon containers. See RELEASE-0.1.3.md.

## DEV 0.1.4 — read-only Logger accessory feed

Full view → Connection → **Share readings with DX Caliber** enables a local, read-only `/api/v1/telemetry` feed on port 51980. It is off by default, remembers the choice, and shares only cached measurements/status (including simulator labeling); it exposes no USB settings, history, credentials or operating controls. The standalone app remains the only amplifier reader. Turning sharing off immediately returns HTTP 403. DX Caliber can show one accessory widget and open the full application; it cannot operate the amplifier through this feed.

The DEV build is local and ad-hoc signed; the published notarized beta remains 0.1.3. Automated simulator/API checks passed, including sharing opt-in/opt-out/persistence, no reader started by telemetry, shutdown and existing control guards. No new hardware test was performed for this change.

### Meter range colors (local 0.1.5)

Full and Compact views use anchored, blended green/yellow/red scales: temperature
65/66 and 85/86 C boundaries; SWR blends around 1.5 and just above 2.1; forward
power blends around 1400 and just above 1500 W. Power scale includes headroom to
2000 W, temperature to 110 C. Numerical values remain visible with separate
Light/Dark text palettes; stale/missing values have no active color. These are
presentation thresholds only and never alter amplifier protections or commands.
Local simulator visual checks and color/boundary tests passed; 22 engine/control
tests passed with one skipped. USB reader and CAT architecture are unchanged.

0.1.6 — Optional Station callsign in Connection, saved with local view preferences.
A title badge remains visible in Full and Compact views and both themes; blank
values hide the badge. Display only: no amplifier, single-reader or shared-feed
changes. Browser UI verified lowercase normalization, compact visibility and
reload persistence with equipment disconnected.

Window placement update: preserve valid display positions; recover windows after display changes, activation/reopen, and Full/Compact transitions. Error alerts attach to the main window. Full-screen placement is left to macOS. Reader, telemetry and CAT behavior are unchanged. Native placement checks: compile Sources/WindowPlacement.swift with tests/window_placement.swift and run the resulting test executable.

## Release 0.1.7

Consolidates DX Caliber sharing, meter colors, callsign badge and window recovery in a signed, notarized Apple Silicon beta. See RELEASE-0.1.7.md. USB remains the hardware connection; TCP/IP is planned separately.
