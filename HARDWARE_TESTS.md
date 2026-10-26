# Hardware validation — October 20, 2026

App: KPA1500 Control 0.1.0, local macOS build. Amplifier firmware: 03.06. Transport: Host PC USB at 230400 baud. These results reflect a short initial bench session, not long-duration qualification.

| Check | Result and evidence |
| --- | --- |
| USB identity and monitoring | Passed. Amplifier identity/firmware, frequency, temperature, voltage, power, antenna, ATU and mode populated from hardware. |
| Monitoring stability | All 30 one-second cached-state samples were LIVE, with no protocol errors; maximum reading age was approximately 0.535 seconds. |
| Serial ownership | OS inspection showed only this app's amplifier worker owning the amplifier port. Elecraft utility was not running. DX Caliber CAT and PowerMaster remained on separate ports. Deliberately competing USB opens were not tested. |
| Applied RF | User applied RF and confirmed responsive meters with good data. No calibrated accuracy comparison was performed. |
| Operate → Standby → Operate | User confirmed both directions after the Standby parsing fix below. |
| Next antenna | Two requests returned antenna 1. User confirmed only one antenna is enabled on 15m, explaining the unchanged selection. Multi-antenna cycling remains unverified. |
| ATU In / ATU Bypass | Both confirmed working by user. |
| ATU Tune | User confirmed successful tune, followed by successful transition to Standby. |
| Cancel Tune | Pending physical test during an active tune. Software/simulator coverage exists. |
| Fault display and clear | Pending physical verification. Software tests cover fault gating and temperature-fault persistence. Do not deliberately create high SWR, overdrive or overheating for testing. |

## Standby fix

Hardware returned this diagnostic state while idle in Standby:

```
TR inhibit x01 TR_STATE_PA_BYPASSED_3R_ON 3R:1 3T:0 Bias:0 PA STBY KeyIn:0 MODE_STBY
```

The initial parser recognized only `TR_STATE_RX` as idle, so Standby displayed RX/TX UNKNOWN and disabled Operate. The parser now recognizes the specific bypassed Standby state only with receive relay on, transmit relay off, bias off, explicit Standby mode and key input off. Explicit transmit/key indicators take precedence. Other unrecognized states remain unknown and blocked. Every operating command still rechecks current hardware status and RF power before sending.

Regression coverage includes the observed frame, keyed/transmit variants, unexpected bias, missing key input and conflicting RX/TX indicators. The rebuilt app was reconnected, showed LIVE/Standby with Operate enabled, and the user verified switching in both directions.

## Remaining scope

Cancel Tune, naturally occurring fault handling, multi-antenna cycling, extended-duration monitoring and competing-reader behavior need hardware verification. TCP/IP and DX Caliber embedding are future work. No radio CAT commands are issued by this application.

## TCP transport read-only verification — 2026-10-25

New TCPTransport connected to 192.168.0.18:1500 three times. A wrapper enforced a GET-only allowlist before any byte write; Session.identify and full fast/slow polling returned LIVE, firmware 03.06, Standby, 0 W and 25 C with no query errors. 21 queries per connection took 0.008–0.010 seconds in this brief sample. Each socket was closed. No SET/control/tuning/power/radio commands sent. Operating controls over TCP and sustained/recovery hardware testing remain pending.

## Installed TCP monitoring check — 2026-10-25

Operator approved installation of signed 0.1.8 and selection of TCP/IP at
192.168.0.18:1500. Previous installed 0.1.6 app/settings backed up under
backups/before-0.1.8; USB port/baud retained in saved connection settings.
Initial installed-app connection failed with macOS error 65 (No route to host),
while a direct read-only query still reached the device. Operator handled the
local-network permission dialog; System Settings showed KPA1500 Control allowed.
After restarting the app and explicitly retrying Connect, native UI showed LIVE,
TCP/IP endpoint, firmware 03.06, Standby, 0 W, antenna 1 and ATU bypass.
No operating, tuning, power, radio-keying or drive-power commands were sent.
This local build remains unpublished. macOS Local Network access must be enabled
for the app; an initial failed attempt does not automatically retry.

Twenty cached telemetry samples over twenty seconds all remained LIVE, maximum
sample age 0.216 seconds, Standby and 0 W throughout. DXC widget feed was LIVE
with matching readings. OS inspection showed one established TCP connection to
192.168.0.18:1500 and no owner of the previous USB port. A further native app
quit/relaunch automatically restored the saved TCP connection to LIVE, without
manual Connect. No operating actions were invoked.

