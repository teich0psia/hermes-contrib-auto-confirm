"""contrib-auto-confirm: pre-approve data-training-tier model switches.

Entry-point module for the ``hermes_agent.plugins`` group; Hermes calls
:func:`register` after loading it. See :mod:`hermes_contrib_auto_confirm.plugin`.
"""

from .plugin import PLUGIN_ID, register

__all__ = ["PLUGIN_ID", "register"]
