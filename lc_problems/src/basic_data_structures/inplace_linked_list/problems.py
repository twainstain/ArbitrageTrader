def reverse(head):
    prev = next = None
    current = head
    while current != None:
        next = current.next
        current.next = prev
        prev = current
        current = next
    head = prev
    return head