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

## Mac harness suite startup correction

Mac retest at `7c1fb7bf4e4147e8e9704dc6d8d4c7f54aa03446` identified a blocking generated-harness startup crash: UserDefaults(suiteName:) was given the app's own bundle ID and its nil result was force-unwrapped. The generator now derives a distinct `<bundle ID>.geometry` suite, records the actual suite in both geometry fields of review-plan.json, and uses guarded optional initialization after identity validation and before creating any window/backend. Suite failure reports an error and returns without fallback. Existing forced simulation, fresh private settings, stable review-only port, named persistent WebKit store and disabled implicit autosaving are preserved. Production Mac wrapper and Windows runtime code remain unchanged.

The Mac agent reported 128/134 Python tests passed with six expected skips, all ten JS suites and native placement passed. Frozen footer checks passed. All six native preference/reopen checks were blocked, not passed, because the generated app crashed. All 66 production fingerprints and decoded geometry values stayed unchanged; a separate production launch explains why the earlier geometry write is not a confirmed isolation defect. Mac launch/reopen acceptance is still required on the corrected harness; see MAC-REVIEW.md.

Suite correction validation on Windows: **136 Python tests: 134 passed, two documented platform skips; all ten JavaScript suites passed.** Nine generator tests passed and a fresh plan/Swift output was inspected. No Mac launch or native preference acceptance is claimed. Production Mac/Windows runtime sources are unchanged; no rebuild of the unchanged Windows runtime was needed. Evidence: `.tmp/mac-suite-fix-tests.log`, `.tmp/mac-suite-fix-generation-check`. No hardware connection, merge or publication occurred.


## Mac acceptance and local-service control guard

The Mac agent completed retesting at `69be2fb4ed9a4b3e56043714a114a66c6619590d`: 136 Python tests (130 passed, six expected skips), all ten then-existing JS suites and native Swift placement passed. The isolated frozen app launched; all six preferences survived two reopen rounds; forced geometry-suite failure exited before a window/backend/listener; all 66 production fingerprints and decoded geometry stayed unchanged. Processes exited cleanly. These Mac results do not establish Windows native close/save acceptance.

One remaining Mac finding is fixed here: a frontend-only local-service outage marker disables Power On and Simulate transmit, as well as operating actions and Connect/Disconnect, after a failed state poll. The control handler also rejects actions while that marker is set. Healthy simulator disconnected/error/powered-off states retain Power On recovery; a fresh successful state response clears the marker and restores state-appropriate controls. Permanent simulation labeling remains. A new JS suite executes the real polling failure/recovery, control renderer and guarded handler, including initial failure, repeated outages and recovery through powered-off/disconnected/error/live states. Actual frozen Mac retesting remains required.

Windows validation: **136 Python tests: 134 passed, two expected platform skips; all 11 JavaScript suites passed.** The frozen Windows build and 57-file notice/module audit passed. First-launch/close-during-save and reopen checks used fresh isolated settings and forced offline simulation. Evidence: `.tmp/service-availability-tests.log`, `.tmp/service-availability-build.log`, `.tmp/service-availability-frozen-01`.

Separate native display acceptance on the previous head observed 100/125/150/200 percent transitions and on-screen recovery, with the original 125 percent restored. Compact retained logical size. A Full-view edge case remains unresolved: after 200 percent clamping and minimizing, returning to 125 percent retained enlarged physical bounds and persisted the enlarged logical size. The non-clamped Full control case remains unestablished. Evidence: `.tmp/native-scale-69be2fb/acceptance-summary.json`. This outage fix does not resolve that sizing finding; physical multiple-monitor acceptance also remains pending. No hardware connection, merge or publication occurred.


## Minimized Full-view DPI sizing fix (review branch)

Reproduced the separate Full-view growth finding with actual Windows Display Settings and a fresh isolated simulator profile. The ignored diagnostic source host only added native-event logging and internal minimize/restore/resize controls; no renderer emulation or hardware connection was used. The trace showed two restore orderings: WM_DPICHANGED can arrive while minimized or after WM_SIZE already reports Normal. Windows may suggest nearly the old physical size, and its outer restore operation can later overwrite a corrected WinForms Bounds assignment.

