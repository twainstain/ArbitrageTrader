# importing libraries
from collections import Counter
import heapq

def reorganize_string(str):

    char_counter = Counter(str)
    most_freq_chars = []

    for char, count in char_counter.items():
        most_freq_chars.append([-count, char])

    heapq.heapify(most_freq_chars)

    previous = None
    result = ""

    while len(most_freq_chars) > 0 or previous:

        if previous and len(most_freq_chars) == 0:
            return ""

        count, char = heapq.heappop(most_freq_chars)
        result = result + char
        count = count + 1

        if previous:
            heapq.heappush(most_freq_chars, previous)
            previous = None

        if count != 0:
            previous = [count, char]

    return result


# Driver code
def main():
    test_cases = ["programming", "hello", "fofjjb",
                  "abbacdde", "aba", "awesome", "aaab"]
    for i in range(len(test_cases)):
        print(i+1, '. \tInput string: "', test_cases[i], '"', sep="")
        temp = reorganize_string(test_cases[i])
        print('\tReorganized string: "', temp + '"' if temp else '"', sep="")
        print("-"*100)


if __name__ == '__main__':
    main()