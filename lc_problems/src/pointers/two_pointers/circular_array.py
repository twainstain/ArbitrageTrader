

def find_cycle(nums):
    fast = slow = 0
    length = len(nums)
    while fast < length and nums[fast]< len(nums):
        slow = (nums[slow%length])
        fast = nums[(nums[fast]%length)]%length
        if fast == slow:
            return True
    return False

def find_duplicate(nums):
    fast = slow = nums[0]
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow ==fast:
            print(f"first meeting : slow={slow}, fast={fast}")
            break
    slow = nums[0]
    while slow != fast:
        slow = nums[slow]
        fast = nums[fast]
        print(f"slow={slow}")
        print(f"fast={fast}")
    return fast

def circular_array_loop(nums):
    length = len(nums)
    print(nums)
    for i in range(0,length) :
        fast, slow = i,i
        current_direaction = nums[i] > 0
        while True:
            print(f"slow={slow}")
            print(f"fast={fast}")
            next_fast = (fast + nums[fast])% length
            next_fast_direaction = nums[next_fast] > 0
            next_slow = (slow + nums[slow]) % length
            next_slow_direaction = nums[next_slow] > 0
            if next_fast == fast or slow == next_slow or next_slow_direaction != current_direaction:
                break;
            if next_fast_direaction != current_direaction:
                break;
            next_fast_2 = (next_fast + nums[next_fast])% length
            next_fast_direaction = nums[next_fast] > 0
            if next_fast == next_fast_2 or next_fast_direaction != current_direaction:
                break;
            print(f"next_slow={next_slow}")
            print(f"next_fast={next_fast_2}")
            if next_fast_2 == next_slow:
                return True
            fast = next_fast_2
            slow = next_slow

    return False


def circular_array_loop_official(nums):
    size = len(nums)
    # Iterate through each index of the array 'nums'.
    for i in range(size):
        # Set slow and fast pointer at current index value.
        slow = fast = i

        # Set true in 'forward' if element is positive, set false otherwise.
        forward = nums[i] > 0

        while True:
            # Move slow pointer to one step.
            slow = next_step(slow, nums[slow], size)
            # If cycle is not possible, break the loop and start from next element.
            if is_not_cycle(nums, forward, slow):
                break

            # First move of fast pointer.
            fast = next_step(fast, nums[fast], size)
            # If cycle is not possible, break the loop and start from next element.
            if is_not_cycle(nums, forward, fast):
                break

            # Second move of fast pointer.
            fast = next_step(fast, nums[fast], size)
            # If cycle is not possible, break the loop and start from next element.
            if is_not_cycle(nums, forward, fast):
                break

            # At any point, if fast and slow pointers meet each other,
            # it indicate that loop has been found, return True.
            if slow == fast:
                return True

    return False


# A function to calculate the next step
def next_step(pointer, value, size):
    result = (pointer + value) % size
    if result < 0:
        result += size
    return result


# A function to detect a cycle doesn't exist
def is_not_cycle(nums, prev_direction, pointer):
    # Set current direction to True if current element is positive, set False otherwise.
    curr_direction = nums[pointer] >= 0
    # If current direction and previous direction is different or moving a pointer takes back to the same value,
    # then the cycle is not possible, we return True, otherwise return False.
    if (prev_direction != curr_direction) or (abs(nums[pointer] % len(nums)) == 0):
        return True
    else:
        return False