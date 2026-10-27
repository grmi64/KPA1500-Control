# KPA1500 baseline audit — 2026-10-26

## Provenance

- Installed Mac app: 0.1.25/build 26, arm64, bundled Python 3.9. All 63 regular files match the original local dist app. Five packaged web assets also match the source. Developer ID and nested signatures verify. No new notarization or clean-machine installation test was performed.
- Original checkout: /Users/gregorymiller/Documents/Codex/2026-10-18/new-chat/KPA1500-Release-0.1.9. Its name is historical; the actual local version is 0.1.25. Original edits remain untouched.
- Last committed development source: 8f9bd8e177d820986929b96588c8c534fcd387cf (published 0.1.21). Local work adds discovery, bounded identity probes, cancellation, request serialization, result selection, spinner/spacing, novice help/failure wording and version labels. These changes were previously unpublished.
- GitHub default main is still 25674edfffd5a87e40dd8ebb82ee74df2990356b, from the 0.1.3 era. TCP/IP and later controls are on release branches. This baseline preserves that history through 0.1.21 and adds the installed local work. Do not start the Windows port from the old main.
- Latest published binary remains 0.1.21. This audit does not merge, publish binaries, install, or restart production apps.

## Offline checks

Python 3.12.14 discovery completed 72 tests: 71 passed and one expected Mac pseudo-terminal exclusivity skip. All nine JavaScript suites and native Swift window-placement tests passed. Diff checks passed.

The matching frozen 0.1.25 backend was launched with explicit demo mode, a fresh isolated settings path and HTTP port 0. It reported live simulated telemetry, served all five UI assets, kept sharing/startup auto-connect disabled, and exited with code 0 in 0.019 seconds. No native production window was opened. This validates simulator packaging, not Windows or hardware acceptance.

Historical hardware evidence covers USB/TCP monitoring, RF power/SWR comparison, mode transitions, ATU In/Bypass, operator-supplied-RF tuning, Cancel Tune confirmation, enabled/disabled antenna selection, USB/Ethernet power cycles and operator-verified fan settings. See HARDWARE_TESTS.md and release notes. No new hardware test occurred here. Deliberate fault recovery remains unverified.

## Portability findings

1. transport.py imports termios and port_lock.py at module import; port_lock.py imports fcntl. TCP also uses a POSIX flock lease. Even TCP/simulator imports need platform adapters before they can run on Windows.
2. USB enumeration and validation are /dev/cu-specific in engine.py and transport.py. Windows needs COM enumeration, COM10+ support, busy/driver errors, exclusive opens and bounded I/O. Windows serial handles cannot use the existing select-based serial implementation; keep socket handling separate.
3. discovery.local_targets uses Mac route/ipconfig commands. Windows needs a platform-correct local-subnet provider. Preserve the /24 cap, bounded probes, cancellation and no routed scans.
4. Existing USB discovery actively opens unowned serial ports and sends ^I; up to three times. It is not passive listing and can target an unrelated idle radio/meter. For Windows, begin with passive enumeration and explicit user port selection; do not blindly probe every COM port. Any broader active discovery policy needs deliberate review. Mac behavior is recorded here, not silently changed.
5. Settings paths, locks, singleton protection and the Swift/WebKit bridge are Mac-specific. Review/simulator sessions must always use new settings, not production settings that may enable startup hardware connections. Keep the loopback/token/feed contract.
6. Mac build.sh defaults to a temporary build environment, merges frozen output without clearing old runtime files, lacks explicit architecture/deployment flags, and lacks the unique-UUID linker option used by OM Power. Address build hygiene separately before another distributable Mac build. Prefer Python 3.12/PyInstaller 6.22.3 for future reviewed builds; the installed Python 3.9 build has not been migrated by this audit.
7. No pinned Windows dependency manifest, root LICENSE, or bundled-runtime notice inventory was found. Confirm distribution rights/license with the owner and include Python, PyInstaller, serial and native UI dependency notices before public/Store release. Do not copy OM licensing files without checking applicability.
8. Historical README version/test sections are stale; this report gives the audited counts. Preserve historical evidence without presenting it as current Windows acceptance.

## Preservation

Installed app and KPA configuration/preferences were hashed for before/after comparison. No production settings enter Git, no actual discovery scan ran, and no amplifier/radio commands were sent. Private manifests/logs and isolated simulator files remain ignored. Production running apps and settings are not changed.
