# Windows port status: dependencies, discovery and native host

Baseline: `5427161b96dbcaec1373274b8f49d249df31876f` (audited Mac 0.1.25). Review branch `codex/windows-port` contains the initial Windows port for PR review. The validation notes below record the offline checks performed before committing. Checkout is outside OneDrive at `C:/Users/gmill/source/repos/KPA1500-Control`.

## Completed for offline review

- Dedicated KPA Python 3.12 environment with pinned dependencies, including pyserial 3.5, PyInstaller 6.22.3, pywebview 6.2.1 and pythonnet 3.2.1. The new bundle no longer uses OM's development environment.
- Complete frozen serial/native dependencies, 57 pinned license/notice/source files, module-root mappings and binary-hash audit. The pyserial wheel omits its license, so the v3.5 license text was fetched from the official tagged source. Existing OM dependency notice texts were reused only for matching versions/binary hashes; no OM application licensing assertion was copied.
- Platform-specific serial transport, passive COM listing/COM10+, bounded I/O, failed-open cleanup, kernel/cooperative exclusivity and portable TCP endpoint leases. Shared protocol, power implementation and command guards remain unchanged.
- Windows local-subnet provider with metric-based default-interface selection, direct-gateway validation, /24 maximum scan scope and at most 254 TCP targets. Cancellation/progress/manual fallback retained. No blind USB identity probes.
- Synthetic discovery in the native offline review, including progress, cancel, selection and explicit Connect; simulation never enumerates or opens hardware.
- Native Full/Compact, Light/Dark, stay-on-top, persistent view preferences, saved full-window size/position, display-change/activation recovery, PerMonitorV2 DPI handling and About/version. Preferences persist across random loopback origins and process restarts.
- Authenticated loopback activation of the existing review identity; an actual second process exits without replacing or creating another simulator reader. Graceful app/controller/server/discovery shutdown releases the instance metadata/lease.
- Missing-WebView2 preflight and error guidance before any controller/server starts. All native object references remain private to the Python bridge.

## Validation

Windows 11 build 26300, AMD64; Python 3.12.14. **127 Python tests: 125 passed, 2 skipped. All 10 JavaScript suites passed.** The skips are POSIX pseudo-terminal exclusivity and POSIX SIGTERM semantics; Windows fake-serial/cross-process exclusion and native graceful-close tests provide the Windows alternatives. Mac execution was not performed here.

Source and frozen actual-WebView2 smoke tests passed, followed by source/frozen reopen checks with saved preferences. Coverage includes Full/Compact, Light/Dark, native stay-on-top, simulated mode/fan/tune/cancel/RF/power controls, Standby, About/version, actual second-process activation without reader replacement, synthetic discovery progress/cancel/select, saved theme/meter/callsign/section settings, pyserial 3.5 import, and stale/error blanking/control disabling. These are simulation results, not Windows hardware acceptance.

The frozen-only activation regression was diagnosed and fixed: the generic URL opener unnecessarily created an HTTPS context for local HTTP activation. Activation now uses a bounded direct HTTP connection exclusively to the validated 127.0.0.1 endpoint; no external connection or TLS-validation bypass is used. Settings/metadata paths are made absolute before GUI initialization.

The notice audit passes all 57 pinned notice/source hashes, frozen module mappings and the exact binary inventory. Private evidence is ignored under `.tmp/native-final-02`, `.tmp/frozen-final-01` and `.tmp/completed-review-build.log`. A machine-readable summary and source hashes are in `.tmp/windows-complete-validation.json` and the review bundle.

Artifact: `dist/windows/KPA1500 Control Review/KPA1500 Control Review.exe`; keep the entire folder. It remains unsigned and **simulation-only**. See WINDOWS.md for usage.

## Remaining release and hardware gates

- Confirm application distribution license with owner; sign/release and Store packaging are separate work. No distribution/license approval is inferred from third-party notices.
- Clean-PC/Sandbox acceptance and physical multiple-monitor checks remain separate. Automated geometry/DPI recovery tests pass; no second physical monitor was available.
- Mac regression execution/review is required before merging shared adapter/bridge changes. Mac packaging and protocol/command-guard sources have not been modified.
- Windows serial hardware, real TCP discovery, read-only USB/TCP monitoring and all operating/RF/power/fan/ATU acceptance remain untested. They require separate explicit approval. The desktop review host remains offline-only; no hardware session is enabled by this milestone.

No real device was opened, no local-subnet scan was executed, and no amplifier/radio commands were sent. Only dependency/license downloads used Internet. No production app/settings were copied or replaced. No commit, push, merge or publication occurred. The operator alone supplies/stops RF and sets radio drive.

## Pre-commit review fixes verified

All three findings from the Windows pre-commit review have been fixed without committing or changing hardware access:

