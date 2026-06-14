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
def _read_tab_cached(worksheet: str, key_col: str | None = None) -> tuple:
    """Internal cached layer — returns (DataFrame, error_str|None)."""
    try:
        df = _conn().read(worksheet=worksheet)
    except Exception as e:
        return pd.DataFrame(), str(e)
    df = df.dropna(how="all")
    if key_col and key_col in df.columns:
        df = df[df[key_col].astype(str).str.strip().ne("") & df[key_col].notna()]
    return df.reset_index(drop=True), None


def read_tab(worksheet: str, key_col: str | None = None) -> pd.DataFrame:
    """
    Baca satu tab. Jika key_col diberikan, buang baris kosong.
    Warning ditampilkan di luar cache agar teks terbaca.
    """
    df, err = _read_tab_cached(worksheet, key_col)
    if err:
        st.warning(f"❌ Gagal baca tab **'{worksheet}'**: {err}")
    return df


@st.cache_data(ttl="5m", show_spinner=False)
def _read_dashboard_cached() -> tuple:
    """Internal cached layer — returns (dict, error_str|None)."""
    out = {s: {} for s in SECTIONS}
    try:
        raw = _conn().read(worksheet="10_DASHBOARD", header=None)
    except Exception as e:
        return out, str(e)

    current = None
    for _, row in raw.iterrows():
        cells = [str(c).strip() for c in row.tolist() if str(c).strip() not in ("", "nan")]
        if not cells:
            continue
        first = cells[0].upper()
        if first in SECTIONS:
            current = first
            if len(cells) >= 3:
                out[current][cells[1]] = cells[2]
            continue
        if current and len(cells) >= 2:
            out[current][cells[0]] = cells[1]
    return out, None


def read_dashboard() -> dict:
    """
    Parse tab 10_DASHBOARD. Warning ditampilkan di luar cache.
    """
    d, err = _read_dashboard_cached()
    if err:
        st.warning(f"❌ Gagal baca tab **'10_DASHBOARD'**: {err}")
    return d


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
    a = read_tab("9_PREVENTIVE MAINTENANCE", key_col="Lokasi/Item")
    b = read_tab("10_CORRECTIVE MAINTENANCE", key_col="Lokasi/Item")
    if not a.empty:
        a["Jenis Perawatan"] = "Preventif"
    if not b.empty:
        b["Jenis Perawatan"] = "Korektif"
    return pd.concat([a, b], ignore_index=True) if (not a.empty or not b.empty) else pd.DataFrame()


# ── Utilitas filter tanggal & tren histori ─────────────────────────────────

def filter_date(df: pd.DataFrame, date_col: str,
                d_from=None, d_to=None) -> pd.DataFrame:
    """Filter df berdasarkan rentang tanggal. Return salinan terfilter."""
    if df.empty or date_col not in df.columns or (d_from is None and d_to is None):
        return df
    ts = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
    mask = pd.Series(True, index=df.index)
    if d_from is not None:
        mask &= ts >= pd.Timestamp(d_from)
    if d_to is not None:
        mask &= ts <= pd.Timestamp(d_to)
    return df[mask].reset_index(drop=True)


def keuangan_trend(df=None) -> pd.DataFrame:
    """
    Agregasi Pendapatan / Beban / Laba / RevPAR per bulan.
    df: DataFrame 3_KEUANGAN yang sudah difilter, atau None untuk data penuh.
    """
    if df is None:
        df = read_tab("3_KEUANGAN", key_col="Tanggal")
    if df.empty or "Bulan" not in df.columns:
        return pd.DataFrame()
    df = df.copy()
    for c in ["Pendapatan Usaha", "Beban Usaha"]:
        if c in df.columns:
            df[c] = df[c].map(to_num)
        else:
            df[c] = 0.0
    g = df.groupby("Bulan")[["Pendapatan Usaha", "Beban Usaha"]].sum().reset_index()
    g["Laba"]   = g["Pendapatan Usaha"] - g["Beban Usaha"]
    g["RevPAR"] = g["Pendapatan Usaha"] / 29  # total kapasitas kamar
    return g.sort_values("Bulan").reset_index(drop=True)


