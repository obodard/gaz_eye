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
```

> [!TIP]
> To find valid address strings, visit the official [Régie Essence Québec Map](https://regieessencequebec.ca/).

## 🛠️ Requirements

- Python 3.7+
- `requests`
- `pyyaml`

## 🐳 Docker Deployment

You can run Gaz Saver as a containerized service that automatically updates daily at 4:00 PM EST.

1. **Build and start the container:**
   ```bash
   docker-compose up -d
   ```

2. **Check the output:**
   Since the script runs via cron, you can check the latest output in the container logs:
   ```bash
   docker logs gaz_eye_container
   ```

3. **Updating Configuration:**
   The `stations.yaml` file is bind-mounted, so you can edit it on your host machine without rebuilding the container. The changes will be picked up by the next cron run.

## 📊 Features

- **Real-time Data:** Fetches the latest GeoJSON data directly from the Régie de l'énergie.
- **Smart Sorting:** Automatically sorts stations by price (cheapest first).
- **Price Delta:** Compares all stations to your designated `reference_station`.
- **Savings Calculation:** Calculates the estimated difference for a 50L fill-up.
- **Custom Aliases:** Add labels like "Home" or "Work" for quick identification.
- **Color-coded Output:** High-visibility terminal output with CYAN city labels and BOLD price highlights.
- **Automatic Alignment:** Columns remain aligned even with long city names (e.g., *Sainte-Agathe-des-Monts*).
- **No API Key Required:** Uses public consumer-facing endpoints.
