"""
Code for parsing lat-long coordinates in various formats.

Formats supported:

Decimal degrees:
   23.43
   -45.21

Decimal Degrees with quadrant:
   23.43 N
   45.21 W
   N 23.43
   W 45.21

Degrees, decimal minutes:
  23° 25.800'
  -45° 12.600'
  23 25.800'
  -45 12.600'
  23° 25.8' N
  45° 12.6' W

Degrees, Minutes, Seconds:
   23° 25' 48.0"
  -45° 12' 36.0"
   23d 25' 48.0"
  -45d 12' 36.0"
   23° 25' 48.0" N
  45° 12' 36.0" S

Maritime coordinate formats:
  40°–41.65'N, 139°-02.54'E (degree-dash-minutes with degree symbol)
  54-05.48N, 162-29.03W (degree-dash-minutes without degree symbol)
  30°34.4'N (degree-minutes with degree symbol)
  30°34'24.0"N (degree-minutes-seconds)

UTM coordinate formats:
  33N 0594934 5810062 (zone letter, easting, northing)
  Zone 18S 0377299 1483035 (with "Zone" prefix)
  33 N 594934 5810062 (with spaces)
  33N594934E5810062N (compact format)
"""

import math
import re
from decimal import Decimal


def utm_to_latlon(
    zone_number: int,
    zone_letter: str,
    easting: float,
    northing: float,
    validate: bool = True,
) -> tuple[float, float]:
    """
    Convert UTM coordinates to latitude/longitude.

    Args:
        zone_number: UTM zone number (1-60)
        zone_letter: UTM zone letter (C-X, excluding I and O)
        easting: UTM easting coordinate in meters
        northing: UTM northing coordinate in meters
        validate: Whether to validate the resulting coordinates are within valid ranges

    Returns:
        Tuple of (latitude, longitude) in decimal degrees

    Raises:
        ValueError: If UTM parameters are invalid or coordinates are outside valid
            ranges
    """
    # Validate inputs
    if not (1 <= zone_number <= 60):
        raise ValueError(f"UTM zone number {zone_number} must be between 1 and 60")

    zone_letter = zone_letter.upper()
    valid_letters = "CDEFGHJKLMNPQRSTUVW"  # X is excluded (only goes to W)
    if zone_letter not in valid_letters:
        raise ValueError(f"UTM zone letter '{zone_letter}' is invalid")

    # Determine if northern or southern hemisphere
    northern = zone_letter >= "N"

    # WGS84 ellipsoid parameters
    a = 6378137.0  # Semi-major axis (meters)
    e = 0.0818191908426215  # First eccentricity
    e_sq = e * e  # e squared
    e1_sq = e_sq / (1 - e_sq)  # e prime squared
    k0 = 0.9996  # Scale factor

    # Calculate central meridian longitude
    lon_origin_deg = (zone_number - 1) * 6 - 180 + 3
    lon_origin_rad = math.radians(lon_origin_deg)

    # Remove false easting and northing
    x = easting - 500000.0
    if not northern:
        y = northing - 10000000.0
    else:
        y = northing

    # Calculate the meridional arc
    M = y / k0

    # Calculate the footprint latitude using series expansion
    mu = M / (a * (1 - e_sq / 4 - 3 * e_sq**2 / 64 - 5 * e_sq**3 / 256))

    e1 = (1 - math.sqrt(1 - e_sq)) / (1 + math.sqrt(1 - e_sq))
    J1 = 3 * e1 / 2 - 27 * e1**3 / 32
    J2 = 21 * e1**2 / 16 - 55 * e1**4 / 32
    J3 = 151 * e1**3 / 96
    J4 = 1097 * e1**4 / 512

    fp = (
        mu
        + J1 * math.sin(2 * mu)
        + J2 * math.sin(4 * mu)
        + J3 * math.sin(6 * mu)
        + J4 * math.sin(8 * mu)
    )

    # Calculate latitude and longitude
    C1 = e1_sq * math.cos(fp) ** 2
    T1 = math.tan(fp) ** 2
    R1 = a * (1 - e_sq) / (1 - e_sq * math.sin(fp) ** 2) ** (3 / 2)
    N1 = a / math.sqrt(1 - e_sq * math.sin(fp) ** 2)
    D = x / (N1 * k0)

    # Calculate latitude
    Q1 = N1 * math.tan(fp) / R1
    Q2 = D**2 / 2
    Q3 = (5 + 3 * T1 + 10 * C1 - 4 * C1**2 - 9 * e1_sq) * D**4 / 24
    Q4 = (61 + 90 * T1 + 298 * C1 + 45 * T1**2 - 252 * e1_sq - 3 * C1**2) * D**6 / 720

    lat_rad = fp - Q1 * (Q2 - Q3 + Q4)

    # Calculate longitude
    Q5 = D
    Q6 = (1 + 2 * T1 + C1) * D**3 / 6
    Q7 = (5 - 2 * C1 + 28 * T1 - 3 * C1**2 + 8 * e1_sq + 24 * T1**2) * D**5 / 120

    lon_rad = lon_origin_rad + (Q5 - Q6 + Q7) / math.cos(fp)

    # Convert from radians to degrees
    lat = math.degrees(lat_rad)
    lon = math.degrees(lon_rad)

    # Apply validation if requested
    if validate:
        lat_decimal = _validate_coordinate(Decimal(str(lat)), "latitude")
        lon_decimal = _validate_coordinate(Decimal(str(lon)), "longitude")
        if lat_decimal is None or lon_decimal is None:
            raise ValueError("Converted coordinates are outside valid ranges")
        return float(lat_decimal), float(lon_decimal)

    return lat, lon


