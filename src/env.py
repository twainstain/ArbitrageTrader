"""Moved to core/env.py — this shim preserves backward compatibility."""
import importlib as _il, sys as _sys
_sys.modules[__name__] = _il.import_module("core.env")