1. Maximized/minimized Full windows now use normal RestoreBounds converted from physical to logical pixels before Compact; transitions normalize WindowState before resize. Closing also saves normal restore dimensions instead of discarding or replacing them with maximized dimensions. Mocked multi-DPI regressions and actual source/frozen maximized Compact/Full transitions pass (one-pixel tolerance for Windows logical/physical rounding).
2. Windows JS bridge updates capture an immutable preference snapshot and serialize native display updates plus persistence in one Promise chain. Deferred-call regressions prove later choices cannot overtake earlier writes, nested preference snapshots remain stable, and a failed save is reported without blocking subsequent updates. Mac WebKit messaging is unchanged.
3. Controller snapshots explicitly identify permanent offline-only sessions. Clear/disconnect/error preserve the demo marker; the UI uses the session marker as well as the current reading marker, retaining badge/banner even when local-service errors replace the state object. Readings still clear and controls remain disabled. Normal hardware sessions are not mislabeled.

Final validation: **127 Python tests: 125 passed, 2 documented platform skips; all 10 JavaScript suites passed.** Source and frozen first-launch/reopen checks pass, including the three added regressions and actual duplicate-process activation. The dependency notice audit still passes all 57 files and the binary/module inventory.

Private evidence: `.tmp/three-fixes-source-03`, `.tmp/three-fixes-frozen-01`, `.tmp/three-fixes-final-build.log`, `.tmp/windows-review-fixes-validation.json`. No hardware connection, network discovery scan, commit, merge or publication occurred.

## Close-during-save review fix verified

The remaining P2 is fixed. Native Close is initially cancelled while a background coordinator asks JavaScript to freeze further preference updates and finish the existing save queue. WinForms stays responsive; after successful persistence, the coordinator retries Close and saves geometry on the UI thread. Repeated close clicks do not create duplicate flushes. Save errors, geometry-write errors and an eight-second flush timeout leave the app open and restore interaction with an error. A later Close retries a failed preference write once; no amplifier operation is retried. Startup closing before the page loads requires no JavaScript flush.

The exact prior offline reproduction now requests Light last and persists Light, rather than Dark. Five new Python lifecycle regressions and extended JavaScript tests cover success, repeated clicks, timeout/late callbacks, failure, retry and freezing additional updates. Source and frozen real-WebView2 checks deliberately hold the first preference save in flight, enqueue a later choice, close without a test-side drain, then verify the latest value on disk. Frozen reopen repeats the same check successfully. Processes exited cleanly.

Latest validation: **127 Python tests: 125 passed, 2 documented skips; all 10 JavaScript suites passed.** The 57-file dependency notice/binary/module audit passed. Evidence: `.tmp/review-close-result.json`, `.tmp/close-fix-source-01`, `.tmp/close-fix-frozen-01`, `.tmp/close-fix-build.log`, `.tmp/windows-close-fix-validation.json`.

All validation remained offline in simulation. The reviewed changes are being committed to the review branch for a PR; no hardware connection, merge or publication is authorized. The previously documented clean-PC, physical-monitor, Mac and hardware acceptance gates remain separate.

## Mac review follow-up and Sandbox acceptance

The Mac agent tested exact commit `74547049d6ad916b1bcf1692cf66b33417e6175b` on macOS 27.0.1 arm64: 127 Python tests (121 passed, six expected skips), all ten JavaScript suites, native placement tests and a separate frozen simulator passed. Three follow-ups are recorded in MAC-REVIEW.md.

The simulator footer now shares the permanent simulation decision used by the badge/banner, including local-service failure where state.demo is absent. Rendering regressions cover those states and preserve normal USB/TCP wording.

Mac random-port preference persistence uses an explicitly documented harness-only solution: a generated private Swift wrapper with a fixed non-production review port, forced simulator/fresh settings, a fresh persistent named WebKit store, and an explicit review-only geometry domain. This deliberately leaves the production Swift wrapper unchanged. Seven Python generator regressions pass; Mac compilation, actual preference reopening and preservation retest are pending. See MAC-REVIEW.md for exact build/retest instructions.

The production geometry-plist hash change reported on Mac has no established cause. Static audit found no explicit writer targeting another preference domain. Generated review geometry no longer uses implicit standard-domain autosave; this is isolation hardening, not proof of the previous cause. Mac retesting must retain decoded before/after geometry and process evidence without overwriting production preferences.

Windows fresh Sandbox first-launch/reopen and separate standard-user simulation acceptance passed on the original PR commit. The standard account had no administrator token and no app-folder write access; per-user settings, simulated controls and close-during-save passed. Networking was disabled. A setup coordinator's unavailable secondary-logon runner exit code was documented separately; both tested app exits were zero and the completed standard-user report passed. These results apply to that tested commit, not automatically to future builds.

Current offline regressions: **134 Python tests: 132 passed, two documented skips; all ten JavaScript suites passed.** No hardware connection, merge or publication occurred. Physical multiple-monitor, distribution licensing and hardware acceptance remain separate gates.

The follow-up Windows frozen build and notice audit passed; fresh first-launch/close-during-save and reopen smoke checks both exited zero. Evidence: `.tmp/mac-review-fixes-tests.log`, `.tmp/mac-review-fixes-build.log`, `.tmp/mac-followup-frozen-01`. Mac harness generation is tested here; actual Swift compilation and Mac preservation/reopen acceptance remain pending.
