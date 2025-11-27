import re
def reverse_words(sentence):

    #sentence = list(sentence[::-1])
    sentence = re.sub(' +', ' ', sentence.strip())
    sentence = list(reversed(sentence))
    start, write_index = 0,0;
    #print(sentence)
    while start < len(sentence):
        end=start
        #print(f"start={start}")
        while end < len(sentence) and sentence[end] != ' ':
            end+=1
        if end > start :
            end-=1
        end_word = end
        start_word = start
        #print(f"end={end}")
        while start<end:
            sentence[start], sentence[end] = sentence[end], sentence[start]
            start+=1
            end-=1
        start = end_word + 1
    #print(sentence)
    return ''.join(sentence)


def reverse_words_official(sentence):
    # Remove extra spaces and strip leading/trailing spaces
    sentence = re.sub(' +', ' ', sentence.strip())

    # Convert the sentence to a list of characters
    # for in-place modification as strings are immutable in Python
    sentence = list(sentence)
    str_len = len(sentence) - 1

    # Reverse the whole sentence first
    str_rev(sentence, 0, str_len)
    start = 0

    # Iterate through the sentence to find and reverse each word
    for end in range(0, str_len + 1):
        if end == str_len or sentence[end] == ' ':
            # Include end character for the last word
            end_idx = end if end == str_len else end - 1
            # Reverse the current word
            str_rev(sentence, start, end_idx)
            # Move the "start" pointer to the start of the next word
            start = end + 1

    return ''.join(sentence)

# A function that reverses characters from start_rev to end_rev in place
def str_rev(_str, start_rev, end_rev):
    while start_rev < end_rev:
        _str[start_rev], _str[end_rev] = _str[end_rev], _str[start_rev]
        start_rev += 1
        end_rev -= 1


# Driver code
def main():
    string_to_reverse = ["Hello World",
                        "a   string   with   multiple   spaces",
                        "Case Sensitive Test Case 1234",
                        "a 1 b 2 c 3 d 4 e 5",
                        "     trailing spaces",
                        "case test interesting an is this"]

    for i in range(len(string_to_reverse)):
        print(i + 1, ".\tOriginal string: '" + "".join(string_to_reverse[i]), "'", sep='')
        result = reverse_words(string_to_reverse[i])

        print("\tReversed string: '" + "".join(result), "'", sep='')
        print("-" * 100)


if __name__ == '__main__':
    main()