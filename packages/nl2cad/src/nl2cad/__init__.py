"""
nl2cad — Redirect package.

This package re-exports everything from iil-nl2cadfw (the umbrella framework).
Install ``iil-nl2cadfw`` directly for the canonical package name.
"""

from nl2cadfw import *  # noqa: F401,F403

try:
    from nl2cadfw import __version__
except ImportError:
    __version__ = "0.2.0"
