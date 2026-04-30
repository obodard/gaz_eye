---
project_name: 'gaz_eye'
user_name: 'Olivier'
date: '2026-04-30'
sections_completed: ['technology_stack', 'language_rules', 'testing_rules', 'code_quality', 'critical_rules']
status: 'complete'
rule_count: 27
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Python** 3.9+ required (code uses `dict[str, Any]` and `list[dict]` built-in generics — NOT compatible with 3.7/3.8)
- **requests** — HTTP client, no version pin
- **pyyaml** — YAML config parser, no version pin
- **colorama** — Terminal ANSI color output, no version pin
- **Data source:** Public GeoJSON endpoint at `regieessencequebec.ca/stations.geojson.gz` (gzip-compressed)
- No pinned dependency versions in `requirements.txt`

## Critical Implementation Rules

### Language-Specific Rules

- **Type hints:** Use built-in generics (`dict[str, Any]`, `list[dict]`, `Optional[str]`) — do NOT import from `typing` for container types (only import `Any`, `Optional` from typing)
- **Logging over print:** Use `logging.Logger` with `StreamHandler(sys.stdout)` — never use `print()` directly. The logger uses a simple `%(message)s` format (no timestamps/levels in output)
- **Exit on fatal errors:** Call `sys.exit(1)` on config errors and network failures — do not raise exceptions to the caller
- **Colorama integration in log messages:** Embed `Fore.*` and `Style.*` tokens directly inside f-strings passed to `logger.info()` — colorama is initialized with `autoreset=True`
- **Path resolution:** Use `Path(__file__).parent` for locating config files relative to the script — never use hardcoded absolute paths
- **String matching:** Partial address matching is case-insensitive via `.lower()` — use `in` operator, not regex
- **Sentinel values:** Use `float('inf')` as sentinel for unavailable/invalid prices — check against it explicitly
- **Single-file architecture:** All logic lives in `gaz_saver.py` — no module/package structure currently

### Testing Rules

- **No test suite exists yet** — when tests are added, follow these conventions:
  - Use `pytest` as the test runner
  - Place tests in a `tests/` directory at project root
  - Name test files `test_<module>.py`
  - Mock `requests.get` for network calls — never hit the live GeoJSON endpoint in tests
  - Mock `Path.exists` and file reads for config loading tests
  - Test `parse_price_value` and `format_price` as pure functions with edge cases (missing price, `¢` symbol, `n/a`)
  - Test `index_stations_by_address` with partial match scenarios

### Code Quality & Style Rules

- **Naming:** `snake_case` for functions and variables, `UPPER_CASE` for module-level constants (`GEOJSON_URL`, `CONFIG_FILE`)
- **String formatting:** Use f-strings exclusively — no `.format()` or `%` interpolation
- **Docstrings:** Every function has a one-line docstring (imperative mood, e.g., "Load station configuration from YAML file.")
- **Imports:** Group in standard order: stdlib → third-party → local. Alphabetical within groups
- **No classes:** Functional style throughout — standalone functions only, no OOP
- **Config file:** `stations.yaml` uses a specific schema: `cities[]` → `city` + `stations[]` → `address` + optional `alias` + optional `reference_station`; `settings[]` is a list of single-key dicts (not a flat dict)
- **Output formatting:** Fixed-width columns with right-aligned prices, left-aligned station names (50 chars), separator lines using `─` (unicode box-drawing character)
- **Encoding:** Always use `encoding="utf-8"` when opening files — station names contain French accents (é, è, ê, etc.)

### Critical Don't-Miss Rules

- **GeoJSON response handling:** The endpoint may return pre-decompressed JSON or raw gzip — always try `json.loads()` first, then fall back to `gzip.decompress()`. Never assume one format
- **Price format:** Prices come from the API as cent strings with `¢` suffix (e.g., `"154.9¢"`) — strip the symbol and divide by 100 to get dollars. Handle `None` and `IsAvailable: false` gracefully
- **Reference station:** Exactly one station in `stations.yaml` should have `reference_station: yes` — all delta/savings calculations are relative to this station. If none is set, deltas are simply omitted (no error)
- **Partial address match is authoritative:** The `address` field in config is a substring matched against the API's `Address` property. One address must match at most one station. Unmatched addresses are reported as warnings, not errors
- **Settings list quirk:** The `settings` key in `stations.yaml` is a list of single-key dicts (`- tank_litres: 50`), NOT a flat dict. The code normalizes this via iteration — preserve this pattern when reading config
- **User-Agent header required:** The GeoJSON endpoint requires a browser-like `User-Agent` header — requests without it may be blocked
- **No API key:** The data source is fully public — never add authentication headers or API key parameters
- **French content:** Station data contains French characters (accented names, addresses) — never strip or normalize unicode characters

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review periodically for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-04-30
