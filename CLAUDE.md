# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate venv (Windows)
.venv\Scripts\activate

# Run locally
streamlit run app.py

# Generate bcrypt hash for a new user password
python hash_password.py

# Install dependencies
pip install -r requirements.txt
```

There are no tests or linting configured. The app auto-deploys to Streamlit Cloud on every push to `main`.

## Secrets (local dev)

Copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml` and fill in:
- `[auth.credentials.usernames.<user>]` — bcrypt hash from `hash_password.py`
- `[auth.cookie]` — random key string
- `[connections.gsheets]` — service account JSON fields + `spreadsheet` URL

`secrets.toml` is gitignored and must never be committed.

## Architecture

Two files: `app.py` (UI) and `data.py` (data layer). No other application code.

### data.py — Data Layer

- **`_read_tab_cached(worksheet)`** — `@st.cache_data(ttl="5m")` cached function that reads one Google Sheets tab via `GSheetsConnection`. Returns `(DataFrame, error_str|None)`. **`st.warning()` must never be called inside a cached function** — errors surface through the wrapper `read_tab()` instead.
- **`read_tab(worksheet, key_col)`** — public wrapper that calls the cached layer and shows warnings outside the cache.
- **`_akun_map()`** — reads `11_DAFTAR_AKUN` → `{Nama Akun: Tipe Akun}` dict used to classify transactions.
- **`_compute_keuangan(df)`** — enriches a `3_KEUANGAN` DataFrame with `_pendapatan` and `_beban` columns by joining against `_akun_map()`. Revenue = Nominal where `Akun Kredit` has Tipe `"Pendapatan"`; Expense = Nominal where `Akun Debit` has Tipe `"Beban"` or `"Beban Non-Operasional"`. Falls back to `Dampak Laba` column if `11_DAFTAR_AKUN` is unavailable.
- **`filter_date(df, date_col, d_from, d_to)`** — date range filter; `dayfirst=True` for Indonesian date format.
- **`keuangan_trend(df)`** — aggregates `_pendapatan`/`_beban`/Laba/RevPAR per calendar month. `Total Kamar` comes from `1_PARAMETER`, not hardcoded.
- **`kpi_executive(keu_df, penghuni_df)`** — computes all KPI floats from raw DataFrames. `penghuni_df` is always unfiltered by date (current state).
- Utility formatters: `to_num(x)` handles `"Rp 1.800.000"` / `0.95` / `""` → `float`; `rupiah()`, `persen()` for display.

### app.py — UI Layer

- Single-file Streamlit app; all 5 pages rendered via `if menu == "..."` blocks (no multi-page routing).
- **`ACCENT`** dict maps page name → hex color used consistently for charts and accents on that page.
- **UI helpers** (defined once, used across all pages):
  - `kpi(col, label, value, ...)` — renders an HTML KPI card with optional delta badge and SVG sparkline.
  - `_delta(current, prev, good_if_up, fmt)` — formats the `▲▼ vs sblm` comparison badge. `fmt` options: `"pct"` (% change), `"pp"` (percentage points), `"count"` (raw delta).
  - `_svg_spark(vals, color)` — pure SVG sparkline using Catmull-Rom Bézier approximation; no external lib.
  - `chart_header(title, subtitle)` — renders the white rounded header above every Plotly chart.
  - `_layout(height, margin, ysfx)` — returns a Plotly layout dict with consistent styling.
  - `donut(labels, values, colors, center)` — `go.Pie` with hole.
  - `bar_chart(x, y, colors, horizontal, ...)` — `go.Bar` with auto-formatted text labels.
- **Sidebar** controls period filter (`d_from`/`d_to`) and page `menu` selection. `_prev_period(d_from, d_to)` computes the equal-length prior period for delta comparisons. Both `pf`/`pt` (prev from/to) are computed once and passed into every page.
- **Period comparison pattern** used on every page: load raw data once → `filter_date` for current period → `filter_date` for prev period → compute KPIs for both → call `_delta()`.
- **Cache invalidation**: sidebar "Refresh data" button calls `st.cache_data.clear()` + `st.rerun()`.
- **Auth**: `streamlit_authenticator` v0.4.2. Credentials (bcrypt hashes) live in `st.secrets["auth"]`. Auth runs at module top-level before any page render; `st.stop()` gates the rest of the app.

### Google Sheets tabs

| Tab | Purpose | Key col |
|-----|---------|---------|
| `1_PARAMETER` | Config (Total Kamar, etc.) | `Parameter` |
| `2_PENGHUNI` | Tenant records | `ID` |
| `3_KEUANGAN` | Double-entry transactions | `Tanggal` |
| `11_DAFTAR_AKUN` | Chart of accounts | — |
| `6_LEADS` / `7_SURVEY` / `8_BOOKING` | Sales pipeline | — |
| `4_KONTEN` / `5_PROMOSI` | Marketing | — |
| `9_PREVENTIVE MAINTENANCE` / `10_CORRECTIVE MAINTENANCE` | Ops | — |

KPIs are computed entirely from raw tab data — there is no pre-summarized tab being read.
