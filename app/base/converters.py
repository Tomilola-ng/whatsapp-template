"""Shared conversion and datetime utilities."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from math import asin, cos, radians, sin, sqrt


def to_kobo(amount: Decimal | float) -> int:
    """Convert NGN amount to integer kobo value."""
    decimal_amount = Decimal(str(amount))
    kobo = (decimal_amount * Decimal("100")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(kobo)


def from_kobo(amount: int) -> Decimal:
    """Convert integer kobo value to NGN Decimal amount."""
    return Decimal(amount) / Decimal("100")


def haversine_distance_km(
    lat1: Decimal, lon1: Decimal, lat2: Decimal, lon2: Decimal
) -> Decimal:
    """Calculate great-circle distance between two coordinates in kilometers."""
    earth_radius_km = 6371.0

    lat1_rad = radians(float(lat1))
    lon1_rad = radians(float(lon1))
    lat2_rad = radians(float(lat2))
    lon2_rad = radians(float(lon2))

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))

    return Decimal(str(earth_radius_km * c))


def decimal_to_str(value: Decimal | str) -> str:
    """Safely normalize Decimal-like values to a string representation."""
    if isinstance(value, str):
        return str(parse_decimal(value))
    return str(value)


def parse_decimal(value: Decimal | str) -> Decimal:
    """Parse decimal-like inputs and raise ValueError on invalid values."""
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"Invalid decimal value: {value}") from exc


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)
