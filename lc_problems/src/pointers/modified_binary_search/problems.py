def binary_search(nums, target):

    left = 0
    right = len(nums) -1
    while left <= right:
        middle = (left + right)//2
        if nums[middle] == target:
            return middle
        elif nums[middle] > target:
            right = middle -1
        else:
            left = middle + 1
    return -1

def binary_search_recursive(nums, low, high, target):

    if (low > high):
        return -1

    # Finding the mid using integer division
    mid = low + (high - low) // 2

    # Target value is present at the middle of the array
    if nums[mid] == target:
        return mid

    # If the target value is greater than the middle, ignore the first half
    elif nums[mid] < target:
        return binary_search_recursive(nums, mid + 1, high, target)

    # If the target value is less than the middle, ignore the second half
    return binary_search_recursive(nums, low, mid - 1, target)

global v
def is_bad_version(s):
    return s >= v
def first_bad_version(n):

    left = 1
    right = n
    comparisions = 0
    while left <= right:
        mid = (left +right)//2
        comparisions+=1
        if not is_bad_version(mid):
            left = mid + 1
        else:
            right = mid -1

    return [left, comparisions]


def binary_search_rotated(nums, target):
    left = 0;
    right = len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] <= nums[right]:
            if nums[mid] <= target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
        else:
            if nums[left] <= target <= nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
    return -1