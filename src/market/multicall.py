"""Multicall3 batching helper for collapsing N eth_calls into one RPC roundtrip.

Multicall3 is deployed at the same canonical address on every EVM chain we
use (Ethereum, Arbitrum, Optimism, Base, Polygon, Avalanche, BNB):

    0xcA11bde05977b3631167028862bE2a173976CA11

Reference: https://github.com/mds1/multicall (Foundry-deployed by mds1, the
de-facto standard since 2022).

Why this exists
~~~~~~~~~~~~~~~
Today each DEX quoter inside ``OnChainMarket._fetch_one`` makes its own
``eth_call``. The scan tail latency is ``max(N parallel calls)``. With
keep-alive (added in commit 8c592fa) per-call overhead drops, but the
slowest single quoter still bounds the tail.

With Multicall3, all quoters on the same chain can be aggregated into a
single ``eth_call``. The RPC executes them inside one transaction context,
so per-chain latency drops from ``max(N)`` to roughly the cost of the
slowest single underlying call plus ABI overhead — usually 1.5-2× a
single call instead of N×.

This module provides the primitives. Wiring into the per-DEX quoter path
is intentionally separate so each quoter implementation can opt in
without forcing a big-bang refactor.
"""

from __future__ import annotations

from typing import Any

from web3 import Web3


# Canonical Multicall3 deployment — same address on every supported chain.
MULTICALL3_ADDRESS: str = Web3.to_checksum_address(
    "0xcA11bde05977b3631167028862bE2a173976CA11"
)


# Minimal ABI: just the aggregate3 entrypoint that's relevant to us.
# Uses Call3 (with allowFailure) so a single bad calldata doesn't revert
# the whole batch — important for resilience when one quoter has stale
# pool data while the others are fine.
MULTICALL3_ABI: list[dict[str, Any]] = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "target", "type": "address"},
                    {"internalType": "bool", "name": "allowFailure", "type": "bool"},
                    {"internalType": "bytes", "name": "callData", "type": "bytes"},
                ],
                "internalType": "struct Multicall3.Call3[]",
                "name": "calls",
                "type": "tuple[]",
            }
        ],
        "name": "aggregate3",
        "outputs": [
            {
                "components": [
                    {"internalType": "bool", "name": "success", "type": "bool"},
                    {"internalType": "bytes", "name": "returnData", "type": "bytes"},
                ],
                "internalType": "struct Multicall3.Result[]",
                "name": "returnData",
                "type": "tuple[]",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


def aggregate3(
    w3: Web3,
    calls: list[tuple[str, bytes]],
    allow_failure: bool = True,
) -> list[tuple[bool, bytes]]:
    """Batch ``calls`` through Multicall3 on the chain backing ``w3``.

    Args:
        w3: Web3 instance for the chain. Must already be connected.
        calls: list of ``(target_address, calldata)`` tuples — one per
            underlying eth_call to be batched.
        allow_failure: when True (default), an individual call failure is
            reported in the per-call ``success`` flag rather than
            reverting the whole batch.

    Returns:
        List of ``(success, return_data)`` tuples in the same order as
        ``calls``. ``return_data`` is the raw bytes returned by each
        sub-call; the caller is responsible for ABI-decoding it against
        the original function signature.

    Raises:
        Whatever ``web3.eth.call`` raises if the batch as a whole fails
        (e.g. RPC error, network error). Individual call failures with
        ``allow_failure=True`` do NOT raise — they appear in the return.
    """
    if not calls:
        return []
    contract = w3.eth.contract(address=MULTICALL3_ADDRESS, abi=MULTICALL3_ABI)
    args = [
        (Web3.to_checksum_address(target), allow_failure, calldata)
        for target, calldata in calls
    ]
    raw = contract.functions.aggregate3(args).call()
    return [(bool(r[0]), bytes(r[1])) for r in raw]
