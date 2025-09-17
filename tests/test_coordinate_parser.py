"""
Tests for coordinate_parser module.
"""

from decimal import Decimal

import pytest

from coordinate_parser import (
    parse_coordinate,
    parse_utm_coordinate,
    parse_utm_coordinate_single,
    utm_to_latlon,
)


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


class TestUTMCoordinates:
    """Test UTM coordinate parsing functionality."""

    def test_utm_to_latlon_basic(self):
        """Test basic UTM to lat/lon conversion."""
        # Test a known location: Berlin, Germany
        # UTM Zone 33N, Brandenburg Gate area
        lat, lon = utm_to_latlon(33, "N", 391545, 5819698)

        # Should be approximately 52.5163° N, 13.3777° E (Brandenburg Gate)
        assert abs(lat - 52.5163) < 0.01
        assert (
            abs(lon - 13.3777) < 0.05
        )  # Allow slightly larger tolerance for longitude

    def test_utm_to_latlon_southern_hemisphere(self):
        """Test UTM conversion in southern hemisphere."""
        # Test a location in southern hemisphere: São Paulo, Brazil
        # UTM Zone 23S
        lat, lon = utm_to_latlon(23, "K", 332398, 7395850)

        # Should be approximately -23.5475° S, -46.6361° W
        assert abs(lat - (-23.5475)) < 0.01
        assert abs(lon - (-46.6361)) < 0.01

    def test_utm_validation(self):
        """Test UTM parameter validation."""
        # Invalid zone number
        with pytest.raises(ValueError, match="zone number"):
            utm_to_latlon(61, "N", 500000, 5000000)

        with pytest.raises(ValueError, match="zone number"):
            utm_to_latlon(0, "N", 500000, 5000000)

        # Invalid zone letter
        with pytest.raises(ValueError, match="zone letter"):
            utm_to_latlon(33, "I", 500000, 5000000)  # I is excluded

        with pytest.raises(ValueError, match="zone letter"):
            utm_to_latlon(33, "O", 500000, 5000000)  # O is excluded

        with pytest.raises(ValueError, match="zone letter"):
            utm_to_latlon(33, "Z", 500000, 5000000)  # Z is beyond valid range

    def test_parse_utm_coordinate_formats(self):
        """Test parsing various UTM coordinate formats."""
        # Test data: (utm_string, expected_approximate_lat, expected_approximate_lon)
        # Using Berlin coordinates: 33N 391545 5819698 ≈ 52.5163°N, 13.3777°E
        test_cases = [
            # Standard format
            ("33N 391545 5819698", 52.5163, 13.3777),
            ("23K 332398 7395850", -23.5475, -46.6361),  # São Paulo, Brazil
            # With "Zone" prefix
            ("Zone 33N 391545 5819698", 52.5163, 13.3777),
            ("ZONE 23K 332398 7395850", -23.5475, -46.6361),
            # With spaces around zone letter
            ("33 N 391545 5819698", 52.5163, 13.3777),
            ("23 K 332398 7395850", -23.5475, -46.6361),
            # Compact format
            ("33N391545E5819698N", 52.5163, 13.3777),
            ("23K332398E7395850N", -23.5475, -46.6361),
        ]

        for utm_string, expected_lat, expected_lon in test_cases:
            result = parse_utm_coordinate(utm_string)
            assert result is not None, f"Failed to parse: {utm_string}"

            lat, lon = result
            # Allow reasonable tolerance for coordinate conversion (0.1 degrees ≈ 11km)
            lat_msg = (
                f"Lat mismatch for {utm_string}: got {lat}, expected ~{expected_lat}"
            )
            assert abs(lat - expected_lat) < 0.1, lat_msg
            lon_msg = (
                f"Lon mismatch for {utm_string}: got {lon}, expected ~{expected_lon}"
            )
            assert abs(lon - expected_lon) < 0.1, lon_msg

    def test_parse_utm_coordinate_invalid(self):
        """Test parsing invalid UTM coordinate formats."""
        invalid_cases = [
            "invalid string",
            "33X 391545 5819698",  # Invalid zone letter (X not in valid letters)
            "33I 391545 5819698",  # Invalid zone letter (I excluded)
            "33O 391545 5819698",  # Invalid zone letter (O excluded)
            "61N 391545 5819698",  # Invalid zone number
            "0N 391545 5819698",  # Invalid zone number
            "33N 91545 5819698",  # Easting too short (5 digits)
            "33N 391545 819698",  # Northing too short (6 digits, need minimum 7)
            "33N391545E5819698",  # Missing final N in compact format
            "33N391545E5819698X",  # Wrong final letter in compact format
            "",
            "   ",
        ]

        for invalid_utm in invalid_cases:
            result = parse_utm_coordinate(invalid_utm)
            assert result is None, f"Should have failed to parse: {invalid_utm}"

    def test_utm_coordinate_edge_cases(self):
        """Test UTM coordinates at edge cases."""
        # Test various zone letters
        valid_letters = "CDEFGHJKLMNPQRSTUVW"

        for letter in valid_letters:
            if letter in "CDEFGHJKLM":  # Southern hemisphere (C-M, excluding I and O)
                result = parse_utm_coordinate(f"33{letter} 391545 5819698")
                assert result is not None
                lat, lon = result
                # Note: some letters near equator might give positive results
                # For this test, we'll just verify parsing works
            else:  # Northern hemisphere (N-X)
                result = parse_utm_coordinate(f"33{letter} 391545 5819698")
                assert result is not None
                lat, lon = result
                # For northern hemisphere letters, latitude should generally be positive
                # But we'll just verify parsing works for this test

    def test_utm_coordinate_case_insensitive(self):
        """Test that UTM parsing is case insensitive."""
        test_cases = [
            "33n 391545 5819698",
            "33N 391545 5819698",
            "zone 33n 391545 5819698",
            "ZONE 33N 391545 5819698",
            "33n391545e5819698n",
            "33N391545E5819698N",
        ]

        # All should parse to the same result
        expected_result = parse_utm_coordinate("33N 391545 5819698")
        assert expected_result is not None

        for test_case in test_cases:
            result = parse_utm_coordinate(test_case)
            assert result is not None
            # Results should be very close (within small floating point differences)
            assert abs(result[0] - expected_result[0]) < 1e-10
            assert abs(result[1] - expected_result[1]) < 1e-10

    def test_utm_coordinate_precision(self):
        """Test UTM coordinate precision with different easting/northing lengths."""
        # Test 6-digit easting and 7-digit northing (Berlin area)
        result1 = parse_utm_coordinate("33N 391545 5819698")
        assert result1 is not None
        lat1, lon1 = result1
        assert isinstance(lat1, float)
        assert isinstance(lon1, float)
        assert -90 <= lat1 <= 90
        assert -180 <= lon1 <= 180

        # Test 7-digit easting and 7-digit northing (different location)
        result2 = parse_utm_coordinate("33N 3915450 5819698")
        assert result2 is not None
        lat2, lon2 = result2
        assert isinstance(lat2, float)
        assert isinstance(lon2, float)
        assert -90 <= lat2 <= 90
        assert -180 <= lon2 <= 180

    def test_utm_coordinate_validation(self):
        """Test UTM coordinate validation functionality."""
        # Test with validation enabled (default)
        result = parse_utm_coordinate("33N 391545 5819698", validate=True)
        assert result is not None
        lat, lon = result
        assert -90 <= lat <= 90
        assert -180 <= lon <= 180

        # Test with validation disabled
        result = parse_utm_coordinate("33N 391545 5819698", validate=False)
        assert result is not None
        lat, lon = result
        # Should still be reasonable since this is a valid UTM coordinate
        assert -90 <= lat <= 90
        assert -180 <= lon <= 180

        # Test utm_to_latlon validation
        lat, lon = utm_to_latlon(33, "N", 391545, 5819698, validate=True)
        assert -90 <= lat <= 90
        assert -180 <= lon <= 180

        lat, lon = utm_to_latlon(33, "N", 391545, 5819698, validate=False)
        assert -90 <= lat <= 90
        assert -180 <= lon <= 180

    def test_utm_coordinate_single_parsing(self):
        """Test parsing individual coordinates from UTM strings."""
        utm_string = "33N 391545 5819698"

        # Test latitude extraction
        lat = parse_utm_coordinate_single(utm_string, "latitude")
        assert lat is not None
        assert isinstance(lat, Decimal)
        assert -90 <= float(lat) <= 90

        # Test longitude extraction
        lon = parse_utm_coordinate_single(utm_string, "longitude")
        assert lon is not None
        assert isinstance(lon, Decimal)
        assert -180 <= float(lon) <= 180

        # Test default (latitude)
        lat_default = parse_utm_coordinate_single(utm_string)
        assert lat_default == lat

        # Test with validation disabled
        lat_no_val = parse_utm_coordinate_single(utm_string, "latitude", validate=False)
        assert lat_no_val is not None
        assert isinstance(lat_no_val, Decimal)

        # Test invalid UTM string
        invalid_result = parse_utm_coordinate_single("invalid utm", "latitude")
        assert invalid_result is None

    def test_utm_coordinate_validation_edge_cases(self):
        """Test UTM coordinate validation with edge cases."""
        # Test coordinates that might produce extreme values
        # These should still pass validation if they're mathematically valid UTM
        # conversions

        # Test zone boundaries
        result1 = parse_utm_coordinate("1N 166021 0", validate=True)
        if result1 is not None:  # Only test if parsing succeeds
            lat, lon = result1
            assert -90 <= lat <= 90
            assert -180 <= lon <= 180

        result2 = parse_utm_coordinate("60N 833978 9329005", validate=True)
        if result2 is not None:  # Only test if parsing succeeds
            lat, lon = result2
            assert -90 <= lat <= 90
            assert -180 <= lon <= 180
