"""Moved to observability/perf_tracker.py — this shim preserves backward compatibility."""
import importlib as _il, sys as _sys
_sys.modules[__name__] = _il.import_module("observability.perf_tracker")
