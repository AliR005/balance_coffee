"""Идемпотентный seed из seed/menu.yaml. Безопасно запускать повторно."""

import asyncio
import hashlib
import sys
from pathlib import Path

import yaml
from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.db import engine  # noqa: E402
from app.modules.menu.models import (  # noqa: E402
    Category,
    Location,
    LocationOptionAvailability,
    LocationProductAvailability,
    Option,
    OptionGroup,
    Product,
    ProductOptionGroup,
)


def pin_hash(pin: str) -> str:
    return "sha256:" + hashlib.sha256(pin.encode()).hexdigest()


async def main() -> None:
    from sqlalchemy.ext.asyncio import AsyncSession

    data = yaml.safe_load((BACKEND_ROOT / "seed" / "menu.yaml").read_text(encoding="utf-8"))

    async with AsyncSession(engine) as session:
        # --- option groups + options ---
        group_by_key: dict[str, OptionGroup] = {}
        for g in data.get("option_groups", []):
            obj = (
                await session.execute(select(OptionGroup).where(OptionGroup.key == g["key"]))
            ).scalar_one_or_none()
            if obj is None:
                obj = OptionGroup(
                    key=g["key"],
                    name=g["name"],
                    min_select=g.get("min_select", 0),
                    max_select=g.get("max_select", 1),
                )
                session.add(obj)
                await session.flush()
            else:
                obj.name = g["name"]
                obj.min_select = g.get("min_select", 0)
                obj.max_select = g.get("max_select", 1)
            group_by_key[g["key"]] = obj
            for idx, o in enumerate(g.get("options", [])):
                opt = (
                    await session.execute(
                        select(Option).where(Option.group_id == obj.id, Option.name == o["name"])
                    )
                ).scalar_one_or_none()
                if opt is None:
                    opt = Option(
                        group_id=obj.id,
                        name=o["name"],
                        price_delta=o.get("price_delta", 0),
                        sort=o.get("sort", idx),
                        visual=o.get("visual"),
                    )
                    session.add(opt)
                else:
                    opt.price_delta = o.get("price_delta", 0)
                    opt.sort = o.get("sort", idx)
                    opt.visual = o.get("visual")

        # --- categories ---
        cat_by_slug: dict[str, Category] = {}
        for c in data.get("categories", []):
            obj = (
                await session.execute(select(Category).where(Category.slug == c["slug"]))
            ).scalar_one_or_none()
            if obj is None:
                obj = Category(slug=c["slug"], name=c["name"], sort=c.get("sort", 0))
                session.add(obj)
                await session.flush()
            else:
                obj.name = c["name"]
                obj.sort = c.get("sort", 0)
            cat_by_slug[c["slug"]] = obj

        # --- products ---
        prod_by_slug: dict[str, Product] = {}
        for p in data.get("products", []):
            cat = cat_by_slug[p["category"]]
            obj = (
                await session.execute(select(Product).where(Product.slug == p["slug"]))
            ).scalar_one_or_none()
            fields = dict(
                category_id=cat.id,
                name=p["name"],
                description=p.get("description", ""),
                base_price=p["base_price"],
                image_url=p.get("image_url", ""),
                video_url=p.get("video_url", ""),
                poster_url=p.get("poster_url", ""),
                video_duration_sec=p.get("video_duration_sec"),
                video_steps=p.get("video_steps"),
                tags=p.get("tags", []),
                prep_units=p.get("prep_units", 1),
                is_active=p.get("is_active", True),
            )
            if obj is None:
                obj = Product(slug=p["slug"], **fields)  # type: ignore[arg-type]
                session.add(obj)
                await session.flush()
            else:
                for k, v in fields.items():
                    setattr(obj, k, v)
            prod_by_slug[p["slug"]] = obj

            # groups of product: replace set
            for old in (
                (
                    await session.execute(
                        select(ProductOptionGroup).where(ProductOptionGroup.product_id == obj.id)
                    )
                )
                .scalars()
                .all()
            ):
                await session.delete(old)
            await session.flush()
            # default option ids resolve by name
            for sort, g in enumerate(p.get("groups", [])):
                grp = group_by_key[g["key"]]
                defaults: list[int] = []
                for name in g.get("defaults", []):
                    opt = (
                        await session.execute(
                            select(Option).where(Option.group_id == grp.id, Option.name == name)
                        )
                    ).scalar_one_or_none()
                    if opt is not None:
                        defaults.append(opt.id)
                session.add(
                    ProductOptionGroup(
                        product_id=obj.id,
                        group_id=grp.id,
                        sort=sort,
                        default_option_ids=defaults,
                        min_select=g.get("min_select"),
                        max_select=g.get("max_select"),
                    )
                )
        await session.flush()

        # --- locations ---
        loc_by_code: dict[str, Location] = {}
        for loc in data.get("locations", []):
            obj = (
                await session.execute(select(Location).where(Location.code == loc["code"]))
            ).scalar_one_or_none()
            fields = dict(
                name=loc["name"],
                address=loc.get("address", ""),
                timezone=loc.get("timezone", "Europe/Moscow"),
                opening_hours=loc.get("opening_hours"),
                lead_time_min=loc.get("lead_time_min", 10),
                slot_step_min=loc.get("slot_step_min", 15),
                slot_capacity=loc.get("slot_capacity", 6),
                is_active=loc.get("is_active", True),
            )
            if obj is None:
                obj = Location(
                    code=loc["code"],
                    staff_pin_hash=pin_hash(loc["staff_pin"]) if loc.get("staff_pin") else None,
                    **fields,
                )  # type: ignore[arg-type]
                session.add(obj)
                await session.flush()
            else:
                for k, v in fields.items():
                    setattr(obj, k, v)
                if loc.get("staff_pin"):
                    obj.staff_pin_hash = pin_hash(loc["staff_pin"])
            loc_by_code[loc["code"]] = obj
        await session.flush()

        # --- availability: reset then apply ---
        for loc in loc_by_code.values():
            for old in (
                (
                    await session.execute(
                        select(LocationProductAvailability).where(
                            LocationProductAvailability.location_id == loc.id
                        )
                    )
                )
                .scalars()
                .all()
            ):
                await session.delete(old)
            for old in (
                (
                    await session.execute(
                        select(LocationOptionAvailability).where(
                            LocationOptionAvailability.location_id == loc.id
                        )
                    )
                )
                .scalars()
                .all()
            ):
                await session.delete(old)
        await session.flush()

        for rule in data.get("availability", []):
            loc = loc_by_code[rule["location"]]
            for slug in rule.get("unavailable_products", []):
                prod = prod_by_slug.get(slug)
                if prod is None:
                    print(f"WARN: unknown product {slug}")
                    continue
                session.add(
                    LocationProductAvailability(
                        location_id=loc.id, product_id=prod.id, is_available=False
                    )
                )
            for name in rule.get("unavailable_options", []):
                opt = (
                    await session.execute(select(Option).where(Option.name == name))
                ).scalar_one_or_none()
                if opt is None:
                    print(f"WARN: unknown option {name}")
                    continue
                session.add(
                    LocationOptionAvailability(
                        location_id=loc.id, option_id=opt.id, is_available=False
                    )
                )

        await session.commit()
        print("seed ok")


if __name__ == "__main__":
    asyncio.run(main())
