from dataclasses import dataclass
from typing import Iterator, List

@dataclass
class Item:
    timestamp: int
    value: str

class SlidingWindow:
    def __init__(self, stream: Iterator[Item], window_width: int):
        self.stream = stream
        self.window_width = window_width
        self.buffer = []

    def __iter__(self):
        return self

    def __next__(self) -> List[Item]:
        # Add items from the stream to the buffer
        while True:
            try:
                item = next(self.stream)
                self.buffer.append(item)
            except StopIteration:
                break  # Stop adding when the stream is exhausted

            # Remove items from the buffer that fall outside the window width
            while self.buffer and self.buffer[-1].timestamp - self.buffer[0].timestamp > self.window_width:
                self.buffer.pop(0)

            # Yield the current window if it's not empty
            if self.buffer:
                return list(self.buffer)

        # Once the stream is exhausted, handle any remaining items in the buffer
        if not self.buffer:
            raise StopIteration

# Test Example
stream_lst = [
    Item(1, "a"),
    Item(3, "b"),
    Item(6, "c"),
    Item(7, "d"),
    Item(8, "e"),
    Item(10, "f"),
    Item(14, "g"),
]

# Create a sliding window iterator
sliding_window = SlidingWindow(stream=iter(stream_lst), window_width=5)

# Iterate through the sliding windows
for window in sliding_window:
    print(window)