def parse_utm_coordinate(
    utm_string: str, validate: bool = True
) -> tuple[float, float] | None:
    """
    Parse UTM coordinate string and return latitude/longitude.

    Supports formats like:
    - "33N 0594934 5810062"
    - "18S 0377299 1483035"
    - "Zone 33N 594934 5810062"
    - "33N594934E5810062N" (compact format)

    Args:
        utm_string: UTM coordinate string
        validate: Whether to validate the resulting coordinates are within valid ranges

    Returns:
        Tuple of (latitude, longitude) in decimal degrees, or None if parsing fails

    Raises:
        ValueError: If validation is enabled and coordinates are outside valid ranges
    """
    utm_string = utm_string.strip().upper()

    # Valid UTM zone letters (excluding I, O, and X)
    zone_letters = "CDEFGHJKLMNPQRSTUVW"

    # Pattern 1: Standard format with optional "Zone" prefix
    # "Zone 33N 594934 5810062" or "33N 594934 5810062"
    pattern1 = (
        rf"^(?:ZONE\s+)?(\d{{1,2}})([{zone_letters}])\s+(\d{{6,7}})\s+(\d{{7,8}})$"
    )

    # Pattern 2: Compact format with E/N suffixes
    # "33N594934E5810062N"
    pattern2 = rf"^(\d{{1,2}})([{zone_letters}])(\d{{6,7}})E(\d{{7,8}})N$"

    # Pattern 3: Alternative spacing
    # "33 N 594934 5810062"
    pattern3 = (
        rf"^(?:ZONE\s+)?(\d{{1,2}})\s+([{zone_letters}])\s+(\d{{6,7}})\s+(\d{{7,8}})$"
    )

    for pattern in [pattern1, pattern2, pattern3]:
        match = re.match(pattern, utm_string)
        if match:
            zone_number = int(match.group(1))
            zone_letter = match.group(2)
            easting = float(match.group(3))
            northing = float(match.group(4))

            try:
                return utm_to_latlon(
                    zone_number, zone_letter, easting, northing, validate
                )
            except ValueError:
                # Invalid UTM parameters or validation failed
                return None

    return None


def parse_utm_coordinate_single(
    utm_string: str, coord_type: str = "latitude", validate: bool = True
) -> Decimal | None:
    """
    Parse UTM coordinate string and return a single coordinate (latitude or longitude).

    This function works similarly to parse_coordinate but for UTM inputs, allowing you
    to extract just the latitude or longitude from a UTM coordinate string.

    Args:
        utm_string: UTM coordinate string (e.g., "33N 391545 5819698")
        coord_type: Type of coordinate to return ('latitude' or 'longitude')
        validate: Whether to validate the coordinate is within valid ranges

    Returns:
        Decimal value representing the requested coordinate in decimal degrees,
        or None if parsing fails

    Raises:
        ValueError: If validation is enabled and coordinate is outside valid range

    Example:
        >>> lat = parse_utm_coordinate_single("33N 391545 5819698", "latitude")
        >>> lon = parse_utm_coordinate_single("33N 391545 5819698", "longitude")
    """
    result = parse_utm_coordinate(utm_string, validate)
    if result is None:
        return None

    lat, lon = result

    if coord_type.lower() == "longitude":
        return Decimal(str(lon))
    else:  # Default to latitude
        return Decimal(str(lat))


