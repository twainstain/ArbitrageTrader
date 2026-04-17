"""Tests for the Multicall3 batching helper.

We don't hit a real chain here — we mock the web3.eth.contract path and
verify (1) the canonical address is correct, (2) calls are forwarded in
order with the right shape, (3) results are unpacked properly, (4) empty
input is a no-op.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from market.multicall import MULTICALL3_ADDRESS, aggregate3


class Multicall3HelperTests(unittest.TestCase):
    def test_canonical_address(self) -> None:
        # The mds1 deployment is the same on every chain; if this changes
        # the integration breaks silently against old chains.
        self.assertEqual(
            MULTICALL3_ADDRESS,
            "0xcA11bde05977b3631167028862bE2a173976CA11",
        )

    def test_empty_input_is_noop(self) -> None:
        w3 = MagicMock()
        out = aggregate3(w3, [])
        self.assertEqual(out, [])
        # Should not have constructed a contract or made any RPC call.
        w3.eth.contract.assert_not_called()

    def test_forwards_calls_and_unpacks_results(self) -> None:
        w3 = MagicMock()
        contract = w3.eth.contract.return_value
        # Simulate Multicall3 returning two (success, returnData) tuples.
        contract.functions.aggregate3.return_value.call.return_value = [
            (True, b"\x01" * 32),
            (False, b""),
        ]

        calls = [
            ("0x" + "11" * 20, b"call_a"),
            ("0x" + "22" * 20, b"call_b"),
        ]
        results = aggregate3(w3, calls, allow_failure=True)

        # Output preserves order, and bool/bytes are coerced.
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], (True, b"\x01" * 32))
        self.assertEqual(results[1], (False, b""))

        # Verify aggregate3 was called with checksummed addresses + the
        # allow_failure flag we passed.
        sent_calls = contract.functions.aggregate3.call_args[0][0]
        self.assertEqual(len(sent_calls), 2)
        self.assertTrue(sent_calls[0][0].startswith("0x"))
        self.assertEqual(sent_calls[0][1], True)  # allow_failure=True
        self.assertEqual(sent_calls[0][2], b"call_a")

    def test_disable_allow_failure(self) -> None:
        w3 = MagicMock()
        contract = w3.eth.contract.return_value
        contract.functions.aggregate3.return_value.call.return_value = []

        aggregate3(w3, [("0x" + "00" * 20, b"x")], allow_failure=False)

        sent_calls = contract.functions.aggregate3.call_args[0][0]
        self.assertEqual(sent_calls[0][1], False)


if __name__ == "__main__":
    unittest.main()
