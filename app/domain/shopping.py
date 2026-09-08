from dataclasses import dataclass


@dataclass(frozen=True)
class ShoppingList:
    list_id: int
    items: tuple[str, ...]
