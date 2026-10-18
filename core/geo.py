"""Геометрия: построение точек и полигонов для geography(…, 4326).

Порядок координат в PostGIS — (lon, lat); функции принимают (lat, lon), как в Telegram.
"""

import math

from geoalchemy2 import WKTElement

SRID = 4326
METERS_PER_DEG_LAT = 111_320.0


def point(lat: float, lon: float) -> WKTElement:
    """Точка для колонки geography(Point, 4326)."""
    return WKTElement(f"POINT({lon} {lat})", srid=SRID, extended=False)


def offset(lat: float, lon: float, north_m: float, east_m: float) -> tuple[float, float]:
    """Смещение точки на заданное число метров к северу и востоку (приближённо, < 10 км)."""
    dlat = north_m / METERS_PER_DEG_LAT
    dlon = east_m / (METERS_PER_DEG_LAT * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


def square(lat: float, lon: float, side_m: float) -> WKTElement:
    """Квадратный полигон со стороной side_m и центром в (lat, lon)."""
    h = side_m / 2
    corners = [offset(lat, lon, n, e) for n, e in ((h, -h), (h, h), (-h, h), (-h, -h), (h, -h))]
    ring = ", ".join(f"{c_lon} {c_lat}" for c_lat, c_lon in corners)
    return WKTElement(f"POLYGON(({ring}))", srid=SRID, extended=False)
