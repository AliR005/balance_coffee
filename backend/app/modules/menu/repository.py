"""SQL только здесь (по AGENTS.md)."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.menu.models import (
    Category,
    Location,
    LocationOptionAvailability,
    LocationProductAvailability,
    Option,
    OptionGroup,
    Product,
    ProductOptionGroup,
)


async def list_locations(session: AsyncSession) -> list[Location]:
    res = await session.execute(
        select(Location).where(Location.is_active.is_(True)).order_by(Location.id)
    )
    return list(res.scalars().all())


async def get_location(session: AsyncSession, location_id: int) -> Location | None:
    return await session.get(Location, location_id)


async def menu_snapshot(session: AsyncSession, location_id: int) -> dict[str, Any]:
    cats = (
        (await session.execute(select(Category).order_by(Category.sort, Category.id)))
        .scalars()
        .all()
    )
    prods = (await session.execute(select(Product).order_by(Product.id))).scalars().all()
    groups = (await session.execute(select(OptionGroup))).scalars().all()
    pogs = (await session.execute(select(ProductOptionGroup))).scalars().all()
    opts = (await session.execute(select(Option).order_by(Option.sort, Option.id))).scalars().all()
    prod_av = (
        (
            await session.execute(
                select(LocationProductAvailability).where(
                    LocationProductAvailability.location_id == location_id
                )
            )
        )
        .scalars()
        .all()
    )
    opt_av = (
        (
            await session.execute(
                select(LocationOptionAvailability).where(
                    LocationOptionAvailability.location_id == location_id
                )
            )
        )
        .scalars()
        .all()
    )
    return {
        "categories": list(cats),
        "products": list(prods),
        "groups": list(groups),
        "pogs": list(pogs),
        "options": list(opts),
        "prod_av": {r.product_id: r.is_available for r in prod_av},
        "opt_av": {r.option_id: r.is_available for r in opt_av},
    }