The Windows hook now captures normal restore dimensions at minimization before default native processing, scales them from the captured DPI to the new DPI, and passes corrected bounds through the DPI notification. A guarded UI callback applies fitted physical bounds with SetWindowPos after the native restore stack unwinds, without activation or Z-order change. A later DPI/view/user-resize change invalidates obsolete queued corrections. Deferred/disposed-window failures are logged rather than escaping the UI callback. Pending bounds preserve logical close sizes if the window stays minimized. Ordinary normal/maximized suggestions retain the existing behavior; explicit Full/Compact changes discard outdated restore corrections. Mac runtime and shared JavaScript/backend are unchanged.

Actual native acceptance passed: clamped Full at approximately 1918x1198 physical pixels/200 percent restored to 1199x749 at 125 percent, within one pixel of the preserved logical size; the former 1920x1200 expansion no longer persisted. A non-clamped 700x500 logical Full window restored while minimized in both directions: 1400x1000 at 200 percent and 875x625 at 125 percent. It saved full_size [700,500] and reopened at 875x625. The original 125 percent scale was restored and Display Settings closed. Simulation remained permanent, with sharing and auto-connect disabled.

Validation: **149 Python tests: 147 passed, two expected platform skips; all 11 JavaScript suites passed.** Thirteen new DPI regressions cover clamped/non-clamped and Compact dimensions, event ordering, deferred native overwrite, pending close dimensions, invalidation, fitting, native flags/failure and safe UI error handling. The final frozen build and 57-file notice/module audit passed. Existing native close/save/reopen and maximized Compact/Full frozen smoke checks passed on the rebuilt Windows candidate (both process exits zero); actual frozen display-scale transitions are not claimed by the source-host native reproduction. Physical multiple-monitor acceptance remains pending.

Evidence: `.tmp/dpi-diagnose/events.jsonl`, `.tmp/dpi-diagnose/acceptance-summary.json`, `.tmp/dpi-restore-tests.log`, `.tmp/dpi-restore-build.log`, `.tmp/dpi-restore-frozen-final`. The fix is prepared on the existing review branch for review; no hardware connection, merge or publication occurred.


## Final Mac acceptance and affected-scale packaged acceptance

The Mac agent completed the outage-control retest at exact commit `660f6270420bae208e1ab5e1bea179103cadfad5`: 136 Python tests (130 passed, six expected platform skips), all nine generator tests, all 11 JavaScript suites and native Swift placement passed. Frozen startup and healthy simulator recovery passed; outage controls disabled correctly in Full/Compact with readings cleared and permanent simulation labels retained. All six preferences survived two actual reopen rounds. All 66 production fingerprints and decoded geometry were unchanged; review processes exited. Automated same-window polling recovery/no command replay and actual packaged close/reopen recovery were reported separately as passed. No new Mac failure was reported.

The DPI follow-up changes only `Sources/windows_app.py`, `Sources/windows_dpi.py`, Windows regression tests and this status document. Shared JavaScript/backend, production Mac Swift/build, Mac harness generator and dependencies are unchanged from the Mac-tested head. The necessary Mac follow-up is a diff-scope check plus offline Python/JavaScript/native-placement regressions at the new review head. A repeat of the full native Mac preference/outage acceptance is not required by this Windows-only runtime change unless that check finds a shared change or regression; the previous acceptance remains tied to its exact commit.

The final packaged EXE was additionally tested at actual 200 percent display scaling: first launch and reopen both exited zero, exercising Full/Compact, maximized-to-Compact-to-Full recovery, native preference persistence, and close during an in-flight save. Its Full size saved as [960,600] logical pixels. After restoring the original 125 percent display setting, the same profile reopened successfully and repeated those checks without logical-size inflation. The prior clamped/non-clamped minimized DPI transitions were native source-host tests with diagnostic instrumentation; these additional packaged checks establish Full/Compact and close/reopen at both affected scaling settings, not an uninstrumented frozen same-process DPI transition test. Physical multiple-monitor acceptance remains pending.

