import unittest

from pointers.fast_slow_pointers import problems
from pointers.two_pointers.linked_list import LinkedList

class TestFstSlowPointers(unittest.TestCase):
    def test_is_palindrome(self):
        self.assertEqual(problems.is_happy_number(4), False)

    def test_detect_cycle(self):
        linked_list = LinkedList()
        linked_list.create_linked_list([0,2,3,5,6,-1])
        self.assertEqual(problems.detect_cycle(linked_list.head), False)