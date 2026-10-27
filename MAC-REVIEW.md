# Offline Mac review of the Windows port

PR #2 initially passed the Mac command-guard and simulator checks at commit `74547049d6ad916b1bcf1692cf66b33417e6175b`, but review found a random-origin preference reset, an inconsistent simulator footer, and an unexplained production geometry-plist hash change. The retest below addresses these separately. No hardware, merge, installation, submission or publication is authorized.

## Preference persistence: explicitly harness-only solution

The production Mac UI stores view preferences in WebKit localStorage. Its origin includes scheme, host and port; the per-process token path does not change the origin. A backend started with `--http-port 0` therefore gets a new preference store on each launch. This is an isolation-harness limitation, not evidence of a fixed-port production Mac regression or a Windows close/save failure.

Keep `--http-port 0` for standalone backend automation. For the **native Mac preference/reopen acceptance only**, use a dedicated stable review port, normally **51981**. This explicitly replaces the previous requirement to use port 0 for that harness. Never use production port 51980. If 51981 is occupied, choose another unused non-production port when generating the harness, retain it for all reopens, and do not stop the occupant. A bind failure must stop the test rather than attach to an existing service.

`scripts/prepare_mac_review.py` generates a build-only copy of the Swift wrapper and an Info.plist under this checkout's `.tmp`. It does not modify `Sources/App.swift`, launch anything, or read production preferences. The generated wrapper:

- Forces `--demo --settings <fresh private file> --http-port <stable review port>` on every launch. Sharing/startup connections remain backend-disabled.
- Requires its generated review bundle identifier, with no production-identity fallback.
- Uses a fresh named persistent WKWebsiteDataStore, retained across reopens; requires macOS 14 or later.
- Uses an explicit review-only UserDefaults suite for Full-frame and window geometry. It disables implicit Cocoa frame autosave in the generated wrapper.
- Refuses to overwrite an existing harness directory or use existing settings at generation. **Generate once, then reuse the same app, identity, WebKit store, port and settings path for reopen tests.** Never regenerate between reopen checks.

In a dedicated checkout at the exact PR commit, with a prepared Mac Python/PyInstaller environment:

```sh
python scripts/prepare_mac_review.py \
  --output .tmp/mac-review-harness \
  --settings .tmp/mac-review-state/connection.json

# This builds only into the isolated checkout. Do not launch its production-ID app.
AMP_BUILD_PYTHON="$PWD/.venv/bin/python" bash scripts/build.sh
ditto "dist/KPA1500 Control.app" "dist/KPA1500 Windows Review.app"
cp .tmp/mac-review-harness/Info.plist "dist/KPA1500 Windows Review.app/Contents/Info.plist"
swiftc -module-cache-path "$PWD/.tmp/mac-review-swift-cache" -O \
  .tmp/mac-review-harness/App.swift Sources/WindowPlacement.swift \
  -framework Cocoa -framework WebKit \
  -o "dist/KPA1500 Windows Review.app/Contents/MacOS/KPA1500Control"
codesign --force --deep --sign - "dist/KPA1500 Windows Review.app"
```

Inspect `review-plan.json`, built Info.plist and generated backend arguments before launching. Build/compile/signing failures are failures to resolve; generation tests on Windows do not establish Mac compilation. Do not replace or launch the installed app. Run the generated review app, set Light, callsign, meter, collapsed sections, Compact and stay-on-top, close normally, and reopen the **same** app. Verify all six choices persist and no backend remains after final Quit. Repeat with Full/Dark. Do not use real discovery.

This solution deliberately leaves production Mac persistence unchanged. Origin-independent native Mac persistence would be a separate product change, not something proven by this harness.

## Simulator footer regression

The footer now uses the same permanent simulation decision as the badge/banner: `snapshot.offline_only === true || state.demo === true`. Rendering tests exercise disconnected/stale/error states with `state.demo` missing, ordinary simulated live state, and normal USB/TCP labels. Verify badge, warning **and footer** after Disconnect and after stopping only the review backend. Readings must blank and controls disable.

## Geometry preservation audit and unresolved provenance

Static audit of the reviewed source found:

- `Sources/App.swift` uses `Bundle.main.bundleIdentifier` for instance/data paths, `UserDefaults.standard` for `KPA1500FullFrame`, and implicit `setFrameAutosaveName("KPA1500MainWindow")`. It has no explicit production-suite write or command targeting another plist. A fallback production identifier exists when the bundle identity is missing.
- `scripts/build.sh` emits the production bundle identifier, so renaming a generated app alone never isolates it. Replace Info.plist before signing/launching the review copy.
- `Sources/platform_paths.py` has a production Mac backend default directory. An explicit fresh `--settings` path is necessary; the generated harness always supplies it.
- LocalStorage stores view choices only. Endpoint locks are intentionally shared per equipment endpoint but the simulator does not acquire a hardware lease. No source calls `defaults`, changes a production plist path, or restores production preferences.

These observations **do not establish the cause** of the previously changed hash. No production preference file has been read, rewritten, reset or restored on Windows. The generated harness removes the implicit geometry-domain dependency for future review; it is not a retrospective diagnosis.

For the Mac retest, first inventory running production/review app and backend processes. With operator cooperation, make production quiescent before the baseline so its normal window/display notifications cannot confound the observation. Do not kill unrelated processes. Record stable before/after hashes and decoded **geometry keys** from both production and generated review preference domains, along with timestamps/process observations. A hash alone cannot show which geometry value changed. Do not collect or publish unrelated preference contents. Never overwrite production values to make preservation pass.

If production geometry changes again, retain exact changed keys/values and process evidence, report preservation as unresolved and leave the PR unmerged. Do not infer that review caused it merely from temporal proximity.

## Required report

Run all Python tests, all ten JavaScript suites and native Swift placement tests. Report exact commit, counts/skips, generated identity/store/port, Mac compile result, six preference reopen results, footer failure-state checks, production geometry preservation evidence and clean shutdown. Include that no hardware connection, USB opening, real discovery, WOL or radio commands occurred. Windows native close/save remains verified on Windows, not by a Mac run.
