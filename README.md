# ⛽ Gaz Saver — Régie Essence Québec

A Python CLI tool to monitor gas prices at specific stations in Quebec. It fetches real-time data from the official [Régie Essence Québec](https://regieessencequebec.ca/) public data source and displays results in a formatted terminal table, grouped by city and sorted by price.

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

The tool uses a **partial address match** (case-insensitive) to find stations in the official database. You can also define an **alias** for each station to make them easier to identify.

```yaml
cities:
  - city: "Montréal"
    stations:
      - address: "9403 boul. des Sciences" 
        alias: "Boulot"
      - address: "4920 rue Beaubien est"
        alias: "Maison"

  - city: "Saint-André-Avellin"
    stations:
      - address: "615 rte 321 nord"
        reference_station: yes  # Used for Delta calculations

settings:
  - tank_litres: 50             # Tank capacity for savings calculation
  - gaz_type: "Régulier"        # "Régulier" | "Super" | "Diesel"
```

> [!TIP]
> To find valid address strings, visit the official [Régie Essence Québec Map](https://regieessencequebec.ca/).

## 🛠️ Requirements

- Python 3.7+
- `requests`
- `pyyaml`

##  Features

- **Real-time Data:** Fetches the latest GeoJSON data directly from the Régie de l'énergie.
- **Smart Sorting:** Automatically sorts stations by price (cheapest first).
- **Price Delta:** Compares all stations to your designated `reference_station`.
- **Customizable Savings:** Calculates the estimated difference for a fuel tank of any size (default: 50L).
- **Multiple Fuel Types:** Supports tracking Régulier, Super, or Diesel prices.
- **Custom Aliases:** Add labels like "Home" or "Work" for quick identification.
- **Color-coded Output:** High-visibility terminal output with CYAN city labels and BOLD price highlights.
- **Automatic Alignment:** Columns remain aligned even with long city names (e.g., *Sainte-Agathe-des-Monts*).
- **No API Key Required:** Uses public consumer-facing endpoints.
