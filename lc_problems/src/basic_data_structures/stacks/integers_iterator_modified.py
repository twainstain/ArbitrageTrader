from nested_integers import NestedIntegers


class NestedIterator:

    # NestedIterator constructor initializes the stack using the
    # given nested_list list
    def __init__(self, nested_list:list):
        print(f"nested_list = {nested_list}")
        self.nested_list_stack = list(reversed([NestedIntegers(val) for val in nested_list]))

    # has_next() will return True if there are still some integers in the
    # stack (that has nested_list elements) and, otherwise, will return False.
    def has_next(self):
        # Iterate in the stack while the stack is not empty
        while len(self.nested_list_stack) > 0:
            # Save the top value of the stack
            top = self.nested_list_stack[-1]
            # Check if the top value is integer, if true return True,
            # if not continue
            if top.is_integer():
                print(f"in an integer")
                return True
            # If the top is not an integer, it must be the list of integers
            # Pop the list from the stack and save it in the top_list
            top_list = self.nested_list_stack.pop().get_list()
            # Save the length of the top_list in i and iterate in the list
            i = len(top_list) - 1
            print(f"in a list: i = {i}")
            while i >= 0:
                # Append the values of the nested list into the stack
                self.nested_list_stack.append(top_list[i])
                i -= 1
        return False

    # next will return the integer from the nested_list
    def next(self):
        # Check if there is still an integer in the stack
        if self.has_next():
            # If true pop and return the top of the stack
            return self.nested_list_stack.pop().get_integer()
        return None


# Driver code
def create_nested_iterator_structure(input_list):
    def parse_input(nested, input_list):
        if isinstance(input_list, int):
            nested.set_integer(input_list)
        else:
            for item in input_list:
                child = NestedIntegers()
                nested.add(child)
                parse_input(child, item)

    nested_structure = NestedIntegers()
    parse_input(nested_structure, input_list)
    return nested_structure

def create_nested_iterator_from_structure(nested_structure):
    def flatten(nested, result):
        if nested.is_integer():
            result.append(nested.get_integer())
        else:
            for child in nested.get_list():
                flatten(child, result)

    flattened_list = []
    flatten(nested_structure, flattened_list)
    return NestedIterator(flattened_list)


# Driver code
def main():

    inputs = [
        [1, [2, 3], 4],
        [3, [2, 3, 4], 4, [2, 3]],
        [[2, 3], 3, [2, 3], 4, [2, 3, 4, 5]],
        [1, [3, [4, [5, 6], 7], 8], 9],
        [[2, 3, [2, 3]]]
    ]
    test_case = NestedIterator([11,[12,13], 14])
    while test_case.has_next():
        print("\titr.next(): ", test_case.next())

    print("-" * 100)
    for i, test_case_input in enumerate(inputs, start=1):
        print(i, ".\tOriginal structure: ", inputs[i-1], sep="")
        print("\n\tOutput:\n")
        nested_structure = create_nested_iterator_structure(test_case_input)
        test_case = create_nested_iterator_from_structure(nested_structure)

        #result = []
        while test_case.has_next():
            print("\titr.next(): ", test_case.next())

        print("-"*100)

if __name__ == '__main__':
    main()