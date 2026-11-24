# DXC Operate / Standby sharing

Based on the exact Windows Build 31 snapshot (b2e02b25d6743b2865a4601d622bd343e2bb7e2e plus the supplied Build 31 overlay). No startup, USB, transport, deadline, native placement, or protocol behavior was replaced.

In Connection, first enable Share readings with DX Caliber, then separately enable Share Operate / Standby controls with DX Caliber. Control sharing defaults off, is persisted, and is revoked if reading sharing is disabled. Offline and read-only modes cannot send shared controls.

GET /api/v1/controls returns cached capabilities and a backend-only session token. POST requires the exact loopback Host, no browser Origin, X-KPA-Feed-Token, a unique request ID, current generation and expected mode. Only operate and standby are allowed. Duplicate receipts are not re-executed. Existing worker freshness, RF, tuning and control guards remain authoritative. Requests are never automatically retried or replayed on reconnect.

DXC renders two compact buttons in the existing Logger accessory footer beside Open full app. Selected mode is derived from telemetry. Missing sharing, stale or inconsistent readings, pending requests and unavailable capabilities disable buttons. No new hardware connection is opened.

The mode sharing source is shared Python/HTML/JS and is portable to Windows. This change is prepared locally; it has not been pushed or merged into the Windows branch. Build 34 also adds separate opt-in power sharing; see DXC-POWER-SHARING.md.

Local Mac Build 34 is 0.1.27, arm64 and ad-hoc signed for local testing. It includes the Build 33 receipt fix.

Build 33 receipt fix: keep up to 128 spent request IDs for the entire backend-token/session lifetime. At capacity, reject every new ID with an explicit restart message; identical duplicate IDs still return their original receipt. Rejected/uncertain requests cannot evict an earlier receipt. Restarting creates a new token and connection generation; old requests are not replayed.