def monthly_count(df: pd.DataFrame, date_col: str, label: str = "Count") -> pd.DataFrame:
    """Hitung jumlah baris per bulan kalender."""
    if df.empty or date_col not in df.columns:
        return pd.DataFrame(columns=["Bulan", label])
    d = df.copy()
    d["_dt"] = pd.to_datetime(d[date_col], errors='coerce', dayfirst=True)
    d = d.dropna(subset=["_dt"])
    if d.empty:
        return pd.DataFrame(columns=["Bulan", label])
    d["Bulan"] = d["_dt"].dt.to_period("M").astype(str)
    return (d.groupby("Bulan").size()
              .reset_index(name=label)
              .sort_values("Bulan")
              .reset_index(drop=True))


def monthly_sum(df: pd.DataFrame, date_col: str,
                value_col: str, label: str = "Nilai") -> pd.DataFrame:
    """Jumlahkan kolom numerik per bulan kalender."""
    if df.empty or date_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame(columns=["Bulan", label])
    d = df.copy()
    d["_dt"] = pd.to_datetime(d[date_col], errors='coerce', dayfirst=True)
    d = d.dropna(subset=["_dt"])
    if d.empty:
        return pd.DataFrame(columns=["Bulan", label])
    d["Bulan"]   = d["_dt"].dt.to_period("M").astype(str)
    d[value_col] = d[value_col].map(to_num)
    return (d.groupby("Bulan")[value_col].sum()
              .reset_index(name=label)
              .sort_values("Bulan")
              .reset_index(drop=True))


# ── KPI kalkulasi dari data mentah ─────────────────────────────────────────

def get_parameter() -> dict:
    """Baca 1_PARAMETER, kembalikan dict {Parameter: Nilai}."""
    df = read_tab("1_PARAMETER", "Parameter")
    if df.empty or "Parameter" not in df.columns or "Nilai" not in df.columns:
        return {}
    return df.set_index("Parameter")["Nilai"].to_dict()


def kpi_executive(keu_df: pd.DataFrame, penghuni_df: pd.DataFrame) -> dict:
    """
    Hitung KPI Eksekutif dari data mentah.
    keu_df       : 3_KEUANGAN (boleh difilter per periode)
    penghuni_df  : 2_PENGHUNI (selalu current-state, tidak difilter)
    """
    # ── Keuangan ──────────────────────────────────────────────────────────
    def _col_sum(df, col):
        return df[col].map(to_num).sum() if (not df.empty and col in df.columns) else 0.0

    pendapatan = _col_sum(keu_df, "Pendapatan Usaha")
    beban      = _col_sum(keu_df, "Beban Usaha")
    laba       = pendapatan - beban
    margin     = laba / pendapatan if pendapatan != 0 else 0.0

    # ── Hunian (current-state) ─────────────────────────────────────────────
    param       = get_parameter()
    total_kamar = max(1, int(to_num(param.get("Total Kamar", 29)) or 29))

    p = penghuni_df
    aktif   = 0 if (p.empty or "Status" not in p.columns) else \
              int(p["Status"].astype(str).str.strip().eq("Aktif").sum())
    booking = 0 if (p.empty or "Status" not in p.columns) else \
              int(p["Status"].astype(str).str.strip().eq("Booking (DP)").sum())
    terisi  = 0 if (p.empty or "Status Okupansi" not in p.columns) else \
              int(p["Status Okupansi"].astype(str).str.strip().eq("Terisi").sum())

    occ_k  = (aktif + booking) / total_kamar
    occ_f  = terisi / total_kamar
    revpar  = pendapatan / total_kamar

    return {
        "pendapatan":      pendapatan,
        "beban":           beban,
        "laba":            laba,
        "margin":          margin,
        "occ_komitmen":    occ_k,
        "occ_fisik":       occ_f,
        "revpar":          revpar,
        "penghuni_aktif":  aktif,
        "total_kamar":     total_kamar,
    }


