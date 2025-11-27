def word_ladder(src, dest, words):
    # Create a set of words for faster lookup
    myset = set(words)
    # If the dest is not in the set, return 0
    if dest not in myset:
        return 0
    # Create a queue for the words to be checked
    q = []
    q.append(src)
    # Initialize the length counter
    length = 0

    # Check words until the queue is empty
    while q:
        length += 1
        # Store the length of the queue
        size = len(q)
        # Check all the words in the current level
        for _ in range(size):
            # Pop a word from the queue
            curr = q.pop(0)
            # Iterate on each character of the popped word
            for i in range(len(curr)):
                alpha = "abcdefghijklmnopqrstuvwxyz"
                # Iterate with all possible characters
                for c in alpha:
                    # As the strings are immutable, we create a list to replace
                    # the ith character of the popped word
                    temp = list(curr)
                    temp[i] = c
                    temp = "".join(temp)
                    # Check if the new word is the dest
                    if temp == dest:
                        return length + 1
                    # Check if the new word is in the set
                    # If it is, push it into the queue and remove it from the set
                    if temp in myset:
                        q.append(temp)
                        myset.remove(temp)
    # Return 0 if no sequence exists
    return 0



# Driver code
if __name__ == '__main__':
    words_list = [["hog", "dot", "pot", "pop", "mop", "map", "cap", "cat"], ["hot", "dot", "lot", "log", "cog"],
                  ["hot", "not", "dot", "lot", "cog"], ["hog", "dot", "pot", "pop", "mop", "map", "cap", "cat"],
                  ["hot", "dot", "lot", "log", "cog", "com", "cam", "frog"]]
    src_list = ["dog", "hit", "hat", "dog", "dog"]
    dest_list = ["cat", "cog", "log", "cat", "frog"]

for i in range(len(src_list)):
    print(i + 1, ".\tsrc: \"", src_list[i], "\"", sep="")
    print("\tdest: \"", dest_list[i], "\"", sep="")
    print("\tAvailable words: ", words_list[i], "\n", sep="")
    print("\tLength of shortest chain is: ", word_ladder(src_list[i], dest_list[i], words_list[i]))
    print("-" * 100)