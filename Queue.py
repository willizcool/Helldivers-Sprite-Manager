class Queue:
    def __init__(self):
        """Initialize an empty queue backed by a list."""
        self._items = []

    def is_empty(self):
        """Check if the queue is empty."""
        return len(self._items) == 0

    def push(self, item):
        """Add an item to the end of the queue."""
        self._items.append(item)

    def dequeue(self):
        """Remove and return the item from the front of the queue."""
        if self.is_empty():
            raise IndexError("Dequeue from an empty queue.")
        return self._items.pop(0)

    def peek(self):
        """Return the item at the front of the queue without removing it."""
        if self.is_empty():
            raise IndexError("Peek from an empty queue.")
        return self._items[0]

    def size(self):
        """Return the number of items in the queue."""
        return len(self._items)

    def get_all_items(self):
        """Return a copy of all items currently in the queue."""
        return list(self._items)

    def clear(self):
        """Remove all items from the queue."""
        self._items.clear()