def kpi_sales(lead_df: pd.DataFrame,
              survey_df: pd.DataFrame,
              booking_df: pd.DataFrame) -> dict:
    """Hitung KPI Sales dari data mentah (semua boleh difilter per periode)."""
    n_leads  = len(lead_df)
    n_survey = len(survey_df)

    # Leads belum di-follow-up
    fu_col  = next((c for c in ["Status FU", "Status Follow Up", "Follow Up", "FU"]
                    if not lead_df.empty and c in lead_df.columns), None)
    belum_fu = 0
    if fu_col:
        belum_fu = int(lead_df[fu_col].astype(str).str.strip()
                       .isin(["", "nan", "-", "Belum"]).sum())

    # Booking & deals
    n_booking = n_batal = n_deal = 0
    nilai_deal = 0.0
    if not booking_df.empty and "Status" in booking_df.columns:
        st_col    = booking_df["Status"].astype(str).str.strip()
        n_batal   = int(st_col.str.contains("Batal", case=False, na=False).sum())
        n_booking = int((~st_col.str.contains("Batal", case=False, na=False)).sum())
        deal_mask = st_col.str.contains("Check-in|Konfirmasi", case=False, na=False)
        n_deal    = int(deal_mask.sum())
        if "Nilai Kontrak" in booking_df.columns:
            nilai_deal = booking_df.loc[deal_mask, "Nilai Kontrak"].map(to_num).sum()

    n_total_bk  = len(booking_df) if not booking_df.empty else 0
    cancel_rate = n_batal / n_total_bk if n_total_bk > 0 else 0.0
    conv_ls     = n_survey / n_leads  if n_leads   > 0 else 0.0
    conv_sd     = n_deal   / n_survey if n_survey  > 0 else 0.0

    return {
        "total_leads":      n_leads,
        "belum_fu":         belum_fu,
        "conv_lead_survey": conv_ls,
        "conv_survey_deal": conv_sd,
        "nilai_deal":       nilai_deal,
        "cancel_rate":      cancel_rate,
    }


def kpi_admin(penghuni_df: pd.DataFrame) -> dict:
    """Hitung KPI Admin dari status penghuni saat ini (current-state)."""
    p = penghuni_df
    if p.empty:
        return {"jatuh_tempo_7": 0, "overdue": 0, "kosong": 0, "kontrak_30": 0}

    sisa = p["Sisa Hari"].map(to_num) if "Sisa Hari" in p.columns else pd.Series(0.0, index=p.index)
    jatuh_7    = int(((sisa > 0) & (sisa <= 7)).sum())
    overdue    = int((sisa < 0).sum())
    kontrak_30 = int(((sisa > 0) & (sisa <= 30)).sum())

    if "Status Okupansi" in p.columns:
        kosong = int(p["Status Okupansi"].astype(str).str.strip().eq("Kosong").sum())
    elif "Status" in p.columns:
        kosong = int(p["Status"].astype(str).str.strip().eq("Non Aktif").sum())
    else:
        kosong = 0

    return {
        "jatuh_tempo_7": jatuh_7,
        "overdue":       overdue,
        "kosong":        kosong,
        "kontrak_30":    kontrak_30,
    }


