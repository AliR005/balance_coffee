from app.modules.menu import pricing


def test_unit_price_no_options() -> None:
    assert pricing.unit_price(32000, []) == 32000


def test_unit_price_with_options() -> None:
    assert pricing.unit_price(32000, [6000, 4000]) == 42000


def test_unit_price_negative_delta() -> None:
    assert pricing.unit_price(32000, [-3000]) == 29000


def test_unit_price_never_negative() -> None:
    assert pricing.unit_price(1000, [-5000]) == 0


def test_line_total_quantity() -> None:
    assert pricing.line_total(32000, 3) == 96000


def test_order_total() -> None:
    assert pricing.order_total([32000, 42000]) == 74000
