"""Moved to tools/show_prices.py — this shim preserves backward compatibility."""
import importlib as _il
import sys as _sys
_mod = _il.import_module("tools.show_prices")
# Re-export everything including private names for test compatibility.
_sys.modules[__name__] = _mod
