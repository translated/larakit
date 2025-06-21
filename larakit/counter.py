from typing import Generic, TypeVar, Dict, List, Optional, Iterable, Iterator, Callable, Tuple

T = TypeVar('T')


class Counter(Generic[T]):
    class _Countable:
        def __init__(self, item: T):
            self._item: T = item
            self._value: int = 0

        @property
        def item(self) -> T:
            return self._item

        @property
        def value(self) -> int:
            return self._value

        def incr(self, value: int = 1) -> None:
            self._value += value

        def __lt__(self, other: 'Counter._Countable') -> bool:
            return self.value < other.value

        def __eq__(self, other: 'Counter._Countable') -> bool:
            return self.value == other.value

        def __hash__(self) -> int:
            return hash((self.item, self.value))

    def __init__(self):
        self._map: Dict[T, 'Counter._Countable'] = {}
        self._total_count: int = 0
        self._values: Optional[List['Counter._Countable']] = None
        self._items: Optional[List[T]] = None

    @property
    def map(self) -> Dict[T, 'Counter._Countable']:
        return self._map

    @property
    def total_count(self) -> int:
        return self._total_count

    @property
    def values(self) -> List['Counter._Countable']:
        if self._values is None:
            values = list(self.map.values())
            values.sort(reverse=True)
            self._values = values
        return self._values

    @property
    def items(self) -> List[T]:
        if self._items is None:
            self._items = [e.item for e in self.values]
        return self._items

    def items_count(self) -> List[Tuple[T, int]]:
        return [(item, countable.value) for item, countable in self.map.items()]

    def invalidate_cache(self) -> None:
        self._values = None
        self._items = None

    def size(self) -> int:
        return len(self.map)

    def is_empty(self) -> bool:
        return len(self.map) == 0

    def count(self, item: T, value: int = 1) -> None:
        if value > 0:
            if item not in self.map:
                self.map[item] = self._Countable(item)
            self.map[item].incr(value)
            self._total_count += value
            self.invalidate_cache()

    def get(self, item: T) -> int:
        countable = self._map.get(item)
        return 0 if countable is None else countable.value

    def __iter__(self) -> Iterator['Counter._Countable']:
        return iter(self.values)

    def unsorted_entries(self) -> Iterable['Counter._Countable']:
        return self.map.values()

    def remove_if(self, predicate: Callable[['Counter._Countable'], bool]) -> None:
        to_remove = [key for key, countable in self.map.items() if predicate(countable)]
        for key in to_remove:
            self._total_count -= self._map[key].value
            del self.map[key]
            self.invalidate_cache()

    def top(self) -> Optional[T]:
        values = self.values
        return None if not values else values[0].item

    def top_entry(self) -> Optional['Counter._Countable']:
        values = self.values
        return None if not values else values[0]

    def get_total_count(self) -> int:
        return self._total_count

    def __str__(self) -> str:
        str_entries = [f'{e.item}:{e.value}' for e in self.values]
        entries = ','.join(str_entries)
        return f'{self.__class__.__name__}({self._total_count}){{{entries}}}'
