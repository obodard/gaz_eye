# Development Guide — checkov

## Prerequisites

- Python 3.9+ (uses built-in generics like `dict[str, Any]`)
- pip (Python package manager)

## Setup

```bash
# Clone the repository
git clone <repo-url>
cd <repo-folder>

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Edit `stations.yaml` to define the gas stations you want to monitor:

```yaml
cities:
  - city: "City Name"
    stations:
      - address: "partial address string"
        alias: "Optional Label"
        reference_station: yes  # Optional: one station for delta calculations

settings:
  - tank_litres: 50
  - gaz_type: "Régulier"  # "Régulier" | "Super" | "Diesel"
```

Find valid addresses at [regieessencequebec.ca](https://regieessencequebec.ca/).

## Running

```bash
python3 checkov.py
```

Output is a color-coded terminal table showing:
- Station names grouped by city, sorted by price
- Price delta against the reference station
- Estimated tank savings based on configured capacity

## Dependencies

| Package   | Purpose                    |
|-----------|----------------------------|
| requests  | HTTP client for GeoJSON    |
| pyyaml    | YAML config file parsing   |
| colorama  | Terminal ANSI color output  |

## Testing

No test suite exists yet. When adding tests:
- Use `pytest`
- Place in `tests/` directory
- Mock `requests.get` — never hit the live endpoint
- Key functions to test: `parse_price_value()`, `format_price()`, `index_stations_by_address()`, `load_config()`
