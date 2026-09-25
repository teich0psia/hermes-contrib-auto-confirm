"""Offline tests for contrib-auto-confirm (runs against the conftest stub).

Run from ``package/`` with any Python 3.11+ intepreter, e.g. ``uvx pytest``.
No Hermes install, gateway, config, or network is touched.
"""

import sys
import types

import pytest
from hermes_cli import model_selection_guards as guards

from hermes_contrib_auto_confirm import plugin


@pytest.fixture()
def fresh_guard(monkeypatch):
    """Restore the stub guard after each test (wrap is module-global)."""
    real = guards.combined_selection_warning
    installed = getattr(guards, plugin._INSTALLED_ATTR, False)
    yield
    guards.combined_selection_warning = real
    if installed:
        setattr(guards, plugin._INSTALLED_ATTR, True)
    else:
        try:
            delattr(guards, plugin._INSTALLED_ATTR)
        except AttributeError:
            pass


def _warning(kind):
    return guards.SelectionWarning(
        kind=kind, title="t", model="meta/muse-spark-1.3-contributor",
        provider="command-code", message="m",
    )


def test_normalize_opt_in():
    assert plugin._normalize_opt_in(True) is True
    assert plugin._normalize_opt_in("true") is True
    assert plugin._normalize_opt_in("YES") is True
    assert plugin._normalize_opt_in(1) is True
    assert plugin._normalize_opt_in(False) is False
    assert plugin._normalize_opt_in("false") is False
    assert plugin._normalize_opt_in(None) is False
    assert plugin._normalize_opt_in([]) is False
    assert plugin._normalize_opt_in(2) is False


def test_data_policy_suppressed_when_opted_in(monkeypatch, fresh_guard):
    monkeypatch.setattr(
        guards, "combined_selection_warning", lambda *a, **k: _warning("data_policy")
    )
    monkeypatch.setattr(plugin, "_read_opt_in", lambda: True)
    plugin.register(ctx=types.SimpleNamespace())
    assert guards.combined_selection_warning("meta/muse-spark-1.3-contributor") is None


def test_popup_returns_when_not_opted_in(monkeypatch, fresh_guard):
    monkeypatch.setattr(
        guards, "combined_selection_warning", lambda *a, **k: _warning("data_policy")
    )
    monkeypatch.setattr(plugin, "_read_opt_in", lambda: False)
    plugin.register(ctx=types.SimpleNamespace())
    assert guards.combined_selection_warning("meta/muse-spark-1.3-contributor") is not None


def test_cost_guard_never_suppressed(monkeypatch, fresh_guard):
    monkeypatch.setattr(guards, "combined_selection_warning", lambda *a, **k: _warning("cost"))
    monkeypatch.setattr(plugin, "_read_opt_in", lambda: True)
    plugin.register(ctx=types.SimpleNamespace())
    assert guards.combined_selection_warning("expensive-model") is not None


def test_selection_context_is_forwarded(monkeypatch, fresh_guard):
    seen = []
    context = object()

    def guard(model_name, **kwargs):
        seen.append(kwargs)
        return _warning("cost")

    monkeypatch.setattr(guards, "combined_selection_warning", guard)
    monkeypatch.setattr(plugin, "_read_opt_in", lambda: True)
    plugin.register(ctx=types.SimpleNamespace())
    result = guards.combined_selection_warning("expensive-model", selection_context=context)
    assert result is not None
    assert seen[0]["selection_context"] is context


def test_old_guard_without_context_still_works(monkeypatch, fresh_guard):
    def guard(model_name, *, provider=None, base_url=None, api_key=None, model_info=None):
        return _warning("data_policy")

    monkeypatch.setattr(guards, "combined_selection_warning", guard)
    monkeypatch.setattr(plugin, "_read_opt_in", lambda: True)
    plugin.register(ctx=types.SimpleNamespace())
    assert guards.combined_selection_warning("contributor-model") is None


def test_multiple_kind_never_suppressed(monkeypatch, fresh_guard):
    monkeypatch.setattr(
        guards, "combined_selection_warning", lambda *a, **k: _warning("multiple")
    )
    monkeypatch.setattr(plugin, "_read_opt_in", lambda: True)
    plugin.register(ctx=types.SimpleNamespace())
    assert guards.combined_selection_warning("expensive-contributor") is not None


def test_register_is_idempotent(monkeypatch, fresh_guard):
    calls = []

    def stub(*a, **k):
        calls.append(1)
        return None

    monkeypatch.setattr(guards, "combined_selection_warning", stub)
    monkeypatch.setattr(plugin, "_read_opt_in", lambda: True)
    plugin.register(ctx=types.SimpleNamespace())
    plugin.register(ctx=types.SimpleNamespace())
    guards.combined_selection_warning("x")
    assert calls == [1]


def test_missing_seam_fails_closed(monkeypatch, fresh_guard, caplog):
    monkeypatch.delattr(guards, "combined_selection_warning", raising=False)
    with caplog.at_level("WARNING", logger="hermes_cli.plugins.contrib_auto_confirm"):
        plugin.register(ctx=types.SimpleNamespace())
    assert "unchanged" in caplog.text
    assert not getattr(guards, plugin._INSTALLED_ATTR, False)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
