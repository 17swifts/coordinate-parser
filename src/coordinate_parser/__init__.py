"""
Coordinate Parser - A Python library for parsing geographic coordinates.

Supports decimal degrees, degrees/minutes/seconds, maritime coordinate formats,
and UTM coordinates.
"""

from .parser import (
    parse_coordinate,
    parse_utm_coordinate,
    parse_utm_coordinate_single,
    to_dec_deg,
    utm_to_latlon,
)

__version__ = "0.1.1"
__all__ = [
    "parse_coordinate",
    "to_dec_deg",
    "parse_utm_coordinate",
    "utm_to_latlon",
    "parse_utm_coordinate_single",
]
