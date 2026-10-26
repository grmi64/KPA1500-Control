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
