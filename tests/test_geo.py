"""Расстояния PostGIS по geography (метры) для точек из core/geo.py."""

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core import geo

pytestmark = pytest.mark.db

BASE = (53.9, 27.56)  # Минск


async def distance_m(
    session: AsyncSession, a: tuple[float, float], b: tuple[float, float]
) -> float:
    query = select(
        func.ST_Distance(
            func.ST_GeogFromText(geo.point(*a).desc), func.ST_GeogFromText(geo.point(*b).desc)
        )
    )
    return float(await session.scalar(query))


@pytest.mark.parametrize("meters", [0, 30, 49, 51, 300])
async def test_distance_north(session: AsyncSession, meters: float) -> None:
    other = geo.offset(*BASE, north_m=meters, east_m=0)
    assert await distance_m(session, BASE, other) == pytest.approx(meters, abs=0.5, rel=0.01)


async def test_distance_30m_east(session: AsyncSession) -> None:
    other = geo.offset(*BASE, north_m=0, east_m=30)
    assert await distance_m(session, BASE, other) == pytest.approx(30, abs=0.5)


async def test_point_order_lon_lat() -> None:
    """В PostGIS сначала долгота, потом широта."""
    assert geo.point(53.9, 27.56).desc == "POINT(27.56 53.9)"


async def test_square_area(session: AsyncSession) -> None:
    area = await session.scalar(
        select(func.ST_Area(func.ST_GeogFromText(geo.square(*BASE, 200).desc)))
    )
    assert float(area) == pytest.approx(40_000, rel=0.01)
