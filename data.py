"""
data.py — Lapisan data dashboard Rumah Pandega.

Tugas file ini:
1. Buka koneksi ke Google Sheets `Rumah_Pandega_LIVE_v2` lewat service account
   (kredensial disimpan di .streamlit/secrets.toml -> backend, tidak pernah ke browser).
2. Baca tab mentah (2_PENGHUNI, 3_KEUANGAN, dst) untuk chart & tabel.
3. Baca + parse tab ringkasan `10_DASHBOARD` (auto-connect) untuk angka KPI.

Semua hasil di-cache 5 menit (ttl) supaya cepat & hemat kuota API.
"""

import re
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Nama section pada tab 10_DASHBOARD
SECTIONS = ["EXECUTIVE", "SALES", "MARKETING", "ADMIN", "OPERASIONAL"]


# ----------------------------------------------------------------------
# Util angka
# ----------------------------------------------------------------------
def to_num(x):
    """Ubah 'Rp1,800,000' / '0.95' / '' menjadi float. Gagal -> 0.0"""
    if x is None:
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if s == "" or s.lower() == "nan":
        return 0.0
    s = re.sub(r"[Rr]p", "", s)
    s = s.replace(",", "").replace("%", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def rupiah(x, juta=False):
    v = to_num(x)
    if juta:
        return f"Rp {v/1_000_000:,.1f} Jt".replace(",", ".")
    return f"Rp {v:,.0f}".replace(",", ".")


def persen(x):
    v = to_num(x)
    # nilai bisa berupa 0.95 (rasio) atau 95 (sudah persen)
    if abs(v) <= 1.5:
        v *= 100
    return f"{v:,.1f}%".replace(",", ".")


# ----------------------------------------------------------------------
# Koneksi
# ----------------------------------------------------------------------
def _conn():
    return st.connection("gsheets", type=GSheetsConnection)


@st.cache_data(ttl="5m", show_spinner=False)
def read_tab(worksheet: str, key_col: str | None = None) -> pd.DataFrame:
    """
    Baca satu tab. Jika key_col diberikan, buang baris kosong
    (sheet ini banyak baris filler kosong di bawah data).
    """
    try:
        df = _conn().read(worksheet=worksheet)
    except Exception as e:
        st.warning(f"Gagal baca tab '{worksheet}': {e}")
        return pd.DataFrame()
    df = df.dropna(how="all")
    if key_col and key_col in df.columns:
        df = df[df[key_col].astype(str).str.strip().ne("") & df[key_col].notna()]
    return df.reset_index(drop=True)


@st.cache_data(ttl="5m", show_spinner=False)
def read_dashboard() -> dict:
    """
    Parse tab 10_DASHBOARD yang berbentuk pasangan (label, nilai)
    dikelompokkan per section. Hasil: {SECTION: {label: nilai_mentah}}.
    """
    out = {s: {} for s in SECTIONS}
    try:
        raw = _conn().read(worksheet="10_DASHBOARD", header=None)
    except Exception:
        return out

    current = None
    for _, row in raw.iterrows():
        cells = [str(c).strip() for c in row.tolist() if str(c).strip() not in ("", "nan")]
        if not cells:
            continue
        first = cells[0].upper()
        if first in SECTIONS:
            current = first
            # kadang label+nilai ada di baris yang sama dengan judul section
            if len(cells) >= 3:
                out[current][cells[1]] = cells[2]
            continue
        if current and len(cells) >= 2:
            out[current][cells[0]] = cells[1]
    return out


# ----------------------------------------------------------------------
# Helper agregasi untuk chart (defensif: aman jika kolom/tab tak ada)
# ----------------------------------------------------------------------
def keuangan_per_bulan() -> pd.DataFrame:
    df = read_tab("3_KEUANGAN", key_col="Tanggal")
    if df.empty or "Bulan" not in df.columns:
        return pd.DataFrame()
    for c in ["Pendapatan Usaha", "Beban Usaha"]:
        if c in df.columns:
            df[c] = df[c].map(to_num)
        else:
            df[c] = 0.0
    g = df.groupby("Bulan")[["Pendapatan Usaha", "Beban Usaha"]].sum().reset_index()
    return g.sort_values("Bulan")


def penghuni() -> pd.DataFrame:
    return read_tab("2_PENGHUNI", key_col="ID")


def value_counts(df: pd.DataFrame, col: str) -> pd.Series:
    if df.empty or col not in df.columns:
        return pd.Series(dtype=int)
    return df[col].astype(str).str.strip().replace("", pd.NA).dropna().value_counts()


def funnel_sales() -> list[tuple[str, int]]:
    leads = len(read_tab("6_LEADS", key_col="Nama Leads"))
    survey = len(read_tab("7_SURVEY", key_col="Nama Calon"))
    bk = read_tab("8_BOOKING", key_col="No Booking")
    booking = 0 if bk.empty else int((~bk.get("Status", pd.Series()).astype(str)
                                      .str.contains("Batal", case=False, na=False)).sum())
    deal = 0 if bk.empty else int(bk.get("Status", pd.Series()).astype(str)
                                  .str.contains("Check-in|Konfirmasi", case=False, na=False).sum())
    return [("Leads", leads), ("Survey", survey), ("Booking", booking), ("Deal", deal)]


def konten() -> pd.DataFrame:
    return read_tab("4_KONTEN", key_col="Tgl Post")


def promosi() -> pd.DataFrame:
    return read_tab("5_PROMOSI", key_col="Nama Promosi")


def maintenance() -> pd.DataFrame:
    a = read_tab("9_PREVENTIVE", key_col="Lokasi/Item")
    b = read_tab("10_CORRECTIVE", key_col="Lokasi/Item")
    if not a.empty:
        a["Jenis Perawatan"] = "Preventif"
    if not b.empty:
        b["Jenis Perawatan"] = "Korektif"
    return pd.concat([a, b], ignore_index=True) if (not a.empty or not b.empty) else pd.DataFrame()
