"""
Coordinate Parser - A Python library for parsing geographic coordinates.

Supports decimal degrees, degrees/minutes/seconds, and maritime coordinate formats.
"""

from .parser import parse_coordinate, to_dec_deg

__version__ = "0.1.1"
__all__ = ["parse_coordinate", "to_dec_deg"]
