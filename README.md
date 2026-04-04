# ⛽ Gaz Saver — Régie Essence Québec

A Python CLI tool to monitor gas prices at specific stations in Quebec. It fetches real-time data from the official [Régie Essence Québec](https://regieessencequebec.ca/) public data source and displays results in a formatted terminal table, grouped by city.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure your stations:**
   Edit `stations.yaml` to include the addresses of the stations you want to monitor.

3. **Run the script:**
   ```bash
   python3 gaz_saver.py
   ```

## ⚙️ Configuration (`stations.yaml`)

Edit `stations.yaml` to list your 12 stations grouped by city. The tool uses a **partial address match** (case-insensitive) to find stations in the official database.

```yaml
cities:
  - name: "Montréal"
    stations:
      - address: "9531 Boul. Gouin"  # Substring match
      - address: "7575 boul. Décarie"
```

> [!TIP]
> To find valid address strings, visit the official [Régie Essence Québec Map](https://regieessencequebec.ca/).

## 🛠️ Requirements

- Python 3.7+
- `requests`
- `pyyaml`

## 📊 Features

- **Real-time Data:** Fetches the latest GeoJSON data published by the Régie de l'énergie.
- **Grouped Display:** Organizes prices by city for easy comparison.
- **Color-coded Output:** High-visibility terminal output showing prices for Régulier, Super, and Diesel.
- **No API Key Required:** Uses public consumer-facing endpoints.
