"""Чистый расчёт цены. Тот же алгоритм обязан использовать фронт (SPEC 5.1)."""


def unit_price(base_price: int, deltas: list[int]) -> int:
    total = base_price + sum(deltas)
    return max(total, 0)


def line_total(unit: int, quantity: int) -> int:
    return unit * quantity


def order_total(lines: list[int]) -> int:
    return sum(lines)
