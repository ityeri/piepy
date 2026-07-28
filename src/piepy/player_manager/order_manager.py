import random
from dataclasses import dataclass
from typing import Hashable


@dataclass(frozen=True)
class OrderManager[T: Hashable]:
    """
    is_loop, is_random_order field cannot be changed without .change_order_mode
    """

    elements: list[T]
    current_element: T | None
    next_element: T | None
    used_elements: set[T] | None

    is_loop: bool
    is_random_order: bool

    @staticmethod
    def create(elements: list[T], current_element: T | None, next_element: T | None, *, is_loop: bool, is_random_order: bool) -> OrderManager[T]:
        if is_random_order:
            used_elements = set()
        else:
            used_elements = None

        if current_element:
            if current_element not in elements:
                raise ValueError('Parameter value current_element does not included in elements')

        return OrderManager(
            elements=elements,
            current_element=current_element,
            next_element=next_element,
            used_elements=used_elements,

            is_loop=is_loop,
            is_random_order=is_random_order
        )

    def step(self) -> OrderManager[T]:
        if self.is_random_order:
            available_elements = set(self.elements) - self.used_elements

            if available_elements:
                next_element = random.choice(list(available_elements))
                used_elements = self.used_elements + {next_element}
            else:
                if self.is_loop:
                    next_element = random.choice(self.elements)
                    used_elements = set()
                else:
                    next_element = None
                    used_elements = self.used_elements

        else:
            if self.next_element is None:
                next_index = 0
            else:
                next_index = self.elements.index(self.next_element) + 1

            if len(self.elements) <= next_index:
                if self.is_loop:
                    next_element = self.elements[0]
                else:
                    next_element = None
            else:
                next_element = self.elements[next_index]

            used_elements = None

        return OrderManager(
            elements=self.elements,
            current_element=self.next_element,
            next_element=next_element,
            used_elements=used_elements,

            is_loop = self.is_loop,
            is_random_order = self.is_random_order
        )

    def change_order_mode(self, is_loop: bool, is_random_order: bool) -> OrderManager[T]:
        if is_random_order:
            if self.is_random_order: # If manager was a random order previously
                used_elements = self.used_elements
            else: # If manager wasn't a random order previously
                used_elements = set()
        else:
            used_elements = None

        return OrderManager(
            elements=self.elements,
            current_element=self.current_element,
            next_element=self.next_element,
            used_elements=used_elements,

            is_loop=is_loop,
            is_random_order=is_random_order
        )

    def goto(self, element: T) -> OrderManager[T]:
        if element not in self.elements:
            raise ValueError('Given element does not included in elements')

        return OrderManager(
            elements=self.elements,
            current_element=element,
            next_element=self.next_element,
            used_elements=self.used_elements,

            is_loop=self.is_loop,
            is_random_order=self.is_random_order
        )
    def set_next(self, element: T) -> OrderManager[T]:
        if element not in self.elements:
            raise ValueError('Given element does not included in elements')

        return OrderManager(
            elements=self.elements,
            current_element=self.current_element,
            next_element=element,
            used_elements=self.used_elements,

            is_loop=self.is_loop,
            is_random_order=self.is_random_order
        )
    def add_last(self, element: T) -> OrderManager[T]:
        return OrderManager(
            elements=self.elements + [element],
            current_element=self.current_element,
            next_element=self.next_element,
            used_elements=self.used_elements,

            is_loop=self.is_loop,
            is_random_order=self.is_random_order
        )
    def rm(self, element: T) -> OrderManager[T]:
        if element not in self.elements:
            raise ValueError('Given element does not included in elements')

        if element == self.current_element:
            raise ValueError('Given element is same as current_element')

        if self.used_elements is not None:
            used_elements = self.used_elements - {element}
        else:
            used_elements = None

        return OrderManager(
            elements=[e for e in self.elements if e != element],
            current_element=self.current_element,
            next_element=self.next_element,
            used_elements=used_elements,

            is_loop=self.is_loop,
            is_random_order=self.is_random_order
        )
