"""
data.py — Lapisan data dashboard Rumah Pandega.

Tugas file ini:
1. Koneksi ke Google Sheets lewat service account.
2. Baca tab mentah (2_PENGHUNI, 3_KEUANGAN, 3_DAFTAR_AKUN, dst) untuk chart & tabel.
3. Hitung semua KPI dari data mentah — tidak dari tab pre-summarized.

Semua hasil di-cache 5 menit (ttl) supaya cepat & hemat kuota API.
"""

import re
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection


# ── Util angka ───────────────────────────────────────────────────────────────
def to_num(x):
    """Ubah 'Rp1,800,000' / '0.95' / '' / '-' menjadi float. Gagal -> 0.0"""
    if x is None:
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if s in ("", "-", "nan"):
        return 0.0
    s = re.sub(r"[Rr]p\s*", "", s)
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


# ── Koneksi ──────────────────────────────────────────────────────────────────
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


# ── Akun (Chart of Accounts) ─────────────────────────────────────────────────
_PENDAPATAN_TIPE = {"Pendapatan"}
_BEBAN_TIPE      = {"Beban", "Beban Non-Operasional"}


def _akun_map() -> dict:
    """Return {Nama Akun: Tipe Akun} dari 3_DAFTAR_AKUN."""
    df = read_tab("3_DAFTAR_AKUN")
    if df.empty or "Nama Akun" not in df.columns or "Tipe Akun" not in df.columns:
        return {}
    return df.set_index("Nama Akun")["Tipe Akun"].to_dict()


def _compute_keuangan(df: pd.DataFrame) -> pd.DataFrame:
    """
    Dari df transaksi double-entry (3_KEUANGAN baru), tambah kolom:
    - _pendapatan : Nominal jika Akun Kredit = akun Pendapatan (4xxx)
    - _beban      : Nominal jika Akun Debit  = akun Beban (5xxx / 6xxx)

    Fallback: jika 3_DAFTAR_AKUN kosong/tidak ada, pakai kolom 'Dampak Laba'
    (positif = pendapatan; beban tidak terdeteksi).
    """
    if df.empty:
        return df

    akun = _akun_map()
    d    = df.copy()
    d["Nominal"] = (d["Nominal"].map(to_num)
                    if "Nominal" in d.columns
                    else pd.Series(0.0, index=d.index))

    if akun:
        kredit_tipe = (d["Akun Kredit"].astype(str).str.strip()
                       .map(lambda x: akun.get(x, ""))
                       if "Akun Kredit" in d.columns
                       else pd.Series("", index=d.index))
        debit_tipe  = (d["Akun Debit"].astype(str).str.strip()
                       .map(lambda x: akun.get(x, ""))
                       if "Akun Debit" in d.columns
                       else pd.Series("", index=d.index))
        d["_pendapatan"] = d["Nominal"].where(kredit_tipe.isin(_PENDAPATAN_TIPE), 0.0)
        d["_beban"]      = d["Nominal"].where(debit_tipe.isin(_BEBAN_TIPE),       0.0)
    elif "Dampak Laba" in d.columns:
        # Fallback — kolom Dampak Laba: positif = pendapatan
        dampak = d["Dampak Laba"].map(to_num)
        d["_pendapatan"] = dampak.where(dampak > 0, 0.0)
        d["_beban"]      = (-dampak).where(dampak < 0, 0.0)
    else:
        d["_pendapatan"] = 0.0
        d["_beban"]      = 0.0

    return d


# ── Helper agregasi ──────────────────────────────────────────────────────────
def penghuni() -> pd.DataFrame:
    return read_tab("2_PENGHUNI", key_col="ID")


def value_counts(df: pd.DataFrame, col: str) -> pd.Series:
    if df.empty or col not in df.columns:
        return pd.Series(dtype=int)
    return df[col].astype(str).str.strip().replace("", pd.NA).dropna().value_counts()


