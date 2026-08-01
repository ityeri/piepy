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

    def _get_next_element_of(
            self,
            current_element: T | None,
            elements: list[T] | None = None,
            used_elements: set[T] | None = None
    ) -> T | None:
        elements = elements if elements is not None else self.elements

        if self.is_random_order:
            effective_used = used_elements if used_elements is not None else self.used_elements
            available = set(elements) - (effective_used | {current_element})

            if available:
                return random.choice(list(available))
            elif self.is_loop:
                return random.choice(elements)
            else:
                return None

        else:
            if current_element is None:
                next_index = 0
            else:
                next_index = elements.index(current_element) + 1

            if len(elements) <= next_index:
                if self.is_loop:
                    return elements[0]
                else:
                    return None
            else:
                return elements[next_index]

    def step(self) -> OrderManager[T]:
        if self.is_random_order:
            next_target_element = {self.next_element} if self.next_element is not None else set()
            tentative_used = self.used_elements | next_target_element

            if not set(self.elements) - tentative_used and self.is_loop:
                new_used = set()
                next_element = self._get_next_element_of(None, used_elements=new_used)
            else:
                new_used = tentative_used
                next_element = self._get_next_element_of(self.next_element, used_elements=new_used)
        else:
            new_used = None
            next_element = self._get_next_element_of(self.next_element, new_used)

        return OrderManager(
            elements=self.elements,
            current_element=self.next_element,
            next_element=next_element,
            used_elements=new_used,

            is_loop=self.is_loop,
            is_random_order=self.is_random_order
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

    def update_next_element(self) -> OrderManager[T]:
        return OrderManager(
            elements=self.elements,
            current_element=self.current_element,
            next_element=self._get_next_element_of(self.current_element),
            used_elements=self.used_elements,

            is_loop=self.is_loop,
            is_random_order=self.is_random_order
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

        new_elements = [e for e in self.elements if e != element]

        if self.used_elements is not None:
            used_elements = self.used_elements - {element}
        else:
            used_elements = None

        if self.next_element == element:
            next_element = self._get_next_element_of(
                self.current_element,
                elements=new_elements,
                used_elements={used_elements}
            )
        else:
            next_element = self.next_element

        return OrderManager(
            elements=new_elements,
            current_element=self.current_element,
            next_element=next_element,
            used_elements=used_elements,

            is_loop=self.is_loop,
            is_random_order=self.is_random_order
        )
