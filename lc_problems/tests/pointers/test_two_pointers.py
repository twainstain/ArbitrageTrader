import unittest
from pointers.two_pointers import circular_array, problems, linked_list as LinkedList


class TestTwoPointers(unittest.TestCase):
    def test_is_palindrome(self):
        self.assertEqual(problems.is_palindrome('ab'), False)
        self.assertEqual(problems.is_palindrome('a'), True)
        self.assertEqual(problems.is_palindrome('aba'), True)
        self.assertEqual(problems.is_palindrome('abba'), True)
        self.assertEqual(problems.is_palindrome('abaa'), False)

    def test_move_zero_to_end(self):
        self.assertEqual(problems.move_zero_to_end([0, 1]), [1, 0])
        self.assertEqual(problems.move_zero_to_end([2, 0, 1, 0, 1]), [2, 1, 1 , 0, 0])
        self.assertEqual(problems.move_zero_to_end([0, 0]), [0, 0])

    def test_remove_nth_last_node(self):
        linked_list = LinkedList()
        linked_list.create_linked_list([23,28,10,5,67,39,70,28])
        linked_list_result = LinkedList()
        linked_list_result.create_linked_list([23,28,10,5,67,39,28])
        self.assertEqual(linked_list.equal(problems.remove_nth_last_node(linked_list.head, 2), linked_list_result.head), True)
        linked_list = LinkedList()
        linked_list.create_linked_list([69, 8, 49, 106, 116, 112])
        linked_list_result = LinkedList()
        linked_list_result.create_linked_list([69, 49, 106, 116, 112])
        self.assertEqual(linked_list.equal(problems.remove_nth_last_node(linked_list.head, 5), linked_list_result.head),
                         True)
    def test_sum_3(self):
        self.assertEqual(problems.sum_3([0, 1, 2, 3, 4], 6), True)
        self.assertEqual(problems.sum_3([0, 1, 2, 3, 4], 16), False)
        self.assertEqual(problems.sum_3([0, 10, 25, 30, 45], 70), True)

    def test_cycle(self):
        self.assertEqual(circular_array.find_cycle([2, 3, 1, 4, 0, 9, 7]), True)
        self.assertEqual(circular_array.find_cycle([1, 2, 3]), True)

if __name__ == '__main__':
    unittest.main()