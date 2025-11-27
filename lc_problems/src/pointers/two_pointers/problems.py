from typing import List
from src.two_pointers.linked_list import LinkedList
from src.two_pointers.linked_list_node import LinkedListNode
from two_pointers.linked_list_reversed import reverse_linked_list

'''
1,3,0,4,0
1,3,4,0,0
'''
def move_zero_to_end(array:List[int])->List[int]:
   left = 0
   right = 0
   while(right < len(array)):
      if array[right] != 0:
         swap(array, left, right)
         left+=1
         right+=1
      else:
         right += 1

   return array

def sum_3(array:List[int], sum)->bool:
   left = 0
   right = len(array)-1
   while(left < right-2):
      sum_2 = sum - array[left]
      if sum_exist(array,sum_2,left+1, right):
         print(f'{array[left]} + {sum_2}= {sum}')
         return True
      else:
         left+=1

   return False


def sum_exist(array: List[int], sum, left_index, right_index) -> bool:
   while (left_index < right_index):
      if array[left_index] + array[right_index] == sum:
         print(f'{array[left_index]} + {array[right_index]} = {sum}')
         return True

      if array[left_index] + array[right_index] > sum:
         right_index-=1
      else:
         left_index+=1

def swap (array, index_a, index_b):
   temp = array[index_a]
   array[index_a] = array[index_b]
   array[index_b] = temp

def is_palindrome(s:str):
   array = list(s)
   left = 0
   right = len(array)-1
   while(left < right) :
      if array[left] != array[right]:
         return False
      left+=1
      right-=1

   return True

'''
[69,8,49,106,116,112] , 5
'''
def remove_nth_last_node(head, n):
   left:LinkedListNode = head
   right:LinkedListNode = head
   i = 0
   while right is not None and i < n:
      right = right.next
      i+=1

   while right.next is not None:
      right = right.next
      left = left.next

   if right is None and left is not None and left == head:
      head = head.next
      left.next = None
   elif left is not None:
      left.next = None
      left.next = left.next

   return head


def palindrome(head):
   slow: LinkedListNode = head
   fast: LinkedListNode = head
   while fast != None and fast.next != None:
      slow = slow.next
      fast = fast.next.next

   left = head
   right = reverse_linked_list(slow)
   while left != slow and right != None:
      if left.data != right.data:
         return False
      left = left.next
      right = right.next

   return True

def main():
   print('main')


if __name__ == '__main__':
   main()