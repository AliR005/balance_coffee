"""SQL только здесь (по AGENTS.md)."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
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


async def set_product_availability(
    session: AsyncSession, location_id: int, product_id: int, is_available: bool
) -> None:
    stmt = pg_insert(LocationProductAvailability).values(
        location_id=location_id, product_id=product_id, is_available=is_available
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["location_id", "product_id"], set_={"is_available": is_available}
    )
    await session.execute(stmt)
    await session.commit()


async def set_option_availability(
    session: AsyncSession, location_id: int, option_id: int, is_available: bool
) -> None:
    stmt = pg_insert(LocationOptionAvailability).values(
        location_id=location_id, option_id=option_id, is_available=is_available
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["location_id", "option_id"], set_={"is_available": is_available}
    )
    await session.execute(stmt)
    await session.commit()