def to_dec_deg(*args: float) -> float:
    """Convert degrees, minutes, seconds to decimal degrees.

    Args:
        *args: Variable arguments representing degrees, minutes (optional),
            seconds (optional)

    Returns:
        Decimal degrees as float
    """
    if len(args) == 1:
        return float(args[0])
    elif len(args) == 2:
        degrees, minutes = args
        return float(degrees) + float(minutes) / 60.0
    elif len(args) == 3:
        degrees, minutes, seconds = args
        return float(degrees) + float(minutes) / 60.0 + float(seconds) / 3600.0
    else:
        raise ValueError("Invalid number of arguments")


def parse_coordinate(
    string: str | float | Decimal | None,
    coord_type: str = "coordinate",
    validate: bool = True,
) -> Decimal | None:
    """
    Attempts to parse a latitude or longitude string with optional validation.

    Returns the value in decimal degrees.

    If parsing fails, it raises a ValueError.

    Args:
        string: The coordinate string to parse
        coord_type: Type of coordinate ('latitude', 'longitude', or 'coordinate')
        validate: Whether to validate the coordinate is within valid ranges

    Returns:
        A Decimal value representing degrees.
        Negative for southern or western hemisphere.

    Raises:
        ValueError: If the coordinate cannot be parsed or is outside valid range
    """
    if string is None:
        return None

    # Handle numeric types directly
    if isinstance(string, float | int | Decimal):
        decimal_result = Decimal(str(string))
        if validate:
            return _validate_coordinate(decimal_result, coord_type)
        return decimal_result

    if not isinstance(string, str):
        raise ValueError(f"Expected string, float, or Decimal, got {type(string)}")

    orig_string = string
    string = string.strip()
    if not string:
        return None

    # First, try maritime coordinate patterns (more specific patterns first)
    maritime_patterns = [
        # Pattern 1: degree-dash-minutes with degree symbol: "40°–41.65'N"
        r'^(\d+\.?\d*)°[–\-](\d+\.?\d*)[\'""]?([A-Z])$',
        # Pattern 2: degree-dash-minutes without degree symbol: "54-05.48N"
        r"^(\d+\.?\d*)[–\-](\d+\.?\d*)([A-Z])$",
        # Pattern 3: degree-minutes with degree symbol: "30°34.4'N"
        r'^(\d+\.?\d*)°(\d+\.?\d*)[\'""]?([A-Z])$',
        # Pattern 4: degree-minutes-seconds: "30°34'24.0\"N"
        r'^(\d+\.?\d*)°(\d+\.?\d*)[\'""](\d+\.?\d*)[\'""]([A-Z])$',
    ]

    # Check maritime patterns first
    for pattern in maritime_patterns:
        match = re.match(pattern, string.strip())
        if match:
            groups = match.groups()

            if len(groups) == 3:  # degrees, minutes, hemisphere
                degrees = float(groups[0])
                minutes = float(groups[1])
                hemisphere = groups[2].upper()

                # Validate hemisphere
                if hemisphere not in ("N", "S", "E", "W"):
                    raise ValueError(
                        f"Invalid hemisphere '{hemisphere}', must be N, S, E, or W"
                    )

                # Check for fractional degrees with minutes (invalid)
                if degrees != int(degrees):
                    raise ValueError(
                        "Fractional degrees cannot be combined with minutes"
                    )

                # Validate minutes
                if minutes >= 60:
                    raise ValueError(f"Minutes {minutes} must be less than 60")

                # Convert to decimal degrees
                result = degrees + minutes / 60.0

                # Apply hemisphere sign
                if hemisphere in ("S", "W"):
                    result = -result

                # Convert to Decimal and validate if requested
                decimal_result = Decimal(str(result))
                if validate:
                    return _validate_coordinate(decimal_result, coord_type)
                return decimal_result

            elif len(groups) == 4:  # degrees, minutes, seconds, hemisphere
                degrees = float(groups[0])
                minutes = float(groups[1])
                seconds = float(groups[2])
                hemisphere = groups[3].upper()

                # Validate hemisphere
                if hemisphere not in ("N", "S", "E", "W"):
                    raise ValueError(
                        f"Invalid hemisphere '{hemisphere}', must be N, S, E, or W"
                    )

                # Check for fractional degrees with minutes/seconds (invalid)
                if degrees != int(degrees):
                    raise ValueError(
                        "Fractional degrees cannot be combined with minutes and seconds"
                    )

                # Validate minutes and seconds
                if minutes >= 60:
                    raise ValueError(f"Minutes {minutes} must be less than 60")
                if seconds >= 60:
                    raise ValueError(f"Seconds {seconds} must be less than 60")

                # Convert to decimal degrees
                result = degrees + minutes / 60.0 + seconds / 3600.0

                # Apply hemisphere sign
                if hemisphere in ("S", "W"):
                    result = -result

                # Convert to Decimal and validate if requested
                decimal_result = Decimal(str(result))
                if validate:
                    return _validate_coordinate(decimal_result, coord_type)
                return decimal_result

    # If no maritime pattern matched, try standard parsing
    string = string.strip().lower()

    # replace full cardinal directions:
    string = string.replace("north", "n")
    string = string.replace("south", "s")
    string = string.replace("east", "e")
    string = string.replace("west", "w")

    # replace cyrillic cardinal directions:
    string = string.replace("с", "n")
    string = string.replace("ю", "s")
    string = string.replace("в", "e")
    string = string.replace("з", "w")

    # change W and S to a negative value
    negative = -1 if string.endswith(("w", "s")) else 1
    negative = -1 if string.startswith(("-", "w", "s")) else negative

    try:
        parts = re.findall(r"\d+(?:[.,]\d+)?", string)
        if parts:
            parts = [float(part.replace(",", ".")) for part in parts]

            # Validate coordinate components
            if len(parts) >= 2:  # degrees, minutes
                if parts[1] >= 60:  # minutes must be < 60
                    raise ValueError("Minutes must be less than 60")
            if len(parts) >= 3:  # degrees, minutes, seconds
                if parts[2] >= 60:  # seconds must be < 60
                    raise ValueError("Seconds must be less than 60")
                # Check for decimal in multiple fields - only invalid if degrees
                # AND minutes both have decimals (since degrees-minutes-seconds
                # is allowed to have decimals in all fields)
                if len(parts) == 2:  # degrees, minutes only
                    decimal_parts = [
                        part_str
                        for part_str in re.findall(r"\d+(?:[.,]\d+)?", orig_string)
                        if "." in part_str or "," in part_str
                    ]
                    if len(decimal_parts) > 1:
                        raise ValueError(
                            "Decimal values in multiple fields not allowed "
                            "for degrees-minutes format"
                        )

            result = math.copysign(to_dec_deg(*parts), negative)
            if not math.isfinite(result):
                raise ValueError()

            # Convert to Decimal and validate if requested
            decimal_result = Decimal(str(result))
            if validate:
                return _validate_coordinate(decimal_result, coord_type)
            return decimal_result
        else:
            raise ValueError()
    except ValueError as e:
        # Re-raise validation errors as-is, but wrap parsing errors
        if (
            "outside valid range" in str(e)
            or "must be less than" in str(e)
            or "Decimal values in multiple fields" in str(e)
            or "Invalid hemisphere" in str(e)
            or "Fractional degrees cannot be combined" in str(e)
        ):
            raise e
        raise ValueError(f"{orig_string!r} is not a valid coordinate string")


def _validate_coordinate(
    value: Decimal | None, coord_type: str = "coordinate"
) -> Decimal | None:
    """Validate that a coordinate is within valid ranges.

    Args:
        value: Coordinate value to validate
        coord_type: Type of coordinate ('latitude' or 'longitude' or 'coordinate')

    Returns:
        Validated coordinate or None if invalid

    Raises:
        ValueError: If coordinate is outside valid range
    """
    if value is None:
        return None

    # Convert to float for range checking
    coord_float = float(value)

    if coord_type.lower() == "latitude":
        if not (-90 <= coord_float <= 90):
            raise ValueError(f"Latitude {coord_float} is outside valid range [-90, 90]")
    elif coord_type.lower() == "longitude":
        if not (-180 <= coord_float <= 180):
            raise ValueError(
                f"Longitude {coord_float} is outside valid range [-180, 180]"
            )
    else:
        # General coordinate validation - assume it should be reasonable
        if not (-180 <= coord_float <= 180):
            raise ValueError(
                f"Coordinate {coord_float} is outside reasonable range [-180, 180]"
            )

    return value
