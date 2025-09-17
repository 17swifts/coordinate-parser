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
"""

import math
import re
from decimal import Decimal


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
