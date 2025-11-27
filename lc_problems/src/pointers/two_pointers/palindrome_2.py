def is_palindrome_index(s, start, end):
    while start < end:
        if s[start] != s[end]:
            return False
        start += 1
        end -= 1
    return True


def is_palindrome(s):
    left = 0
    right = len(s) - 1
    while left < right:
        if s[left] == s[right]:
            left += 1
            right -= 1
        else:
            break
    if left < right:
        return (is_palindrome_index(s, left + 1, right) or
                is_palindrome_index(s, left, right - 1))

    return True