import unittest

from src.basic_data_structures.inplace_linked_list import problems
from src.basic_data_structures.inplace_linked_list.linked_list import LinkedList
from src.basic_data_structures.inplace_linked_list.linked_list_node import LinkedListNode

class TestFstSlowPointers(unittest.TestCase):
    def test_is_palindrome(self):
        linked_list = LinkedList()
        linked_list.create_linked_list([1,2,3,4])
        linked_list_res = LinkedList()
        linked_list_res.create_linked_list([1,3,3,4])
        self.assertEqual(problems.reverse_even_length_groups(linked_list.head),linked_list_res)