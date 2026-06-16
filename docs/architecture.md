# Architecture — checkov

## Architecture Pattern

Single-file functional CLI. No classes, no OOP. All logic resides in `checkov.py` (~270 LOC) with pure functions and a linear execution pipeline.

## Module Structure

```
checkov.py
├── Constants
│   ├── GEOJSON_URL        # Data source endpoint
│   └── CONFIG_FILE        # Path to stations.yaml (relative to script)
│
├── Configuration
│   └── load_config()      # Parse stations.yaml → config dict
│
├── Data Fetching
│   └── fetch_stations()   # HTTP GET → GeoJSON dict (handles gzip fallback)
│
├── Data Processing
│   ├── index_stations_by_address()  # O(N) partial address matching
│   ├── parse_price_value()          # Cent string → dollar float
│   └── format_price()               # Dollar float → formatted display string
│
├── Output
│   └── display_results()  # Builds sorted table with deltas and tank savings
│
└── Entry Point
    └── main()             # Pipeline: load → fetch → display
```

## Function Signatures & Responsibilities

### `load_config(path: Path) -> dict[str, Any]`
- Reads `stations.yaml`, validates `cities` key exists
- Normalizes `settings` from list-of-dicts to flat dict
- Applies defaults: `tank_litres=50`, `gaz_type="Régulier"`
- Exits with `sys.exit(1)` on missing file or invalid config

### `fetch_stations() -> dict[str, Any]`
- Downloads gzipped GeoJSON from Régie Essence endpoint
- Uses browser-like User-Agent header (required by endpoint)
- Double-parse strategy: tries `json.loads()` first, falls back to `gzip.decompress()`
- Exits with `sys.exit(1)` on network or parse errors

### `index_stations_by_address(features, address_queries) -> dict`
- Single-pass O(N) scan over all GeoJSON features
- Partial case-insensitive address matching using `in` operator
- Early exit when all queries are matched
- Returns dict mapping query string → GeoJSON feature

### `parse_price_value(price_entry) -> float`
- Extracts numeric price from cent string (strips `¢` symbol)
- Converts cents to dollars (÷100)
- Returns `float('inf')` for unavailable/invalid prices

### `format_price(price_entry, width=10) -> str`
- Formats price as `X.XXX$` right-aligned to `width`
- Uses colorama `Style.BRIGHT` wrapping
- Shows `n/a` for infinite (unavailable) prices

### `display_results(config, data) -> None`
- Builds sorted price table with columns: Station (50 chars), Price, Delta, Tank savings
- Calculates delta against reference station (if set)
- Reports unmatched stations as warnings
- All output via `logger.info()` with colorama formatting

## Configuration Schema (stations.yaml)

```yaml
cities:                          # Required
  - city: "City Name"            # Required: city label for grouping
    stations:                    # Required: list of stations
      - address: "partial addr"  # Required: substring to match against API
        alias: "Label"           # Optional: display alias
        reference_station: yes   # Optional: exactly one, used for delta calc

settings:                        # Optional
  - tank_litres: 50              # Tank capacity for savings (default: 50)
  - gaz_type: "Régulier"         # Fuel type: "Régulier" | "Super" | "Diesel"
```

## Error Handling Strategy

- **Fatal errors** → `sys.exit(1)`: missing config, invalid config, network failure, parse failure
- **Soft warnings** → logged to stdout: unmatched station addresses
- No exceptions propagated to caller — the script is the top-level entry point

## Logging

- Single logger named `"Checkov"` writing to `sys.stdout`
- Format: `%(message)s` only (no timestamps, no log levels in output)
- Colorama tokens embedded in messages for terminal highlighting
