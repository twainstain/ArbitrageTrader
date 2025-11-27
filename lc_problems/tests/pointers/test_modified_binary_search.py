import unittest

from pointers.modified_binary_search import problems


class TestFstSlowPointers(unittest.TestCase):
    def test_is_palindrome(self):
        self.assertEqual(problems.binary_search_rotated([6, 7, 1, 2, 3, 4, 5], 6), 0)