## TCP Operate/Standby — 2026-10-25

Operator explicitly authorized Operate/Standby using installed 0.1.8 on TCP/IP
192.168.0.18:1500. Initial fresh telemetry showed Standby, no transmit, 0 W.
Native app Operate button produced one confirmed action (Operate confirmed),
with fresh operate=true, transmitting=false, 0 W and fault 00. Native Standby
button then produced one confirmed action (Standby confirmed). Final fresh
readback: LIVE, operate=false, transmitting=false, 0 W, fault 00; DXC feed LIVE
and Standby. Action history shows exactly one confirmed Operate and one
confirmed Standby for this test. No tuning, power, radio-keying or drive-power
commands sent. No application/source behavior changed for this test.

## TCP RF power/SWR — 2026-10-25

Operator supplied/stopped RF and selected amplifier mode. Operator front-panel
comparison: approximately 980 W and SWR 1.1, then returned to Standby.
Read-only local recording captured 1,147 samples over 294.1 seconds, including
33 amplified-RF samples: forward 900–993 W, reflected 3–4 W, SWR 1.1.
DXC active-RF samples showed 900–990 W and SWR 1.1. The two cached feeds refresh
independently; these ranges are not a claim of identical simultaneous samples.
All amplifier samples remained LIVE; maximum reported age 0.263 seconds, no
reported fault. Final app and DXC feeds LIVE, Standby and forward/reflected 0 W.
No amplifier or radio commands were sent by the observer during this test.
Evidence: test-evidence/tcp-rf-2026-10-25.jsonl and corresponding summary JSON.

## TCP cable loss and recovery — 2026-10-25

Operator kept radio idle, unplugged amplifier LAN with USB still connected, then
restored LAN on request. Installed 0.1.8 native app showed ERROR and unknown
readings; API cleared power, SWR, temperature, operate and transmit state to null.
All operating/ATU/fault controls disabled. DXC showed error without meter values.
No fallback to USB occurred. Restoring LAN alone left app disconnected/error;
previous four completed actions remained unchanged. One explicit native Connect
restored LIVE TCP readings: Standby, receiving, 0 W, fault 00. DXC also LIVE.
Connection generation/action history reset, no new operating requests queued.
No operating, tuning, power or radio commands issued for this test.

Limitation: initial ten-minute recorder expired before cable removal, so exact
live-to-stale/timeout delay was not captured. Disconnected and recovered states
are separately saved in test-evidence/tcp-loss-disconnected-2026-10-25.json and
tcp-loss-restored-2026-10-25.json. UI issue found: previous completed-action text
(Standby confirmed) masks the disconnection error message; error badge, blank
readings and control disabling remain correct. The message resets on Connect.

## 0.1.9 timed LAN-loss retest — 2026-10-25

Installed signed 0.1.9 with prior app/settings backup. Recorder sampled cached app and DXC feeds at approximately 0.25-second intervals. After operator unplugged LAN with USB still connected, both feeds cleared readings about 2.58 seconds after the last fresh amplifier sample. App ERROR appeared about 9.52 seconds after that sample; DXC ERROR about 9.77 seconds. Times are relative to the last measured sample, not an independently timed physical unplug. Native UI displayed the connection-closed/reconnect message, unknown readings and all operating controls disabled. The offline regression separately covers priority over a previous completed action.

Operator restored LAN; app remained disconnected with no queued actions. One explicit Connect restored LIVE TCP and DXC readings, Standby, receiving, 0 W and fault 00. No mode, tuning, power, radio-keying or drive-power commands were issued for this retest. Local raw evidence remains excluded from source distributions under test-evidence/.

## TCP ATU In/Bypass — 2026-10-25

Operator authorized ATU In → Bypass only on installed 0.1.9 over TCP/IP.
Initial fresh state: Standby, receiving, 0 W, not tuning, fault 00, ATU bypass.
Native ATU In button returned one confirmed atu_in action; amplifier readback
showed atu_enabled=true and, after relay/readback refresh, atu_inline=true.
Native ATU Bypass returned one confirmed atu_bypass action; final readback
atu_enabled=false, atu_inline=false, Standby, receiving, 0 W, not tuning,
fault 00. DXC feed remained LIVE and showed ATU bypass. No Tune/Cancel Tune,
mode, power, radio-keying or drive-power commands sent for this test.

## TCP ATU Tune — 2026-10-25

