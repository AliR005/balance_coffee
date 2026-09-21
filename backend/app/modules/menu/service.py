"""Логика меню: сборка ответа, quote. Без SQL и без HTTP."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.time import is_open_now
from app.modules.menu import pricing, validation
from app.modules.menu.models import (
    Location,
    Option,
    OptionGroup,
    Product,
    ProductOptionGroup,
)
from app.modules.menu.repository import get_location, list_locations, menu_snapshot
from app.modules.menu.schemas import (
    CategoryOut,
    GroupOut,
    LocationOut,
    MenuOut,
    OptionOut,
    ProductOut,
    QuoteIn,
    QuoteLineOut,
    QuoteOut,
)
from app.modules.menu.validation import (
    CatalogGroup,
    CatalogOption,
    CatalogProduct,
    ValidationError,
)


def location_out(loc: Location, now_utc: datetime) -> LocationOut:
    return LocationOut(
        id=loc.id,
        code=loc.code,
        name=loc.name,
        address=loc.address or "",
        timezone=loc.timezone,
        is_open_now=is_open_now(loc.opening_hours, loc.timezone, now_utc),
    )


async def get_locations(session: AsyncSession, now_utc: datetime) -> list[LocationOut]:
    locs = await list_locations(session)
    return [location_out(loc, now_utc) for loc in locs]


def _catalog(snapshot: dict[str, Any], location_id: int) -> dict[int, CatalogProduct]:
    prod_av: dict[int, bool] = snapshot["prod_av"]
    opt_av: dict[int, bool] = snapshot["opt_av"]
    groups_by_id: dict[int, OptionGroup] = {g.id: g for g in snapshot["groups"]}
    opts_by_group: dict[int, list[Option]] = {}
    for o in snapshot["options"]:
        opts_by_group.setdefault(o.group_id, []).append(o)
    pog_by_product: dict[int, list[ProductOptionGroup]] = {}
    for p in snapshot["pogs"]:
        pog_by_product.setdefault(p.product_id, []).append(p)

    catalog: dict[int, CatalogProduct] = {}
    for p in snapshot["products"]:
        options: dict[int, CatalogOption] = {}
        groups: dict[int, CatalogGroup] = {}
        unavailable: set[int] = set()
        for pog in pog_by_product.get(p.id, []):
            g = groups_by_id[pog.group_id]
            gopts = opts_by_group.get(g.id, [])
            options.update(
                {
                    o.id: CatalogOption(id=o.id, group_id=g.id, price_delta=o.price_delta)
                    for o in gopts
                }
            )
            for o in gopts:
                if opt_av.get(o.id) is False:
                    unavailable.add(o.id)
            groups[g.id] = CatalogGroup(
                id=g.id,
                min_select=pog.min_select if pog.min_select is not None else g.min_select,
                max_select=pog.max_select if pog.max_select is not None else g.max_select,
                option_ids=[o.id for o in gopts],
                default_option_ids=list(pog.default_option_ids or []),
            )
        catalog[p.id] = CatalogProduct(
            id=p.id,
            base_price=p.base_price,
            is_active=p.is_active,
            available=prod_av.get(p.id, True),
            groups=groups,
            options=options,
            unavailable_option_ids=unavailable,
        )
    return catalog


async def get_menu(session: AsyncSession, location_id: int) -> MenuOut:
    loc = await get_location(session, location_id)
    if loc is None or not loc.is_active:
        raise ValidationError("not_found", "Location not found", {"location_id": location_id})
    snap = await menu_snapshot(session, location_id)
    groups_by_id: dict[int, OptionGroup] = {g.id: g for g in snap["groups"]}
    opts_by_group: dict[int, list[Option]] = {}
    for o in snap["options"]:
        opts_by_group.setdefault(o.group_id, []).append(o)
    pog_by_product: dict[int, list[ProductOptionGroup]] = {}
    for p in snap["pogs"]:
        pog_by_product.setdefault(p.product_id, []).append(p)
    opt_av: dict[int, bool] = snap["opt_av"]
    prod_av: dict[int, bool] = snap["prod_av"]

    categories: list[CategoryOut] = []
    for c in snap["categories"]:
        products: list[ProductOut] = []
        for p in [x for x in snap["products"] if x.category_id == c.id]:
            groups: list[GroupOut] = []
            for pog in sorted(pog_by_product.get(p.id, []), key=lambda x: x.sort):
                g = groups_by_id[pog.group_id]
                gopts = opts_by_group.get(g.id, [])
                lo = pog.min_select if pog.min_select is not None else g.min_select
                hi = pog.max_select if pog.max_select is not None else g.max_select
                groups.append(
                    GroupOut(
                        id=g.id,
                        key=g.key,
                        name=g.name,
                        min_select=lo,
                        max_select=hi,
                        required=lo >= 1,
                        default_option_ids=list(pog.default_option_ids or []),
                        options=[
                            OptionOut(
                                id=o.id,
                                name=o.name,
                                price_delta=o.price_delta,
                                visual=o.visual,
                                available=opt_av.get(o.id, True),
                            )
                            for o in gopts
                        ],
                    )
                )
            products.append(
                ProductOut(
                    id=p.id,
                    slug=p.slug,
                    name=p.name,
                    description=p.description or "",
                    base_price=p.base_price,
                    image_url=p.image_url or "",
                    video_url=p.video_url or "",
                    poster_url=p.poster_url or "",
                    video_duration_sec=p.video_duration_sec,
                    video_steps=p.video_steps,
                    tags=list(p.tags or []),
                    prep_units=p.prep_units,
                    available=prod_av.get(p.id, True),
                    groups=groups,
                )
            )
        categories.append(CategoryOut(id=c.id, slug=c.slug, name=c.name, products=products))
    return MenuOut(location_id=location_id, categories=categories)


async def quote(session: AsyncSession, location_id: int, payload: QuoteIn) -> QuoteOut:
    loc = await get_location(session, location_id)
    if loc is None or not loc.is_active:
        raise ValidationError("not_found", "Location not found", {"location_id": location_id})
    snap = await menu_snapshot(session, location_id)
    catalog = _catalog(snap, location_id)
    products_by_id: dict[int, Product] = {p.id: p for p in snap["products"]}

    lines: list[QuoteLineOut] = []
    line_totals: list[int] = []
    total_units = 0
    for item in payload.items:
        product = catalog.get(item.product_id)
        if product is None:
            raise ValidationError(
                "validation_error", "Unknown product", {"product_id": item.product_id}
            )
        deltas = validation.validate_line(product, list(item.option_ids), item.quantity)
        unit = pricing.unit_price(product.base_price, deltas)
        line = pricing.line_total(unit, item.quantity)
        lines.append(
            QuoteLineOut(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=unit,
                line_total=line,
            )
        )
        line_totals.append(line)
        total_units += item.quantity * products_by_id[item.product_id].prep_units

    validation.validate_order_total_units(total_units)

    return QuoteOut(
        lines=lines,
        total=pricing.order_total(line_totals),
        currency=settings.default_currency,
    )


def now_utc() -> datetime:
    return datetime.now(UTC)
