"""Pin the conftest stub against the real Hermes source tree by AST (no imports).

Skips when the Hermes checkout is absent. Fails when the seam the plugin
wraps (``combined_selection_warning``) or the ``SelectionWarning`` shape it
inspects (``.kind``) drifts, so a Hermes refactor turns into a loud test
failure instead of a silent behavior change.
"""

import ast
import os
from pathlib import Path

import pytest


def _repo_root():
    home = os.environ.get("HERMES_HOME") or str(Path.home() / "AppData/Local/hermes")
    candidates = [Path(home) / "hermes-agent"]
    here = Path(__file__).resolve()
    candidates.extend(p / "hermes-agent" for p in here.parents)
    for cand in candidates:
        if (cand / "hermes_cli" / "model_selection_guards.py").exists():
            return cand
    return None


REPO = _repo_root()
pytestmark = pytest.mark.skipif(REPO is None, reason="Hermes checkout not found")


def _parse():
    src = (REPO / "hermes_cli" / "model_selection_guards.py").read_text(encoding="utf-8")
    return ast.parse(src)


def test_guard_function_signature():
    tree = _parse()
    fns = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "combined_selection_warning"
    ]
    assert fns, "combined_selection_warning is gone"
    fn = fns[0]
    kwonly = {a.arg for a in fn.args.kwonlyargs}
    assert {"provider", "base_url", "api_key", "model_info"} <= kwonly


def test_selection_warning_has_kind():
    tree = _parse()
    classes = [
        n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "SelectionWarning"
    ]
    assert classes, "SelectionWarning is gone"
    announced = ast.get_source_segment(
        (REPO / "hermes_cli" / "model_selection_guards.py").read_text(encoding="utf-8"),
        classes[0],
    )
    assert "kind" in announced


def test_call_sites_still_resolve_at_call_time():
    """Every interactive switch path must keep its function-local import.

    A top-level ``from ... import combined_selection_warning`` would freeze
    the unwrapped reference and silently defeat this plugin.
    """
    targets = [
        REPO / "tui_gateway" / "model_switch.py",
        REPO / "hermes_cli" / "cli_model_switch_mixin.py",
        REPO / "hermes_cli" / "web_routers" / "models.py",
    ]
    for path in targets:
        assert path.exists(), f"switch path moved: {path}"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        top_level = [
            n
            for n in tree.body
            if isinstance(n, (ast.ImportFrom,))
            and "combined_selection_warning" in {a.asname or a.name for a in n.names}
        ]
        assert not top_level, f"{path} binds the guard at module top level"
