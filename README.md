# hermes-contrib-auto-confirm

**A fork-free [Hermes Agent](https://github.com/NousResearch/hermes-agent) plugin that skips the data-training-tier confirmation popup on model switches — once you explicitly opt in.**

`-contributor` models are discounted because the vendor may use your prompts for training. Hermes therefore asks for confirmation every time you pick one interactively. This plugin records that consent in your own config (`contrib_auto_confirm: true`) and pre-approves those switches, so the composer picker, `/model`, the Bots editor, and `POST /api/model/set` all switch without the popup. No Hermes source files are modified.

> **Consent note.** Enabling this flag means you agree to send prompts to data-training-tier models without per-switch confirmation. That is the entire point of the plugin — only enable it if you mean it.

## Install

Install the wheel from the latest [GitHub Release](https://github.com/teich0psia/hermes-contrib-auto-confirm/releases) **into the Python environment that runs your gateway** (venv python, not system python):

```bash
# Linux
~/.hermes/hermes-agent/venv/bin/python -m pip install hermes_contrib_auto_confirm-*.whl --no-deps
~/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main plugins enable contrib-auto-confirm --no-allow-tool-override
~/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main config set contrib_auto_confirm true
```

```cmd
:: Windows (adjust paths to your install)
C:\Users\<you>\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe -m pip install hermes_contrib_auto_confirm-*.whl --no-deps
hermes plugins enable contrib-auto-confirm --no-allow-tool-override
hermes config set contrib_auto_confirm true
```

Then restart the gateway process that serves your client:

```bash
hermes gateway restart
# or, for a systemd-served remote backend:
systemctl --user restart hermes-desktop-http.service
```

Verify: the gateway log shows `contrib-auto-confirm: installed`, and picking a `-contributor` model no longer pops a confirmation.

### Remote-gateway note

The guard runs **in the gateway process**, not in the Desktop app. If your Desktop talks to a remote gateway (SSH/URL), install + enable + flag + restart **on that host**. The Desktop itself needs nothing.

## Scope discipline (deliberate)

- Only `data_policy` warnings are suppressed, and only while opted in.
- Cost guards (`cost` / `multiple`) always pass through — their popups stay.
- The CLI startup guard and the OAuth-login picker call the guard set directly and keep prompting (audit output and first-time consent are preserved).
- The flag is re-read on every switch: `hermes config set contrib_auto_confirm false` restores popups immediately, no restart needed.
- Any failure fails closed to stock behavior (the popup returns). If a future Hermes refactor removes the seam, registration logs a warning and stays inert.

## Uninstall

```bash
hermes plugins disable contrib-auto-confirm
hermes config set contrib_auto_confirm false
# restart the gateway, then optionally:
<venv python> -m pip uninstall hermes-contrib-auto-confirm
```

## Compatibility

Developed against Hermes Agent `v0.21.0`. `tests/test_seam_shape.py` pins the wrapped seam by AST against a local Hermes checkout (`HERMES_HOME`) and fails loudly on drift instead of silently changing behavior.

## Development

```bash
uv run --extra dev pytest -q
uv run --extra dev ruff check .
```

## License

MIT — see [LICENSE](LICENSE).
