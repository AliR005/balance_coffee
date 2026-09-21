"""Валидация выбора опций (SPEC 5.2–5.3). Чистые функции поверх снапшота каталога."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CatalogOption:
    id: int
    group_id: int
    price_delta: int = 0


@dataclass
class CatalogGroup:
    id: int
    min_select: int = 0
    max_select: int = 1
    option_ids: list[int] = field(default_factory=list)
    default_option_ids: list[int] = field(default_factory=list)


@dataclass
class CatalogProduct:
    id: int
    base_price: int
    is_active: bool = True
    available: bool = True
    groups: dict[int, CatalogGroup] = field(default_factory=dict)
    options: dict[int, CatalogOption] = field(default_factory=dict)
    unavailable_option_ids: set[int] = field(default_factory=set)


class ValidationError(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


MAX_QTY_PER_LINE = 10
MAX_UNITS_PER_ORDER = 20


def validate_line(product: CatalogProduct, option_ids: list[int], quantity: int) -> list[int]:
    """Возвращает deltas выбранных опций. Бросает ValidationError с кодом из SPEC."""
    if not product.is_active:
        raise ValidationError(
            "validation_error", "Product is not active", {"product_id": product.id}
        )
    if not product.available:
        raise ValidationError(
            "product_unavailable",
            "Product unavailable at location",
            {"product_id": product.id},
        )
    if not 1 <= quantity <= MAX_QTY_PER_LINE:
        raise ValidationError("validation_error", "Quantity must be 1..10", {"quantity": quantity})

    by_group: dict[int, list[int]] = {}
    for oid in option_ids:
        opt = product.options.get(oid)
        if opt is None:
            raise ValidationError(
                "validation_error",
                "Option does not belong to product",
                {"option_id": oid},
            )
        if oid in product.unavailable_option_ids:
            raise ValidationError(
                "option_unavailable",
                "Option unavailable at location",
                {"option_id": oid},
            )
        by_group.setdefault(opt.group_id, []).append(oid)

    for gid, group in product.groups.items():
        chosen = by_group.get(gid, [])
        # дубликаты одного option_id считаем выбором (для групп типа "доп. шот" не применимо,
        # там отдельные опции single/double)
        if len(chosen) != len(set(chosen)):
            raise ValidationError("validation_error", "Duplicate option", {"group_id": gid})
        if not group.min_select <= len(chosen) <= group.max_select:
            raise ValidationError(
                "validation_error",
                f"Group {gid}: need {group.min_select}..{group.max_select} options",
                {
                    "group_id": gid,
                    "min": group.min_select,
                    "max": group.max_select,
                    "chosen": len(chosen),
                },
            )

    unknown_groups = set(by_group) - set(product.groups)
    if unknown_groups:
        raise ValidationError(
            "validation_error",
            "Unknown option group",
            {"groups": sorted(unknown_groups)},
        )

    return [product.options[oid].price_delta for oid in option_ids]


def validate_order_total_units(total_units: int) -> None:
    if total_units > MAX_UNITS_PER_ORDER:
        raise ValidationError(
            "validation_error", "Too many units in order", {"total_units": total_units}
        )
