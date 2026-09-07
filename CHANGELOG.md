# Changelog

## 0.1.0 — 2026-09-07

### Added

- Initial release. Wraps `hermes_cli.model_selection_guards.combined_selection_warning` in-memory and suppresses `data_policy` warnings only, only while `contrib_auto_confirm: true` is set.
- Cost guards, CLI startup guard, and OAuth-login picker keep prompting (fail-closed scope discipline).
- Offline unit tests plus an AST seam-shape canary against the host checkout.
