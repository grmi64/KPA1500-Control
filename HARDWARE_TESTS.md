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
