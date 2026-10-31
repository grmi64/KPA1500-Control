# Repository publication audit — October 30, 2026

Result: no unresolved publication blocker found in the checks below. The owner authorized making the existing repository public after this audit. This is a publication review, not a new hardware acceptance run or a guarantee that automated scanning detects every secret.

## Scope and results

- Baseline: main `e2eb09d2f93d3b4aae3cbfd29a80b8cc5d4dc415`. All fetched branches and tags, plus all 21 GitHub PR head refs, were included: 63 reachable commits and 363 unique file blobs (7,900,223 bytes) before this documentation change.
- Official Gitleaks v8.30.1 Windows download was verified against its release checksums. Default-rule scans with full redaction found no leaks in Git history, all reachable blobs, the current tracked tree, or the collected GitHub publication metadata. The all-blob pass supplements the Git diff scan so unchanged/deleted versions are covered. No suppression configuration was added.
- GitHub publication metadata reviewed: 21 issues/PRs, one issue comment, zero inline review comments/reviews, and eight published releases. Release assets are the existing Mac DMGs/release manifests and the accepted Windows ZIP/checksum; no diagnostic archive is attached. There are no Actions runs or artifacts, and wiki and discussions are disabled. No issue/comment attachment URLs were found beyond profile avatars.
- A temporary clone token returned by the authenticated repository API was a collector-only scanner match, not committed content. That transient field was redacted from the private local collection before the metadata scan passed. It is not included in this report or any public asset.
- No credential/key/certificate-store/capture/database filenames were found in reachable source history or the accepted Windows ZIP inventory. Local `.tmp`, `dist`, virtual environments, private profiles, signing configuration and the diagnostic archive remain outside tracked source. Git authors use the owner's GitHub noreply identity.
- Historical reports intentionally retain the project owner's attribution, development paths, private LAN addresses and hardware identifiers. These are technical provenance, not access credentials; this audit does not claim that the repository contains no identifying metadata. Third-party notices retain their upstream attribution/contact details.
- Root MIT licensing covers project-owned code, documentation and artwork, consistent with the owner's recorded licensing decision in `LICENSING.md`. Third-party components retain their own terms. All 57 pinned notice/source files were checked in both the repository and accepted Windows ZIP; both packaged application LICENSE copies match. The Windows inventory lists 22 components. The prior build's frozen-module notice audit passed. PyInstaller's bootloader exception and supplied third-party license/source notices remain intact; no dependency was relicensed.
- The accepted Windows ZIP and executable retain their recorded hashes and valid timestamped signature. The Windows ZIP's 237-file inventory was previously verified; no rebuild or repackaging is performed here. Earlier Mac DMGs are inventoried as existing releases, not rebuilt, reverse-engineered or given new hardware acceptance by this audit.
- Current README, installation, support, data-handling and release records now point to the published Windows Preview and completed hardware/display acceptance. Historical milestones remain labeled. Twenty-six relative links in the current user documents resolve locally; evidence links under `dist/windows` are explicitly local archive paths, not promises of publicly uploaded reports.

## Publication boundaries

The visibility change exposes the existing repository history, PRs/issues, releases and GitHub-generated source archives. It does not upload the off-device backup, raw hardware traces or local signing/session files. The MIT license is unchanged. Microsoft Store distribution remains deferred.

The accepted runtime remains `a400cfe04a09ac7c007186b0c7c1ab0d164b50cf`; the Windows release tag remains `v0.1.25-windows-preview-build26`. This documentation update does not change the accepted binary or its immutable bundled build-time documents.

Private collection files, redacted scanner reports and scanner provenance are preserved locally under `.tmp/publication-audit-2026-10-30/`. A separate local receipt records the subsequent visibility change and unauthenticated download checks. No universal secret-detection, legal-certification or SmartScreen-reputation claim is made.
