"""Moved to market/subgraph_market.py — this shim preserves backward compatibility."""
import importlib as _il, sys as _sys
_sys.modules[__name__] = _il.import_module("market.subgraph_market")