Operator confirmed clear frequency, intended antenna and tuning readiness at
21.366 MHz; authorized one Tune request. Initial state Standby, RF off,
ATU bypass, no fault. Native ATU In confirmed, then native ATU Tune confirmation
sent one request. Action history contains exactly one tune action, confirmed.
Cached telemetry captured tuning=true, then tuning=false; approximately 18.46
seconds of sampled tuning-active state included waiting for operator RF.
Operator supplied RF after NEED TUNE PWR / Key Exciter appeared. Sampled power
peaked at 15 W; observed SWR values 2.0, 1.7, 1.5, 1.2 and 1.1. No faults.
Operator confirmed front panel completed the tune successfully and RF was off.
Final fresh state LIVE, Standby, receiving, not tuning, 0 W, ATU enabled/inline,
fault 00; latest idle SWR reflects the previous RF sample (about 1.2).
No radio CAT, keying or drive-power command was sent by the app/observer;
operator controlled RF. No second tune or Cancel Tune request sent.
“Tune confirmed” reports start acknowledgement; final successful completion here
is established by the tuning transition plus operator front-panel confirmation.
Cancel Tune remains untested over TCP. Local evidence stored under test-evidence/.

### TCP Cancel Tune — 2026-10-25

With RF off in Standby, enabled ATU, started one tune, and clicked Cancel tune once after tuning became active. Subsequent telemetry confirmed tuning stopped, 0 W, no transmit indication, and fault 00. No Cancel retry or second Tune was sent. The immediate action readback reported unconfirmed before the following telemetry showed tuning=false; this is a confirmation-timing issue requiring a bounded readback fix without command replay.

Operator observed both IN and BYP LEDs illuminated. Elecraft KPA1500 Programming Reference V3 (^AI) documents this combination when ATU mode is enabled but the actual relay setting is bypassed; cached telemetry matched atu_enabled=true and atu_inline=false. Restored ATU Bypass once, confirmed. Final state LIVE, Standby, ATU disabled and bypassed, tuning=false, transmitting=false, forward power 0 W, fault 00. No radio keying, drive-power or amplifier power commands sent.

Local evidence: test-evidence/tcp-atu-cancel-2026-10-25.jsonl and tcp-atu-cancel-final-2026-10-25.json.

### TCP Cancel Tune confirmation retest — 0.1.10, 2026-10-25

Installed signed 0.1.10/build 11. Started from LIVE Standby, ATU Bypass, RF off. Sent ATU In once, Tune once, then Cancel tune once after telemetry showed active tuning. UI displayed "Cancel tune confirmed."; cached backend action also confirmed, with tuning=false, transmitting=false, forward=0 W, operate=false and fault=00. No retry was sent. Restored ATU Bypass once; UI confirmed and showed Bypassed relay state, Standby and 0 W. No radio keying, drive-power or amplifier power commands sent. Local evidence: test-evidence/tcp-cancel-confirmed-0.1.10.json. Hardware cancellation and confirmation now pass. Nothing published.

### Explicit antenna selectors — 0.1.11, 2026-10-25

Replaced Next antenna with Ant 1 / Ant 2, highlighting only the reported live selection. Current selection cannot be resent. Both visible in native full and compact views. Offline: 37 Python tests (36 pass, one expected platform skip), four JavaScript suites pass, including selection highlighting and disabled RF/tuning/stale/queued states. Signed build 12 installed locally.

Hardware: initial LIVE Standby, RF off, Ant 1, ATU Bypass on 15m. Clicked Ant 2 once. Amplifier stayed on Ant 1; app reported unconfirmed and retained Ant 1 selection. Operator confirmed Ant 2 is disabled on 15m, consistent with documented ^AN behavior refusing disabled antennas. No configuration changes or retries. A successful Ant 2 / Ant 1 switching check remains pending on a band with both enabled. Restored compact view. No power, mode, tuning, radio keying or drive-power commands sent. Nothing published.


### Antenna switching passed — 0.1.11, 2026-10-25

Operator corrected 15m antenna configuration to enable both ports (previously only Ant 2 was enabled). With LIVE Standby and RF off, selected Ant 1, Ant 2, then Ant 1 once each. All three actions confirmed; selected highlight followed reported state. Operator independently confirmed each antenna on the amplifier front panel. Final Ant 1, Standby, ATU Bypass, 0 W, no fault. Evidence: test-evidence/tcp-ant-selectors-0.1.11.json. No power, mode, tuning, radio keying or drive commands sent. Nothing published.
