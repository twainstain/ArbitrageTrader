def sort_colors_official(colors):
    # Initialize the start, current, and end pointers
    start, current, end = 0, 0, len(colors) - 1

    # Iterate through the list until the current pointer exceeds the end pointer
    while current <= end:
        if colors[current] == 0:
            # If the current element is 0, swap it with the element at the start pointer
            colors[start], colors[current] = colors[current], colors[start]
            # Move both the start and current pointers one position forward
            current += 1
            start += 1

        elif colors[current] == 1:
            # If the current element is 1, just move the current pointer one position forward
            current += 1

        else:
            # If the current element is 2, swap it with the element at the end pointer
            colors[current], colors[end] = colors[end], colors[current]
            # Move the end pointer one position backward
            end -= 1
    return colors


def swap(index_a ,index_b , array):
    temp_value = array[index_a]
    array[index_a] = array[index_b]
    array[index_b] = temp_value

def sort_colors(colors):

    start = 0
    end = len(colors) -1
    current = 0
    while(current<= end):
        print(f"start={start}, current ={current}, end = {end}")
        if colors[current] == 0:
            colors[current], colors[start] = colors[start], colors[current]
            start += 1
            current += 1
        elif colors[current] == 2:
            colors[current], colors[end] = colors[end], colors[current]
            end -= 1
        else :
            current += 1

    return colors