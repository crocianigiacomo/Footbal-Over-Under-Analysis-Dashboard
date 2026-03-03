# stats_partite_db

Football Database Processor + Interactive Stats Dashboard

---

## What Is This Project?

This project is a complete football data pipeline — from raw JSON files to an interactive web dashboard accessible from any device.

It has two main components:

- **`scrapplusdb.py`** — reads match data from JSON files and loads everything into a SQLite database
- **`dashboard.py`** — a Streamlit web dashboard that visualizes the data with interactive tables and filters

---

## Project Structure

```
stats_partite_db/
├── calcio.db              # SQLite database (auto-generated)
├── scrapplusdb.py         # ETL pipeline: JSON → database
├── query.py               # SQL query library (reusable functions)
├── dashboard.py           # Streamlit web dashboard
├── requirements.txt       # Python dependencies
├── .streamlit/
│   └── config.toml        # Dark theme configuration
└── round_1.json           # Raw match data (up to round_38.json)
    ...
```

---

## Part 1 — Database Pipeline (scrapplusdb.py)

### What It Does

- Opens football match JSON files (one per round, up to 38)
- Checks that each match was actually played (skips postponed or not started)
- Saves results into a structured SQLite database
- Avoids saving the same match twice
- Automatically calculates second half goals from total minus first half

### Database Architecture

**File:** `calcio.db`  
**Table:** `partite`

| Column              | Description                                |
| ------------------- | ------------------------------------------ |
| `lega`              | League name                                |
| `giornata`          | Matchday number                            |
| `squadra_casa`      | Home team                                  |
| `squadra_trasferta` | Away team                                  |
| `gol_casa`          | Home goals (full match)                    |
| `gol_trasferta`     | Away goals (full match)                    |
| `gol_casa_1t`       | Home goals (first half)                    |
| `gol_trasferta_1t`  | Away goals (first half)                    |
| `gol_casa_2t`       | Home goals (second half — auto-calculated) |
| `gol_trasferta_2t`  | Away goals (second half — auto-calculated) |
| `winner_code`       | Match outcome code                         |

**Indexes created on:** `lega`, `giornata`, `squadra_casa`, `squadra_trasferta`, `winner_code`, `lega + giornata`

### How to Run

Place your JSON files in the same folder, then:

```bash
python scrapplusdb.py
```

---

## Part 2 — Interactive Dashboard (dashboard.py)

### What It Does

A dark-mode web dashboard with three sections:

**Top 20 Over 2.5** — ranks the 20 teams across all leagues with the highest percentage of matches with 3 or more total goals. Includes a color-coded progress bar (green → yellow → grey based on intensity).

**Top 20 Under 2.5** — same logic for matches with fewer than 3 goals. Color-coded in red/orange.

**Goals by League** — select any league from a dropdown and get a full sortable table with:

- Goals scored and conceded at home
- Goals scored and conceded away
- Average per match (home and away)
- Total goals scored and conceded

Every column header in the goals table is **clickable to sort** (ascending/descending), with arrow indicators showing the active sort direction.

### Mobile Support

The dashboard automatically detects screen width on load:

- On **desktop** — Over and Under tables are shown side by side in two columns
- On **mobile** (under 768px) — tables stack vertically, the goals table hides the "average" columns to keep it readable on small screens, font and padding are reduced

### Technologies Used

| Library                   | Purpose                                                   |
| ------------------------- | --------------------------------------------------------- |
| `streamlit`               | Web framework and UI rendering                            |
| `pandas`                  | Data handling and SQL query results                       |
| `sqlite3`                 | Database connection (standard library)                    |
| `streamlit.components.v1` | Iframe rendering for sortable HTML tables with JavaScript |

### Installation

```bash
pip install -r requirements.txt
```

**requirements.txt:**

```
streamlit>=1.35.0
plotly>=5.20.0
pandas>=2.0.0
```

### How to Run

```bash
streamlit run dashboard.py
```

Then open `http://localhost:8501` in your browser.

---

## Deployment — Streamlit Community Cloud

The dashboard can be deployed publicly (accessible from browser and mobile) via [Streamlit Community Cloud](https://share.streamlit.io) at no cost:

1. Push the project to a GitHub repository (private is fine)
2. Make sure `calcio.db` is included in the repository
3. Connect the repo on share.streamlit.io and select `dashboard.py` as the entry point
4. The app will be live at a public URL within minutes

No code changes are required for deployment.

---

## Why This Project Is Powerful

Even though the interface looks simple, the stack demonstrates:

- **ETL pipeline** — Extract from JSON, Transform with business logic, Load into SQLite
- **Object-Oriented Programming** — `CalcioDatabase` and `StatsQuery` classes
- **SQL indexing and query optimization** — CTEs, aggregations, window functions
- **Frontend without a full web framework** — sortable HTML tables with embedded CSS and vanilla JavaScript rendered inside iframes to bypass Streamlit's script sanitization
- **Responsive design** — server-side mobile detection via query params, conditional layout and column visibility
- **Streamlit caching** — `@st.cache_resource` for the DB connection, `@st.cache_data` for query results (5-minute TTL)
- **Scalable architecture** — adding new leagues or stats requires only a new query function, the UI adapts automatically

---

## Final Summary

This project is a complete mini data platform:

1. Reads and cleans raw match data from JSON
2. Stores it in a structured, indexed SQLite database
3. Exposes it through a dark-mode interactive dashboard
4. Works locally and is deployable to the web with zero code changes
5. Adapts its layout automatically for mobile screens