def funnel_sales() -> list[tuple[str, int]]:
    leads   = len(read_tab("6_LEADS", key_col="Nama Leads"))
    survey  = len(read_tab("7_SURVEY", key_col="Nama Calon"))
    bk      = read_tab("8_BOOKING", key_col="No Booking")
    booking = 0 if bk.empty else int((~bk.get("Status", pd.Series()).astype(str)
                                      .str.contains("Batal", case=False, na=False)).sum())
    deal    = 0 if bk.empty else int(bk.get("Status", pd.Series()).astype(str)
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
        a = a.copy(); a["Jenis Perawatan"] = "Preventif"
    if not b.empty:
        b = b.copy(); b["Jenis Perawatan"] = "Korektif"
    return pd.concat([a, b], ignore_index=True) if (not a.empty or not b.empty) else pd.DataFrame()


# ── Filter & tren ────────────────────────────────────────────────────────────
def filter_date(df: pd.DataFrame, date_col: str,
                d_from=None, d_to=None) -> pd.DataFrame:
    """Filter df berdasarkan rentang tanggal. Return salinan terfilter."""
    if df.empty or not date_col or date_col not in df.columns or (d_from is None and d_to is None):
        return df
    ts   = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
    mask = pd.Series(True, index=df.index)
    if d_from is not None:
        mask &= ts >= pd.Timestamp(d_from)
    if d_to is not None:
        mask &= ts <= pd.Timestamp(d_to)
    return df[mask].reset_index(drop=True)


def keuangan_trend(df=None) -> pd.DataFrame:
    """
    Agregasi Pendapatan / Beban / Laba / RevPAR per bulan dari transaksi double-entry.
    df: DataFrame 3_KEUANGAN (boleh difilter per periode); None = baca data penuh.
    RevPAR dihitung dari total_kamar di 1_PARAMETER — tidak hardcoded.
    """
    if df is None:
        df = read_tab("3_KEUANGAN", key_col="Tanggal")
    if df.empty or "Tanggal" not in df.columns:
        return pd.DataFrame()

    # Ambil total_kamar dari parameter (tidak hardcode)
    param       = get_parameter()
    total_kamar = max(1, int(to_num(param.get("Total Kamar", 29)) or 29))

    d = _compute_keuangan(df)
    d["_dt"] = pd.to_datetime(d["Tanggal"], errors='coerce', dayfirst=True)
    d = d.dropna(subset=["_dt"])
    if d.empty:
        return pd.DataFrame()

    d["Bulan"] = d["_dt"].dt.to_period("M").astype(str)  # "2026-04"
    g = (d.groupby("Bulan")[["_pendapatan", "_beban"]].sum()
          .rename(columns={"_pendapatan": "Pendapatan Usaha", "_beban": "Beban Usaha"})
          .reset_index())
    g = g.sort_values("Bulan")
    g["Laba"]   = g["Pendapatan Usaha"] - g["Beban Usaha"]
    g["RevPAR"] = g["Pendapatan Usaha"] / total_kamar

    # Format label bulan jadi "Apr 2026" untuk sumbu X
    g["Bulan"] = pd.to_datetime(g["Bulan"]).dt.strftime("%b %Y")
    return g.reset_index(drop=True)


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
    g = (d.groupby("Bulan").size()
          .reset_index(name=label)
          .sort_values("Bulan"))
    g["Bulan"] = pd.to_datetime(g["Bulan"]).dt.strftime("%b %Y")
    return g.reset_index(drop=True)


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
    g = (d.groupby("Bulan")[value_col].sum()
          .reset_index(name=label)
          .sort_values("Bulan"))
    g["Bulan"] = pd.to_datetime(g["Bulan"]).dt.strftime("%b %Y")
    return g.reset_index(drop=True)


# ── Parameter ─────────────────────────────────────────────────────────────────
def get_parameter() -> dict:
    """Baca 1_PARAMETER, kembalikan dict {Parameter: Nilai}."""
    df = read_tab("1_PARAMETER", "Parameter")
    if df.empty or "Parameter" not in df.columns or "Nilai" not in df.columns:
        return {}
    return df.set_index("Parameter")["Nilai"].to_dict()


# ── KPI dari data mentah ──────────────────────────────────────────────────────
def kpi_executive(keu_df: pd.DataFrame, penghuni_df: pd.DataFrame) -> dict:
    """
    Hitung KPI Eksekutif dari data mentah.
    keu_df       : 3_KEUANGAN terfilter (double-entry format baru)
    penghuni_df  : 2_PENGHUNI current-state (selalu tanpa filter tanggal)
    """
    d          = _compute_keuangan(keu_df)
    pendapatan = float(d["_pendapatan"].sum()) if "_pendapatan" in d.columns else 0.0
    beban      = float(d["_beban"].sum())      if "_beban"      in d.columns else 0.0
    laba       = pendapatan - beban

    # Fix: margin negatif jika rugi, bukan 0
    if pendapatan > 0:
        margin = laba / pendapatan
    elif beban > 0:
        margin = -1.0      # rugi total — tampilkan ≈ -100%
    else:
        margin = 0.0

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
    revpar = pendapatan / total_kamar

    return {
        "pendapatan":     pendapatan,
        "beban":          beban,
        "laba":           laba,
        "margin":         margin,
        "occ_komitmen":   occ_k,
        "occ_fisik":      occ_f,
        "revpar":         revpar,
        "penghuni_aktif": aktif,
        "total_kamar":    total_kamar,
    }


def kpi_sales(lead_df: pd.DataFrame,
              survey_df: pd.DataFrame,
              booking_df: pd.DataFrame) -> dict:
    """Hitung KPI Sales dari data mentah (semua boleh difilter per periode)."""
    n_leads  = len(lead_df)
    n_survey = len(survey_df)

    fu_col  = next((c for c in ["Status FU", "Status Follow Up", "Follow Up", "FU"]
                    if not lead_df.empty and c in lead_df.columns), None)
    belum_fu = 0
    if fu_col:
        belum_fu = int(lead_df[fu_col].astype(str).str.strip()
                       .isin(["", "nan", "-", "Belum"]).sum())

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


def kpi_admin(penghuni_df: pd.DataFrame,
              all_penghuni_df: pd.DataFrame | None = None) -> dict:
    """
    Hitung KPI Admin.
    penghuni_df     : boleh difilter (e.g. by Tgl Jatuh Tempo) untuk KPI berbasis Sisa Hari.
    all_penghuni_df : full dataset current-state untuk menghitung kamar kosong.
                      Jika None, pakai penghuni_df.
    """
    p     = penghuni_df
    p_all = all_penghuni_df if all_penghuni_df is not None else penghuni_df

    if p.empty and p_all.empty:
        return {"jatuh_tempo_7": 0, "overdue": 0, "kosong": 0, "kontrak_30": 0}

    sisa = (p["Sisa Hari"].map(to_num)
            if (not p.empty and "Sisa Hari" in p.columns)
            else pd.Series(dtype=float))
    jatuh_7    = int(((sisa > 0) & (sisa <= 7)).sum())
    overdue    = int((sisa < 0).sum())
    kontrak_30 = int(((sisa > 0) & (sisa <= 30)).sum())

    if not p_all.empty and "Status Okupansi" in p_all.columns:
        kosong = int(p_all["Status Okupansi"].astype(str).str.strip().eq("Kosong").sum())
    elif not p_all.empty and "Status" in p_all.columns:
        kosong = int(p_all["Status"].astype(str).str.strip().eq("Non Aktif").sum())
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

    mttr = 0.0
    if "Tgl Lapor/Jadwal" in mt_df.columns and "Tgl Selesai" in mt_df.columns:
        t0    = pd.to_datetime(mt_df["Tgl Lapor/Jadwal"], errors='coerce', dayfirst=True)
        t1    = pd.to_datetime(mt_df["Tgl Selesai"],       errors='coerce', dayfirst=True)
        days  = (t1 - t0).dt.days
        valid = days[(days >= 0) & days.notna()]
        mttr  = round(float(valid.mean()), 1) if not valid.empty else 0.0

    biaya = 0.0
    if "Biaya" in mt_df.columns:
        biaya = float(mt_df["Biaya"].map(to_num).sum())

    rasio = "N/A"
    if "Jenis Perawatan" in mt_df.columns:
        n_p   = int(mt_df["Jenis Perawatan"].astype(str).str.strip().eq("Preventif").sum())
        n_k   = int(mt_df["Jenis Perawatan"].astype(str).str.strip().eq("Korektif").sum())
        rasio = f"{n_p}:{n_k}"

    return {
        "total_tiket": total,
        "selesai":     selesai,
        "breach_sla":  breach,
        "mttr":        mttr,
        "biaya":       biaya,
        "rasio":       rasio,
    }
