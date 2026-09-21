import pytest

from app.modules.menu.validation import (
    CatalogGroup,
    CatalogOption,
    CatalogProduct,
    ValidationError,
    validate_line,
    validate_order_total_units,
)


def make_product() -> CatalogProduct:
    # size (required, 1), syrup (0..2)
    return CatalogProduct(
        id=1,
        base_price=32000,
        groups={
            10: CatalogGroup(id=10, min_select=1, max_select=1, option_ids=[1, 2, 3]),
            20: CatalogGroup(id=20, min_select=0, max_select=2, option_ids=[4, 5]),
        },
        options={
            1: CatalogOption(id=1, group_id=10, price_delta=-3000),
            2: CatalogOption(id=2, group_id=10, price_delta=0),
            3: CatalogOption(id=3, group_id=10, price_delta=6000),
            4: CatalogOption(id=4, group_id=20, price_delta=4000),
            5: CatalogOption(id=5, group_id=20, price_delta=4000),
        },
    )


def test_ok_returns_deltas() -> None:
    assert validate_line(make_product(), [2, 4], 1) == [0, 4000]


def test_missing_required_group() -> None:
    with pytest.raises(ValidationError) as e:
        validate_line(make_product(), [4], 1)
    assert e.value.code == "validation_error"


def test_too_many_in_single_group() -> None:
    with pytest.raises(ValidationError):
        validate_line(make_product(), [1, 2], 1)


def test_max_select_boundary_ok() -> None:
    assert validate_line(make_product(), [2, 4, 5], 1) == [0, 4000, 4000]


def test_foreign_option() -> None:
    p = make_product()
    p.options[99] = CatalogOption(id=99, group_id=999, price_delta=0)
    with pytest.raises(ValidationError) as e:
        validate_line(p, [2, 99], 1)
    assert e.value.code == "validation_error"


def test_unknown_option() -> None:
    with pytest.raises(ValidationError):
        validate_line(make_product(), [2, 777], 1)


def test_unavailable_product() -> None:
    p = make_product()
    p.available = False
    with pytest.raises(ValidationError) as e:
        validate_line(p, [2], 1)
    assert e.value.code == "product_unavailable"


def test_unavailable_option() -> None:
    p = make_product()
    p.unavailable_option_ids = {4}
    with pytest.raises(ValidationError) as e:
        validate_line(p, [2, 4], 1)
    assert e.value.code == "option_unavailable"


def test_inactive_product() -> None:
    p = make_product()
    p.is_active = False
    with pytest.raises(ValidationError):
        validate_line(p, [2], 1)


def test_quantity_limits() -> None:
    with pytest.raises(ValidationError):
        validate_line(make_product(), [2], 0)
    with pytest.raises(ValidationError):
        validate_line(make_product(), [2], 11)


def test_order_units_limit() -> None:
    validate_order_total_units(20)
    with pytest.raises(ValidationError):
        validate_order_total_units(21)
