# Story 1.1: Flask Project Scaffold

## Status

done

## Story

**As a developer,**
I want a runnable Flask application skeleton with the correct project structure, launch script, and environment configuration,
So that I have a working foundation to build all subsequent backend and frontend features on.

## Acceptance Criteria

**AC1:** Given the repository is cloned and `.env` contains `GOOGLE_MAPS_API_KEY=<any value>`, when I run `./run.sh`, then Flask starts at `http://localhost:5000` with debug/hot-reload enabled, `GET /` returns HTTP 200 with placeholder HTML containing "gaz_eye", and a startup warning is printed to stdout if `GOOGLE_MAPS_API_KEY` is unset in the environment.

**AC2:** Given the project structure after this story, when I inspect the repository, then the following files exist:
- `app.py` (pure factory, zero `@app.route` decorators)
- `api/__init__.py`
- `api/routes.py` (Blueprint registered in `app.py`, skeleton with no functional routes yet)
- `run.sh` (executable, sets `FLASK_APP=app.py` and `FLASK_ENV=development`, sources `.env`)
- `.env.example` (key names with empty values)
- `.gitignore` (includes `.env`, `__pycache__/`, `*.pyc`)
- `requirements.txt` updated to include `flask==3.1.3` and `python-dotenv`

**AC3:** `gaz_saver.py` and `stations.yaml` are preserved entirely unchanged.

## Tasks / Subtasks

- [x] Task 1: Update `requirements.txt` with Flask and python-dotenv
  - [x] Add `flask==3.1.3` and `python-dotenv` to requirements.txt
- [x] Task 2: Create `app.py` as a pure Flask factory
  - [x] Import Blueprint from `api.routes`
  - [x] Create `create_app()` factory function
  - [x] Load `.env` via `python-dotenv`
  - [x] Warn to stdout if `GOOGLE_MAPS_API_KEY` is not set
  - [x] Register Blueprint
  - [x] No `@app.route` decorators
- [x] Task 3: Create `api/__init__.py` and `api/routes.py` with Blueprint skeleton
  - [x] `api/__init__.py` — empty or minimal
  - [x] `api/routes.py` — Flask Blueprint `bp`, no routes yet, placeholder `GET /` returning 200 "gaz_eye" HTML
- [x] Task 4: Create `run.sh` launch script
  - [x] Set `FLASK_APP=app.py`, `FLASK_ENV=development`
  - [x] Source `.env` if it exists
  - [x] Execute `flask run`
  - [x] Make script executable
- [x] Task 5: Create `.env.example` and update `.gitignore`
  - [x] `.env.example` with `GOOGLE_MAPS_API_KEY=`
  - [x] `.gitignore` already included `.env`, `__pycache__/`, `*.pyc` — no change needed
- [x] Task 6: Install dependencies and verify Flask starts

## Dev Notes

**Architecture Requirements:**
- `app.py` must be a pure factory — zero `@app.route` decorators; only Blueprint registration
- `api/routes.py` Blueprint pattern: all routes live here, imported and registered in `app.py`
- `run.sh` is the single dev launch command — sets `FLASK_APP`, `FLASK_ENV`, sources `.env`
- `GOOGLE_MAPS_API_KEY` loaded via `python-dotenv` from `.env` — if missing, warn to stdout (not stderr) but don't fail
- `gaz_saver.py` and `stations.yaml` must remain 100% unchanged

**Project Context Rules:**
- Logging over print: use `logging.Logger` with `StreamHandler(sys.stdout)`, `%(message)s` format
- Exit on fatal errors: `sys.exit(1)` on config errors — but missing API key is a warning, not fatal
- Single-file constraint is relaxed for this epic: we are creating `app.py`, `api/` module
- Python 3.9+, use built-in generics

**Placeholder route in `api/routes.py`:**
```python
@bp.route("/")
def serve_index():
    return "<h1>gaz_eye</h1>", 200
```
This will be replaced in Story 3.1 with Jinja2 template rendering.

## Dev Agent Record

### Implementation Plan
- Created `app.py` as pure factory using `create_app()` pattern; loads `.env` via python-dotenv, warns on missing API key, registers Blueprint from `api/routes.py`
- Created `api/__init__.py` (empty) and `api/routes.py` with Flask Blueprint `bp`; `GET /` returns `<h1>gaz_eye</h1>` as placeholder
- Created `run.sh` with env loading and `FLASK_APP`/`FLASK_ENV` exports; made executable
- Created `.env.example` with empty `GOOGLE_MAPS_API_KEY=` key
- Updated `requirements.txt` with `flask==3.1.3` and `python-dotenv`

### Debug Log
(to be filled during implementation)

### Completion Notes
✅ All ACs satisfied:
- AC1: Flask starts, `GET /` returns 200 with "gaz_eye", warning printed when `GOOGLE_MAPS_API_KEY` unset
- AC2: All required files exist; `app.py` has zero `@app.route` decorators (verified via AST)
- AC3: `gaz_saver.py` and `stations.yaml` unchanged (git diff clean)

## File List

- `requirements.txt` (modified)
- `app.py` (created)
- `api/__init__.py` (created)
- `api/routes.py` (created)
- `run.sh` (created)
- `.env.example` (created)

## Change Log

### Review Findings

- [x] [Review][Patch] `FLASK_ENV=development` is a no-op in Flask 3.x — AC1 requires debug/hot-reload but the dev server starts without it; fix: add `--debug` flag to `flask run` in `run.sh` and/or set `FLASK_DEBUG=1` [run.sh:22]
- [x] [Review][Patch] `source .env` in `run.sh` executes arbitrary shell syntax from `.env` values — python-dotenv in `create_app()` already loads `.env`; remove the `source .env` block from `run.sh` to eliminate the risk and the redundancy [run.sh:8-13]
- [x] [Review][Defer] No `SECRET_KEY` configured in `create_app()` — sessions and CSRF tokens will fail when added; pre-existing design gap, not actionable this story [app.py] — deferred, pre-existing

- 2026-05-01: Story 1.1 implemented — Flask scaffold created with app.py factory, api/ Blueprint, run.sh, .env.example, requirements.txt updated
