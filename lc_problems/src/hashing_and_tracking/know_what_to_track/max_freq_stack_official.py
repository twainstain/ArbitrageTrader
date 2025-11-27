from collections import defaultdict


# Declare a FreqStack class containing frequency and group hashmaps
# and maxFrequency integer
class FreqStack:

    # Use constructor to initialize the FreqStack object
    def __init__(self):
        self.frequency = defaultdict(int)
        self.group = defaultdict(list)
        self.max_frequency = 0

    # Use push function to push the value into the FreqStack
    def push(self, value):
        # Get the frequency for the given value and
        # increment the frequency for the given value
        freq = self.frequency[value] + 1
        self.frequency[value] = freq

        # Check if the maximum frequency is lower that the new frequency
        # of the given show
        if freq > self.max_frequency:
            self.max_frequency = freq

        # Save the given showName for the new calculated frequency
        self.group[freq].append(value)

    def pop(self):
        value = ""

        if self.max_frequency > 0:
            # Fetch the top of the group[maxFrequency] stack and
            # pop the top of the group[maxFrequency] stack
            value = self.group[self.max_frequency].pop()

            # Decrement the frequency after the show has been popped
            self.frequency[value] -= 1

            if not self.group[self.max_frequency]:
                self.max_frequency -= 1
        else:
            return -1

        return value


# Driver code
def main():
    inputs = [5, 7, 7, 7, 4, 5, 3]
    obj = FreqStack()
    print("\t Input Stack: ", inputs, "\n", sep="")

    for i in inputs:
        obj.push(i)

    for i in range(len(inputs)):
        print(i + 1, ".\t Popping out the most frequent value... ", sep="")
        print("\t Value removed from stack is: ", obj.pop(), sep="")
        print("-" * 100)


if __name__ == "__main__":
    main()