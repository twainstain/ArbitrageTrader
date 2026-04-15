"""Moved to tools/fork_scanner.py — this shim preserves backward compatibility."""
import importlib as _il
import sys as _sys
_mod = _il.import_module("tools.fork_scanner")
# Re-export everything including private names for test compatibility.
_sys.modules[__name__] = _mod
