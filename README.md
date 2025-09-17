# Coordinate Parser

[![CI](https://github.com/17swifts/coordinate-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/17swifts/coordinate-parser/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/coordinate-parser.svg)](https://badge.fury.io/py/coordinate-parser)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A robust Python library for parsing geographic coordinates in various formats. This library can handle decimal degrees, degrees/minutes/seconds, and maritime coordinate formats with high precision.

## Features

- **Multiple format support**: Decimal degrees, degrees/minutes/seconds, maritime formats
- **Flexible input**: Accepts strings, floats, integers, and Decimal types
- **Validation**: Optional coordinate validation with customizable ranges
- **High precision**: Uses Python's Decimal type for accurate calculations
- **Maritime formats**: Special support for nautical coordinate formats
- **Internationalization**: Supports Cyrillic cardinal directions
- **Error handling**: Comprehensive error messages for invalid inputs

## Installation

```bash
pip install coordinate-parser
```

## Quick Start

```python
from coordinate_parser import parse_coordinate

# Basic usage
lat = parse_coordinate("40°41.65'N")
lon = parse_coordinate("74°02.54'W")
print(f"Latitude: {lat}, Longitude: {lon}")

# Decimal degrees
coord = parse_coordinate("23.43")
print(f"Coordinate: {coord}")

# With validation
lat = parse_coordinate("45.5", coord_type="latitude")
lon = parse_coordinate("120.5", coord_type="longitude")
```

## Supported Formats

### Decimal Degrees

```python
parse_coordinate("23.43")        # 23.43
parse_coordinate("-45.21")       # -45.21
parse_coordinate("23.43 N")      # 23.43
parse_coordinate("45.21 W")      # -45.21
```

### Degrees and Minutes

```python
parse_coordinate("23° 25.800'")     # 23.43
parse_coordinate("23 25.8 N")       # 23.43
parse_coordinate("45°12.6'S")       # -45.21
```

### Degrees, Minutes, and Seconds

```python
parse_coordinate("23° 25' 48.0\" N")  # 23.43
parse_coordinate("45° 12' 36.0\" S")  # -45.21
parse_coordinate("23d 25m 48s")       # 23.43
```

### Maritime Formats

```python
# Pattern 1: degree-dash-minutes with degree symbol
parse_coordinate("40°–41.65'N")    # 40.694166666667
parse_coordinate("139°-02.54'E")   # 139.042333333333

# Pattern 2: degree-dash-minutes without degree symbol
parse_coordinate("54-05.48N")      # 54.091333333333
parse_coordinate("162-29.03W")     # -162.483833333333

# Pattern 3: degree-minutes with degree symbol
parse_coordinate("30°34.4'N")      # 30.573333333333
parse_coordinate("120°45.5'E")     # 120.758333333333

# Pattern 4: degree-minutes-seconds
parse_coordinate("30°34'24.0\"N")  # 30.573333333333
```

### International Support

```python
# Cyrillic cardinal directions
parse_coordinate("23.43 С")  # North (С = N)
parse_coordinate("45.21 З")  # West (З = W)
parse_coordinate("23.43 В")  # East (В = E)
parse_coordinate("45.21 Ю")  # South (Ю = S)

# Comma as decimal separator
parse_coordinate("23,43")         # 23.43
parse_coordinate("23° 25,8'")     # 23.43
```

## API Reference

### `parse_coordinate(string, coord_type="coordinate", validate=True)`

Parse a coordinate string and return a Decimal value in decimal degrees.

**Parameters:**

- `string` (str | float | Decimal | None): The coordinate to parse
- `coord_type` (str): Type of coordinate for validation ("latitude", "longitude", or "coordinate")
- `validate` (bool): Whether to validate the coordinate is within valid ranges

**Returns:**

- `Decimal | None`: The parsed coordinate in decimal degrees, or None if input is None/empty

**Raises:**

- `ValueError`: If the coordinate cannot be parsed or is outside valid range

### `to_dec_deg(*args)`

Convert degrees, minutes, seconds to decimal degrees.

**Parameters:**

- `*args`: Variable arguments representing degrees, minutes (optional), seconds (optional)

**Returns:**

- `float`: Decimal degrees

## Validation

The library supports optional validation for coordinates:

```python
# Latitude validation (-90 to 90)
parse_coordinate("45.5", coord_type="latitude")     # Valid
parse_coordinate("95.0", coord_type="latitude")     # Raises ValueError

# Longitude validation (-180 to 180)
parse_coordinate("120.5", coord_type="longitude")   # Valid
parse_coordinate("185.0", coord_type="longitude")   # Raises ValueError

# Disable validation
parse_coordinate("95.0", coord_type="latitude", validate=False)  # Returns 95.0
```

## Error Handling

The library provides comprehensive error handling:

```python
try:
    coord = parse_coordinate("invalid_coordinate")
except ValueError as e:
    print(f"Parse error: {e}")

# Common error cases:
# - Invalid format: "'invalid' is not a valid coordinate string"
# - Out of range: "Latitude 95.0 is outside valid range [-90, 90]"
# - Invalid minutes: "Minutes 65 must be less than 60"
# - Invalid seconds: "Seconds 75 must be less than 60"
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/shipster-ai/coordinate-parser.git
cd coordinate-parser
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Running Tests with Coverage

```bash
pytest --cov=coordinate_parser --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

Originally developed as part of the Shipster project for parsing maritime coordinates.
