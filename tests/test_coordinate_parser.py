"""
Tests for coordinate_parser module.
"""

from decimal import Decimal

import pytest

from coordinate_parser import parse_coordinate


class TestCoordinateParser:
    """Test coordinate parsing functionality."""

    # Test values: (input_string, expected_decimal_degrees)
    test_values = [
        # decimal degrees
        ("23.43", 23.43),
        ("-45.21", -45.21),
        ("23.43 N", 23.43),
        ("45.21 W", -45.21),
        ("23.43 E", 23.43),
        ("45.21 S", -45.21),
        ("23.43 n", 23.43),
        ("45.21 w", -45.21),
        ("23.43 e", 23.43),
        ("45.21 s", -45.21),
        # degrees, minutes
        ("23° 25.800'", 23.43),
        ("-45° 12.600'", -45.21),
        ("23° 25.800", 23.43),
        ("-45° 12.600", -45.21),
        ("23° 25.800", 23.43),
        ("-45° 12.600'", -45.21),
        ("23°25.800′", 23.43),
        ("-45°12.600′", -45.21),
        ("23d25.800'", 23.43),
        ("-45deg12.600'", -45.21),
        ("23Deg25.800'", 23.43),
        ("-45D12.600'", -45.21),
        # degrees, minutes, just space
        ("23 25.0", 23.416666666667),
        ("-45 12.0", -45.2),
        ("23 25", 23.416666666667),
        ("-45 12", -45.2),
        ("23 25 N", 23.416666666667),
        ("45 12W", -45.2),
        # degrees, minutes, seconds
        ("23° 25' 48.0\" N", 23.43),
        ("45° 12' 36.0\" S", -45.21),
        ("23 25 48.0 N", 23.43),
        ("45 12 36.0 S", -45.21),
        ("23 25 48.0", 23.43),
        ("-45 12 36.0", -45.21),
        # leading hemisphere
        ("N 23° 25' 48.0\"", 23.43),
        ("S 45° 12' 36.0\"", -45.21),
        ("N 23 25 48.0", 23.43),
        ("S 45 12 36.0", -45.21),
        # leading zero
        ("088° 53' 23\" W", -88.889722222222),
        ("-088° 53' 23\"", -88.889722222222),
        # more verbose
        ("153° 55.85′ West", -153.930833333333),
        ("153° 55.85′ East", 153.930833333333),
        ('15° 55′ 20" north', 15.922222222222),
        ("15d 55m 20s south", -15.922222222222),
        # space on both ends:
        (" 088° 53' 23\"   ", 88.889722222222),
        ("   -79.123456  ", -79.123456),
        # space between the minus sign and number:
        ("- 088° 53' 23\" ", -88.889722222222),
        ("- 79.123456", -79.123456),
        ("   - 79.123456", -79.123456),
        # no space
        ("23°25'48.0\"N", 23.43),
        ("45°12'36.0\"S", -45.21),
        ("23 25 48N", 23.43),
        ("45 12 36S", -45.21),
        ("N23 25 48.0", 23.43),
        ("S45 12 36.0", -45.21),
        # minus sign as a separator:
        (" 45-32-12N ", 45.536666666666667),
        (" 45d-32'-12\" west ", -45.536666666666667),
        (" 45d - 32'-12\" South ", -45.536666666666667),
        (" -45d-32'-12\" ", -45.536666666666667),
        ("- 45-32-12", -45.536666666666667),
        # cyrillic number locale
        ("23,43", 23.43),
        ("-45,21", -45.21),
        ("23° 25,800'", 23.43),
        ("-45° 12,600'", -45.21),
        ("23° 25' 48,0\" ", 23.43),
        ("45° 12' 36,0\" ", 45.21),
        # cyrillic hemisphere
        ("23.43 С", 23.43),
        ("45.21 З", -45.21),
        ("23.43 В", 23.43),
        ("45.21 Ю", -45.21),
        ("23.43 с", 23.43),
        ("45.21 з", -45.21),
        ("23.43 в", 23.43),
        ("45.21 ю", -45.21),
        # commas as separators
        ("- 45, 32, 12", -45.536666666666667),
        ("- 45.0, 32.0, 12.0", -45.536666666666667),
        ("45.5, ", 45.5),
        # maritime coordinate formats
        # Pattern 1: degree-dash-minutes with degree symbol
        ("40°–41.65'N", 40.694166666667),
        ("139°-02.54'E", 139.042333333333),
        ('40°–41.65"N', 40.694166666667),  # with double quote
        ('139°-02.54"E', 139.042333333333),  # with double quote
        ("40°–41.65N", 40.694166666667),  # without quote
        ("139°-02.54E", 139.042333333333),  # without quote
        # Pattern 2: degree-dash-minutes without degree symbol
        ("54-05.48N", 54.091333333333),
        ("162-29.03W", -162.483833333333),
        ("54–05.48N", 54.091333333333),  # with en-dash
        ("162–29.03W", -162.483833333333),  # with en-dash
        # Pattern 3: degree-minutes with degree symbol
        ("30°34.4'N", 30.573333333333),
        ("120°45.5'E", 120.758333333333),
        ("45°12.6'S", -45.21),
        ("90°30'W", -90.5),
        ('30°34.4"N', 30.573333333333),  # with double quote
        ("30°34.4N", 30.573333333333),  # without quote
        # Pattern 4: degree-minutes-seconds
        ("30°34'24.0\"N", 30.573333333333),
        ("45°12'36.0\"S", -45.21),
        ("120°30'15.5\"E", 120.504305555556),
        ("75°45'30.25\"W", -75.758402777778),
        ("30°34'24.0'N", 30.573333333333),  # with single quote for seconds
        # maritime edge cases
        ("0°0'0\"N", 0.0),
        ("180°0'0\"E", 180.0),
        ("90°0'0\"S", -90.0),
        ("179°59'59.9\"W", -179.999972222222),
        ("45°30'N", 45.5),
        ("120°45'E", 120.75),
        ("30°15'30\"S", -30.258333333333),
        ("123-45.67E", 123.761166666667),
        ("89-59.99N", 89.999833333333),
        # Additional valid cases that were previously considered invalid
        ("23.43.2", 23.463333333333335),  # 23 degrees, 43.2 minutes
        ("23.4 14.2", 23.636666666666667),  # 23.4 degrees, 14.2 minutes
        (
            "23.2d 14' 12.22\" ",
            23.43672777777778,
        ),  # 23.2 degrees, 14 minutes, 12.22 seconds
    ]

    @pytest.mark.parametrize("string, value", test_values)
    def test_parse_coordinate(self, string, value):
        """Test coordinate parsing with various formats."""
        tol = 12
        result = parse_coordinate(string)
        assert result is not None
        assert round(float(result), tol) == round(value, tol)

    def test_parse_none(self):
        """Test parsing None returns None."""
        assert parse_coordinate(None) is None

    def test_parse_empty_string(self):
        """Test parsing empty string returns None."""
        assert parse_coordinate("") is None
        assert parse_coordinate("   ") is None

    def test_parse_numeric_types(self):
        """Test parsing numeric types."""
        assert parse_coordinate(23.43) == Decimal("23.43")
        assert parse_coordinate(45) == Decimal("45")
        assert parse_coordinate(Decimal("12.34")) == Decimal("12.34")

    def test_coordinate_validation(self):
        """Test coordinate validation with coord_type parameter."""
        # Valid latitude
        assert parse_coordinate("45.5", coord_type="latitude") == Decimal("45.5")

        # Valid longitude
        assert parse_coordinate("120.5", coord_type="longitude") == Decimal("120.5")

        # Invalid latitude (too large)
        with pytest.raises(ValueError, match="outside valid range"):
            parse_coordinate("95.0", coord_type="latitude")

        # Invalid longitude (too large)
        with pytest.raises(ValueError, match="outside valid range"):
            parse_coordinate("185.0", coord_type="longitude")

        # Test with validation disabled
        assert parse_coordinate(
            "95.0", coord_type="latitude", validate=False
        ) == Decimal("95.0")

    # Invalid values that should raise ValueError
    invalid_values = [
        "some_crap",
        "92 92",  # too large a minute value
        "3° 25' 61.0\" N",  # too large a second value
        # maritime invalid formats that should fail
        "40°41.65'X",  # invalid hemisphere
        "40.5°41.65'N",  # fractional degrees with minutes
    ]

    @pytest.mark.parametrize("string", invalid_values)
    def test_parse_invalid(self, string):
        """Test that invalid coordinate strings raise ValueError."""
        with pytest.raises(ValueError):
            parse_coordinate(string)

    def test_parse_invalid_type(self):
        """Test that invalid types raise ValueError."""
        with pytest.raises(ValueError):
            parse_coordinate([1, 2, 3])  # type: ignore
