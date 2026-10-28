# KPA1500 Control - Windows candidate release notes

Local release-preparation text for Windows 0.1.25/build 26, numeric version 0.1.25.26, from main `9efe8c119c0655333e52d4078f43b18f4675cdcc`. This is an unpublished prerelease candidate, not an announcement of public availability.

- [Installation, verification, modes, updates and removal](WINDOWS-INSTALL.md)
- [Support through KPA1500-Control GitHub Issues](WINDOWS-SUPPORT.md)
- [Local storage, optional sharing and data handling](WINDOWS-DATA-HANDLING.md)
- [Exact candidate, checksums and remaining acceptance](WINDOWS-RELEASE-CANDIDATE.md)

The support channel is GitHub Issues with no personal email listing. No public privacy-policy URL has been assigned or published.

## Candidate behavior and validation

The Windows port provides the shared amplifier interface in a native window with Full/Compact views, appearance/stay-on-top controls, saved preferences and explicit Simulation, Read-only and Hardware control handoffs. Normal double-click starts in Simulation. Hardware modes start disconnected; the operator must choose Connect. The operator supplies/stops RF and controls drive power; the app must not key the radio or set drive.

The complete signed payload contains 78 verified PE files: the EXE and six dependencies newly signed as Gregory Miller, with 71 vendor signatures preserved. The matching `.exe.config` supports loading bundled managed assemblies from an Internet-marked ZIP. Keep the complete folder together; neither signing nor this config removes download markers or disables Windows security. Third-party licenses and authorship notices remain unchanged.

The exact signed ZIP passed build/provenance/identity audits; eight offline private MSIX/portable coordination cases; separate clean packaged first-launch/reopen; non-admin/read-only-folder preference persistence; reversible missing-WebView2 failure/recovery; and both offline and Internet-enabled marked-file Explorer launch observations. Both marked-file launches reached Simulation without a user-observed warning and retained all 240 file markers plus the ZIP marker. These used synthetic markers, not browser downloads or Explorer propagation. They do not guarantee SmartScreen behavior elsewhere or establish a positive cloud verdict. The interrupted first missing-runtime observation and separate completed automated repeat are qualified in the validation report.

Main Windows regressions: 240 Python passed/two expected skips and all 12 JavaScript suites. The Mac agent reported no blockers on exact PR #10 commit 5a077fe904d619a570036028f81e9d77ecdedcac: 218 Python passed/24 expected skips, 12 JavaScript suites and Swift placement. No new native Mac launch or independent Windows-binary acceptance is claimed from that tooling-only review.

## Pending release work

The EXE remains prerelease. Physical multiple-monitor and final signed-package hardware acceptance remain pending; older live results do not establish this exact ZIP's hardware acceptance. Production Store identity/MSIX/WACK, release-version/distribution decisions and public-release approval remain separate. Private non-Store MSIX testing is complete only within its documented feasibility scope.

This source text and its standalone companion are external to the immutable tested ZIP. Build-time documents in that ZIP retain older candidate references, and links to the validation report are not self-contained because it is not inside the archive. Use the external companion as the current linked set and reconcile shipped documentation before public release. Any regenerated ZIP needs new checksums and artifact-specific validation and must not inherit the old ZIP's hash. No hardware work, repackaging or publication is authorized by finalizing these records.

Application code and project-owned artwork use MIT; see LICENSE and LICENSING.md. Bundled components retain their own notices. No Elecraft affiliation or endorsement is asserted.
