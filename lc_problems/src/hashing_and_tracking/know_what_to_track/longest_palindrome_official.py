from collections import Counter

def longest_palindrome(words):
    # The built-in counter method is used to count the
    # Frequencies of each word
    frequencies = Counter(words)
    count = 0
    central = False

    for word, frequency in frequencies.items():
        # If word is a palindrome
        if word[0] == word[1]:
            # If a word has even occurrences
            if frequency % 2 == 0:
                count += frequency
            # If a word has odd occurrences
            else:
                count += frequency - 1
                central = True

        # If word is not a palindrome
        # Ensuring that a word and its reverse is only considered once
        elif word[1] > word[0]:
            # Get the minimum of the occurrences of the word and its reverse
            count += 2 * min(frequency, frequencies[word[1] + word[0]])

    if central:
        count += 1

    return 2 * count

# driver code
def main():
    input_nums = [
        ["ab", "cd", "ef", "gh", "ab", "cd", "ef", "gh"],
        ["aa", "bb", "cc", "dd", "ee"],
        ["ab", "bc", "cd", "dc", "aa", "dd"],
        ["ae", "pq", "qp", "cd", "ee", "ea"],
        ["xx", "yy", "xy", "yx", "zz", "zz"],
    ]

    for i in range(len(input_nums)):
        words = ', '.join(['"{0}"'.format(word) for word in input_nums[i]])
        print("{0}.\twords = [{1}]".format(i + 1, words))
        print("\tThe length of the longest palindrome by concatenating two letter words is: {0}".format(
            longest_palindrome(input_nums[i])))
        print("-" * 100)

if __name__ == "__main__":
    main()