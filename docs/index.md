# Project Documentation Index — gaz_eye

## Project Overview

- **Type:** Monolith — single-file Python CLI
- **Primary Language:** Python 3.9+
- **Architecture:** Functional pipeline (load → fetch → display)
- **Purpose:** Monitor gas prices at Quebec stations via public GeoJSON data

### Quick Reference

- **Tech Stack:** Python + requests + pyyaml + colorama
- **Entry Point:** `gaz_saver.py` → `main()`
- **Configuration:** `stations.yaml`
- **Data Source:** Régie Essence Québec public GeoJSON (no API key)

## Generated Documentation

- [Project Overview](./project-overview.md)
- [Architecture](./architecture.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [Development Guide](./development-guide.md)

## Existing Documentation

- [README](../README.md) — User-facing quick start and feature list

## BMAD Artifacts

- [Project Context](../_bmad-output/project-context.md) — AI agent implementation rules

## Getting Started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 gaz_saver.py
```