Evidence: `.tmp/dpi-affected-scales/200-first.smoke.json`, `.tmp/dpi-affected-scales/200-reopen.smoke.json`, `.tmp/dpi-affected-scales/125-cross-scale-reopen.smoke.json`, together with the preceding native event traces and 149-test/11-suite regression results. Keep PR #2 unmerged pending review; hardware testing remains disabled.


## Maximized restore follow-up

Final review at `ed5ad1c7b97c70ef26d55a84a90a60a40fb94c6a` found a distinct remaining case: maximize at 200 percent, minimize, change to 125 percent and restore Maximized. The visible maximized window filled the screen, but the corrected normal bounds were discarded because keep_visible returned early. Native normal logical size grew from [959,599] to [1534,958], and closing persisted the enlarged dimensions.

The Windows sizing coordinator now preserves corrected normal geometry separately while Maximized, retaining the native maximized DPI suggestion. Closing and Full/Compact use the pending normal size. A later normal WM_SIZE applies the retained bounds and queues a guarded native correction after restore completes. Further DPI/minimize cycles rescale retained geometry rather than stale WinForms RestoreBounds. User resize/view changes invalidate pending geometry and queued corrections.

Native source-host acceptance repeated the actual 200-to-125 percent sequence: normal logical size stayed [959,599] while the visible window remained Maximized. Closing from Maximized saved [959,599]. Reopening at 125 percent produced 1198x748 physical pixels ([958,598] logical due to existing integer pixel rounding, within one logical pixel); Compact was 512x675 physical; the final Full roundtrip retained [958,598] logical pixels (1197x747 physical, within one physical pixel of reopened bounds). All testing used a fresh forced-simulation profile, with no hardware access. Original 125 percent scaling was restored and Display Settings closed.

Offline validation: **157 Python tests: 155 passed, two expected platform skips; all 11 JavaScript suites passed.** Eight new regressions cover maximized persistence, normal restoration/deferred native overwrite, Full/Compact, successive DPI changes, re-minimizing, user-resize invalidation, post-default native notification ordering and a 20-cycle fractional-DPI view roundtrip. Native size capture rounds physical bounds instead of using pywebview's floored logical getters, preventing cumulative view-size shrink. The build and 57-file notice/module audit passed.

**Final frozen acceptance passed:** the final rebuilt EXE started normally and both first-launch and reopen smoke runs exited zero, including Full/Compact, maximized Compact/Full restore, serialized preference persistence and close during an in-flight save. An intermediate build had been rejected before startup by Windows Application Control (Code Integrity event 3077, unsigned image did not meet the policy signing requirements); no policy/security settings were changed or bypassed. The final artifact passed by ordinary execution. Its SHA256 is `6bc0cc57a9bdb69a062c45077c108527799374897c4d39163a2c7b49e231c7fd`. Native same-process scale transitions used the isolated instrumented source host; packaged smoke tests are separate and do not establish uninstrumented frozen same-process DPI-transition acceptance. Physical multiple-monitor acceptance remains pending.

Changed scope is Windows wrapper/DPI code, Windows tests and this document only. Shared JavaScript/backend, Mac Swift/build, Mac harness generator and dependencies remain unchanged. Mac compatibility acceptance at ed5ad1c remains recorded separately (143/149 Python passes, six skips; all 11 JS suites and Swift placement passed; production fingerprints unchanged). No hardware connection, merge or publication occurred. PR #2 remains a draft pending review and explicit merge authorization.

Private evidence: `.tmp/maximized-dpi-final-native` repeats the maximized DPI sequence and close/save using the exact final source hashes; `.tmp/maximized-dpi-fix` records native reopen and Full/Compact snapshots; `.tmp/maximized-dpi-frozen-final` records final packaged acceptance; `.tmp/maximized-dpi-fix-tests.log`, `.tmp/maximized-dpi-fix-build.log`. Native diagnostic instrumentation is ignored and not part of the reviewed runtime.
