"""Pre-approve data-training-tier model switches once explicitly opted in.

Mechanism: every interactive model-switch surface (desktop composer picker,
``/model``, Bots editor, ``POST /api/model/set``) funnels through
``hermes_cli.model_selection_guards.combined_selection_warning``, resolved via
a function-local import at call time. This plugin installs an in-memory
wrapper around that single function: when the only warning is
``kind == "data_policy"`` and the user set ``contrib_auto_confirm: true`` in
config.yaml, the wrapper returns ``None`` so the gateway applies the switch
without a confirmation round-trip.

Scope discipline (deliberate, mirrors the documented non-interactive ack):

- cost guards (``kind == "cost"`` / ``"multiple"``) always pass through;
- the CLI startup guard calls ``selection_warnings`` directly and is
  unaffected, so its audit output is preserved;
- the OAuth-login picker (``auth_model_picker``) also uses
  ``selection_warnings`` directly and keeps prompting;
- any failure fails closed to stock behavior (the popup returns);
- the flag is read fresh on every switch, so toggling it needs no restart.

No Hermes files are modified. Disabling/uninstalling the plugin plus a
gateway restart removes the wrapper. If a future Hermes refactor removes the
seam, registration logs a warning and stays inert instead of half-enabling.
"""

from __future__ import annotations

import functools
import logging
from typing import Any

logger = logging.getLogger("hermes_cli.plugins.contrib_auto_confirm")

PLUGIN_ID = "contrib-auto-confirm"
OPT_IN_KEY = "contrib_auto_confirm"
_SEAM_MODULE = "hermes_cli.model_selection_guards"
_SEAM_FUNC = "combined_selection_warning"
_INSTALLED_ATTR = "_contrib_auto_confirm_installed"


def _normalize_opt_in(raw: Any) -> bool:
    """Coerce a config value to bool. Unknown shapes are opt-out (fail-closed)."""
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return raw == 1
    if isinstance(raw, str):
        return raw.strip().lower() in {"true", "yes", "on", "1"}
    return False


def _read_opt_in() -> bool:
    """Fresh opt-in read per switch so toggling needs no restart."""
    try:
        from hermes_cli.config import cfg_get, load_config_readonly
        return _normalize_opt_in(cfg_get(load_config_readonly(), OPT_IN_KEY, default=False))
    except Exception:
        return False


def _install_wrap() -> bool:
    """Wrap the guard once. True when active, False when inert (fail-closed)."""
    try:
        import importlib

        guards = importlib.import_module(_SEAM_MODULE)
    except Exception as exc:
        logger.warning(
            "contrib-auto-confirm: guard module unavailable (%s); popup behavior unchanged", exc
        )
        return False
    original = getattr(guards, _SEAM_FUNC, None)
    if not callable(original):
        logger.warning("contrib-auto-confirm: guard function missing; popup behavior unchanged")
        return False
    if getattr(guards, _INSTALLED_ATTR, False):
        return True

    @functools.wraps(original)
    def auto_confirm(model_name, *, provider=None, base_url=None, api_key=None,
                     model_info=None, selection_context=None):
        kwargs = dict(provider=provider, base_url=base_url, api_key=api_key, model_info=model_info)
        if selection_context is not None:
            kwargs["selection_context"] = selection_context
        result = original(model_name, **kwargs)
        if result is None or getattr(result, "kind", "") != "data_policy":
            return result
        try:
            opted_in = _read_opt_in()
        except Exception:
            return result
        if not opted_in:
            return result
        logger.info(
            "contrib-auto-confirm: pre-approved data-policy switch to %s (provider=%s)",
            model_name,
            provider,
        )
        return None

    setattr(guards, _SEAM_FUNC, auto_confirm)
    setattr(guards, _INSTALLED_ATTR, True)
    return True


def register(ctx: Any) -> None:
    """Entry point called by Hermes after loading this module."""
    if _install_wrap():
        logger.info("contrib-auto-confirm: installed (opt-in key: %s)", OPT_IN_KEY)
    # Otherwise a warning was already logged; registration stays inert.
