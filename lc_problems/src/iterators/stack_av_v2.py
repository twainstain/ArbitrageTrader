"""The
user
configuration
defines
the
time
width
of
each
chunk
that
our
data
structure
will
be
returning.
A
width
of
10
means
that
our
iterator
will
be
returning
all
contiguous
list
of
items
from the stream

where
the
timestamp
difference
between
the
first and last
item in the
list is at
most
10.

Figure
out
the
interfaces
for the following:
    - Stream
    object - what is type? how
    do
    you
    iterate
    over
    it?
    - User
    configuration - what
    fields? what is important
    to
    be
    configured?
    - The
    data
    structure - what is the
    API?

    Goal: Implement
    the
    data
    structure and get
    it
    running
    on
    test
    examples
    before
    the
    interview
    ends(25
    minutes)

    Hint: You
    are
    implementing
    an
    iterator
    https: // wiki.python.org / moin / Iterator.
    """

from collections.abc import Iterator
from dataclasses import dataclass


@dataclass
class Item:
    timestamp: int
    value: str


stream_lst = [
    Item(1, "a"),
    Item(3, "b"),
    Item(6, "c"),
    Item(7, "d"),
    Item(8, "e"),
    Item(10, "f"),
    Item(14, "g"),
]


class SlidingWindow:
    def __init__(self, stream, window_width):
        self.stream = stream
        self.window_width = window_width
        self.start = 0
        self.buffer = []

    def __iter__(self):
        return self

    def __next__(self):
        try:
            start = self.start if self.start > 0 else next(self.stream).timestamp
            end = start + self.window_width
            #print(f"start ={start} , end = {end}")
            result = []
            while start < end:
                #print(start)
                result.append(start)
                start = next(self.stream).timestamp
            self.start = start
            #print(f"start ={start} , result = {result}")
            return result
        except StopIteration:
            raise StopIteration

    # Test Code

sliding_window = SlidingWindow(stream=iter(stream_lst), window_width=5)

for window in sliding_window:
    print(window)

    # expect this to return the following windows:
    # [Item(1, "a"),Item(3, "b"), Item(6, "c")]
    # [Item(7, "d"),Item(8, "e"), Item(9, "f")]
    # [Item(14, "g")
    # StopIteration