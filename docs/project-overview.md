# Project Overview — chekov

## Executive Summary

**Chekov** is a Python CLI tool that monitors gas prices at specific stations in Quebec. It fetches real-time data from the official [Régie Essence Québec](https://regieessencequebec.ca/) public GeoJSON endpoint and displays results in a formatted, color-coded terminal table grouped by city and sorted by price.

## Repository Type

**Monolith** — Single-file Python CLI application.

## Technology Stack

| Category       | Technology     | Version    | Notes                                        |
|----------------|----------------|------------|----------------------------------------------|
| Language       | Python         | 3.9+       | Uses built-in generics (dict[], list[])      |
| HTTP Client    | requests       | unpinned   | Fetches gzipped GeoJSON                      |
| Config Parser  | pyyaml         | unpinned   | Parses stations.yaml                         |
| Terminal Color | colorama       | unpinned   | ANSI color output with autoreset             |
| Data Source    | Régie Essence  | public API | GeoJSON at stations.geojson.gz               |

## Architecture Pattern

**Single-file functional CLI** — All logic in `chekov.py` with a `main()` entry point guarded by `if __name__ == "__main__"`. No classes, no module/package structure. Functions follow a pipeline: load config → fetch data → index stations → display results.

## Key Files

| File              | Purpose                                                  |
|-------------------|----------------------------------------------------------|
| `chekov.py`    | Main application — all business logic (270 LOC)          |
| `stations.yaml`   | User configuration — cities, stations, settings          |
| `requirements.txt` | Python dependencies (3 packages, no version pins)       |
| `README.md`       | User-facing documentation                                |
| `.gitignore`      | Standard Python gitignore                                |

## Data Flow

```
stations.yaml → load_config() → config dict
                                      │
regieessencequebec.ca/stations.geojson.gz → fetch_stations() → GeoJSON features
                                      │                              │
                                      └──────────┬───────────────────┘
                                                  ▼
                                    index_stations_by_address()
                                                  │
                                                  ▼
                                       display_results()
                                                  │
                                                  ▼
                                        Terminal output (colorama)
```

## External Dependencies

- **Régie Essence Québec** public GeoJSON endpoint — no API key, requires browser-like User-Agent header
- No database, no file output, no network services beyond the single HTTP GET
