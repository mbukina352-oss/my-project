"""Подбор квартир, ближайших к запросу по цене и площади."""
from .models import Flat
from .query import Query


def pick_flats(flats: list[Flat], q: Query, price_tol: float, area_tol: float, limit: int) -> list[Flat]:
    def fits(f: Flat) -> bool:
        if q.rooms is not None and f.rooms is not None and f.rooms != q.rooms:
            return False
        if q.price and f.price and f.price > q.price * (1 + price_tol):
            return False
        if q.area and f.area and abs(f.area - q.area) > q.area * area_tol:
            return False
        return bool(f.plan_url or f.plan_image)

    def distance(f: Flat) -> float:
        d = 0.0
        if q.area and f.area:
            d += abs(f.area - q.area) / q.area
        if q.price and f.price:
            d += abs(f.price - q.price) / q.price
        return d

    return sorted(filter(fits, flats), key=distance)[:limit]


def closest_flats(flats: list[Flat], q: Query, limit: int) -> list[Flat]:
    """Запасной вариант, когда под допуски ничего не подошло: просто ближайшие."""
    return pick_flats(flats, q, price_tol=10**6, area_tol=10**6, limit=limit)