def kpi_marketing(konten_df: pd.DataFrame,
                  promosi_df: pd.DataFrame,
                  lead_df: pd.DataFrame,
                  booking_df: pd.DataFrame) -> dict:
    """Hitung KPI Marketing dari data mentah (boleh difilter)."""
    total_reach = total_eng = belum_tayang = 0
    avg_er = 0.0
    if not konten_df.empty:
        total_reach = int(konten_df["Reach"].map(to_num).sum()) \
                      if "Reach" in konten_df.columns else 0
        total_eng   = int(konten_df["Engagement"].map(to_num).sum()) \
                      if "Engagement" in konten_df.columns else 0
        er_col = next((c for c in ["ER (%)", "ER", "Engagement Rate"]
                       if c in konten_df.columns), None)
        if er_col:
            avg_er = float(konten_df[er_col].map(to_num).mean() or 0)
        if "Status" in konten_df.columns:
            belum_tayang = int(
                konten_df["Status"].astype(str).str.strip()
                .isin(["Draft", "Scheduled", "Belum Tayang", "Dijadwalkan"]).sum())

    total_spend = avg_cpl = 0.0
    if not promosi_df.empty:
        spend_col = next((c for c in ["Total Spend", "Spend", "Budget", "Total Budget"]
                          if c in promosi_df.columns), None)
        if spend_col:
            total_spend = float(promosi_df[spend_col].map(to_num).sum())
        cpl_col = next((c for c in ["CPL", "Cost per Lead"]
                        if c in promosi_df.columns), None)
        if cpl_col:
            vals = promosi_df[cpl_col].map(to_num)
            avg_cpl = float(vals[vals > 0].mean()) if (vals > 0).any() else 0.0

    n_leads   = len(lead_df)
    n_booking = 0
    if not booking_df.empty and "Status" in booking_df.columns:
        n_booking = int(
            (~booking_df["Status"].astype(str)
              .str.contains("Batal", case=False, na=False)).sum())
    conv_lb = n_booking / n_leads if n_leads > 0 else 0.0

    return {
        "total_reach":       total_reach,
        "total_engagement":  total_eng,
        "avg_er":            avg_er,
        "avg_cpl":           avg_cpl,
        "total_spend":       total_spend,
        "conv_lead_booking": conv_lb,
        "belum_tayang":      belum_tayang,
    }


def kpi_operasional(mt_df: pd.DataFrame) -> dict:
    """Hitung KPI Operasional dari data maintenance (boleh difilter)."""
    if mt_df.empty:
        return {"total_tiket": 0, "selesai": 0, "breach_sla": 0,
                "mttr": 0.0, "biaya": 0.0, "rasio": "N/A"}

    total   = len(mt_df)
    selesai = 0
    if "Status" in mt_df.columns:
        selesai = int(mt_df["Status"].astype(str).str.strip().eq("Selesai").sum())

    breach = 0
    if "SLA OK?" in mt_df.columns:
        breach = int(mt_df["SLA OK?"].astype(str).str.strip()
                     .isin(["No", "Tidak", "N", "FALSE", "False"]).sum())

    # MTTR — rata-rata hari penyelesaian
    mttr = 0.0
    if "Tgl Lapor/Jadwal" in mt_df.columns and "Tgl Selesai" in mt_df.columns:
        t0   = pd.to_datetime(mt_df["Tgl Lapor/Jadwal"], errors='coerce', dayfirst=True)
        t1   = pd.to_datetime(mt_df["Tgl Selesai"],       errors='coerce', dayfirst=True)
        days = (t1 - t0).dt.days
        valid = days[(days >= 0) & days.notna()]
        mttr = round(float(valid.mean()), 1) if not valid.empty else 0.0

    biaya = 0.0
    if "Biaya" in mt_df.columns:
        biaya = float(mt_df["Biaya"].map(to_num).sum())

    rasio = "N/A"
    if "Jenis Perawatan" in mt_df.columns:
        n_p = int(mt_df["Jenis Perawatan"].astype(str).str.strip().eq("Preventif").sum())
        n_k = int(mt_df["Jenis Perawatan"].astype(str).str.strip().eq("Korektif").sum())
        rasio = f"{n_p}:{n_k}"

    return {
        "total_tiket": total,
        "selesai":     selesai,
        "breach_sla":  breach,
        "mttr":        mttr,
        "biaya":       biaya,
        "rasio":       rasio,
    }
