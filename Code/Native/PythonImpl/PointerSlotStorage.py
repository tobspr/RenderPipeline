
from six.moves import range

class PointerSlotStorage(object):

    def __init__(self, max_size):
        self._data = [None] * max_size
        self._max_index = 0
        self._num_entries = 0

    def get_max_index(self):
        return self._max_index

    def get_num_entries(self):
        return self._num_entries

    def find_slot(self):
        # Notice: returns None in case of no free slot, and the slot otherwise, this
        # is different to the C++ Module
        for i, v in enumerate(self._data):
            if not v:
                return i
        return -1

    def find_consecutive_slots(self, num_consecutive):
        if num_consecutive == 1:
            return self.find_slot()

        for i, v in enumerate(self._data):
            any_taken = False
            for k in range(num_consecutive):
                if self._data[i + k]:
                    any_taken = True
                    break
            if not any_taken:
                return i
        return -1

    def free_slot(self, slot):
        self._data[slot] = None
        self._num_entries -= 1
        if slot == self._max_index:
            while self._max_index >= 0 and not self._data[self._max_index]:
                self._max_index -= 1

    def free_consecutive_slots(self, slot, num_consecutive):
        for i in range(num_consecutive):
            self.free_slot(slot + i)

    def reserve_slot(self, slot, ptr):
        self._max_index = max(self._max_index, slot)
        self._data[slot] = ptr
        self._num_entries += 1

    def begin(self):
        for i in range(self._max_index + 1):
            yield self._data[i]

    def end(self):
        raise NotImplementedError("Use .begin() as iterator when using the python side!")
