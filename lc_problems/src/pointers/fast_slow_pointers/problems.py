def is_happy_number(n):
    slow = n
    fast = number_sum(n)
    while slow != fast and fast != 1:
        slow = number_sum(slow)
        fast = number_sum(number_sum(fast))

    if fast == 1:
        return True
    return False


def number_sum(number):
    total_sum = 0
    while number > 0:
        digit = number % 10
        number = number // 10
        total_sum += digit ** 2
    return total_sum


def get_middle_node(head):
    slow, fast = head, head
    while fast and fast.next:
        fast = fast.next.next
        slow = slow.next

    return slow

def detect_cycle(head):
    if head is None:
        return False

    slow, fast = head, head

    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next

        if slow == fast:
            return True

    return False
'''
   # Replace this placeholder return statement with your code
   if not head : return False
   slow = head.next
   fast = head.next.next if head.next else head.next
   while fast and fast != slow:
      fast = fast.next.next if fast.next else fast.next
      slow = slow.next

   if fast:
      return True
   return False
'''