"""Hermes directory-plugin adapter for PM-managed installations."""


def register(ctx):
    from .hermes_contrib_auto_confirm import register as register_plugin

    register_plugin(ctx)
