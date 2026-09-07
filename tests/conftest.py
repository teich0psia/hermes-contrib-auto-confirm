"""Hermes-free test bootstrap.

The plugin under test only touches
``hermes_cli.model_selection_guards`` (attribute read + wrap at register
time; config import only inside the opt-in reader, which tests monkeypatch).
Seeding a faithful stub keeps this suite runnable on a bare interpreter while
``test_seam_shape.py`` pins the stub against the real source tree by AST.
"""

import sys
import types
from dataclasses import dataclass


@dataclass(frozen=True)
class SelectionWarning:
    kind: str
    title: str
    model: str
    provider: str
    message: str


def _unwrapped(model_name, *, provider=None, base_url=None, api_key=None, model_info=None):
    return None


def _ensure_stub() -> None:
    if "hermes_cli.model_selection_guards" in sys.modules:
        return
    fake_guards = types.ModuleType("hermes_cli.model_selection_guards")
    fake_guards.SelectionWarning = SelectionWarning
    fake_guards.combined_selection_warning = _unwrapped
    fake_pkg = types.ModuleType("hermes_cli")
    fake_pkg.__path__ = []  # mark as package so submodule import resolves
    fake_pkg.model_selection_guards = fake_guards
    sys.modules["hermes_cli"] = fake_pkg
    sys.modules["hermes_cli.model_selection_guards"] = fake_guards


_ensure_stub()
