"""
app.py — Dashboard Rumah Pandega (Streamlit).
UI disesuaikan dengan desain Figma: Kost Management Dashboard UI
"""

import plotly.graph_objects as go
import streamlit as st
import streamlit_authenticator as stauth

import data as D

# ============================ KONFIG HALAMAN ============================
st.set_page_config(page_title="Rumah Pandega — Dashboard",
                   page_icon="🏠", layout="wide",
                   initial_sidebar_state="expanded")

ACCENT = {
    "Executive":   "#4F46E5",
    "Sales":       "#059669",
    "Admin":       "#2563EB",
    "Marketing":   "#7C3AED",
    "Operasional": "#EA580C",
}

st.markdown("""
<style>
/* ── Layout ── */
.block-container {padding-top:1.5rem;padding-bottom:2rem;max-width:none;}
.stApp {background:#F1F5F9 !important;}
[data-testid="stMain"] {background:#F1F5F9 !important;}
section.main {background:#F1F5F9 !important;}

/* ── Login Form ── */
[data-testid="stForm"] {background:white;border-radius:16px;padding:8px 4px;}
[data-testid="stForm"] p,
[data-testid="stForm"] h1,
[data-testid="stForm"] h2,
[data-testid="stForm"] h3 {color:#0F172A !important;font-weight:700;}
.stTextInput label,
.stTextInput > div > label {color:#374151 !important;font-weight:500;font-size:13px;}
.stTextInput input {
    background:#F8FAFC !important;color:#0F172A !important;
    border:1px solid #E2E8F0 !important;border-radius:8px !important;
}
.stTextInput input:focus {border-color:#4F46E5 !important;box-shadow:none !important;}
[data-testid="stFormSubmitButton"] button {
    background:#4F46E5 !important;color:white !important;
    border:none !important;border-radius:8px !important;
    font-weight:600 !important;
}
[data-testid="stFormSubmitButton"] button:hover {background:#4338CA !important;}

/* ── Sidebar ── */
[data-testid="stSidebar"] {background:#0F172A;}
[data-testid="stSidebar"] * {color:#E2E8F0;}
[data-testid="stSidebar"] .stRadio > label {display:none;}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    padding:10px 12px !important;
    border-radius:10px !important;
    font-size:13px !important;
    color:#94A3B8 !important;
    font-weight:500 !important;
    display:block;
    cursor:pointer;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) {
    background:#1E293B !important;
    color:#FFFFFF !important;
    border-left:3px solid #4F46E5 !important;
    font-weight:600 !important;
}

/* ── KPI Card ── */
.kpi {
    background:#FFFFFF;border:1px solid #E8EDF3;border-radius:16px;
    padding:16px 20px;margin-bottom:4px;min-height:108px;
}
.kpi .lab  {font-size:12px;color:#64748B;font-weight:500;margin-bottom:4px;}
.kpi .val  {font-size:22px;color:#0F172A;font-weight:700;margin:0 0 6px;}
.kpi .sub  {font-size:11px;color:#64748B;}
.kpi .sub.pos  {color:#16A34A;font-weight:600;}
.kpi .sub.neg  {color:#DC2626;font-weight:600;}
.kpi .sub.warn {color:#D97706;font-weight:600;}

/* ── Chart Header ── */
.cht-hdr {
    background:white;border:1px solid #E8EDF3;border-radius:16px 16px 0 0;
    padding:16px 20px 10px;margin-top:0;
}
.cht-hdr .cht-t {font-size:15px;font-weight:600;color:#0F172A;margin:0 0 2px;}
.cht-hdr .cht-s {font-size:11px;color:#94A3B8;margin:0;}
.cht-body {
    background:white;border:1px solid #E8EDF3;border-top:none;
    border-radius:0 0 16px 16px;padding:0 12px 8px;
}

/* ── Table ── */
[data-testid="stDataFrame"] {border-radius:12px;overflow:hidden;}
</style>
""", unsafe_allow_html=True)


# ============================ AUTENTIKASI ============================
def build_authenticator():
    users = st.secrets["auth"]["credentials"]["usernames"]
    credentials = {"usernames": {
        u: {"name": v["name"], "email": v.get("email", ""), "password": v["password"]}
        for u, v in users.items()
    }}
    ck = st.secrets["auth"]["cookie"]
    return stauth.Authenticate(credentials, ck["name"], ck["key"],
                               int(ck.get("expiry_days", 7)))


authenticator = build_authenticator()
authenticator.login(location='main', fields={'Form name': 'Masuk Dashboard'})
name       = st.session_state.get("name") or ""
auth_status = st.session_state.get("authentication_status")
username   = st.session_state.get("username") or ""

if auth_status is False:
    st.error("Username / password salah.")
    st.stop()
if auth_status is None:
    st.info("Silakan login untuk melihat dashboard.")
    st.stop()


# ============================ KOMPONEN UI ============================
def kpi(col, label, value, sub="", sub_type=""):
    sub_class = f"sub {sub_type}".strip()
    col.markdown(
        f'<div class="kpi">'
        f'<div class="lab">{label}</div>'
        f'<div class="val">{value}</div>'
        f'<div class="{sub_class}">{sub}</div>'
        f'</div>',
        unsafe_allow_html=True)


def chart_header(title, subtitle=""):
    """Panggil di dalam with-block kolom."""
    st.markdown(
        f'<div class="cht-hdr">'
        f'<p class="cht-t">{title}</p>'
        f'<p class="cht-s">{subtitle}</p>'
        f'</div>',
        unsafe_allow_html=True)


def _chart_layout(height=260, margin=None):
    m = margin or dict(t=10, b=30, l=10, r=10)
    return dict(
        height=height, margin=m,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickfont=dict(size=9, color='#94A3B8')),
        yaxis=dict(showgrid=True, gridcolor='#F1F5F9',
                   tickfont=dict(size=9, color='#94A3B8')),
    )


def donut(labels, values, colors, total_label=""):
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=.62,
                           marker=dict(colors=colors), sort=False))
    fig.update_layout(
        height=260, margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        annotations=[dict(text=total_label, showarrow=False, font_size=16)],
        legend=dict(orientation='v', x=1.05, y=0.5, font=dict(size=11)))
    return fig


def bars(x, y, color, horizontal=False):
    if horizontal:
        fig = go.Figure(go.Bar(x=y, y=x, orientation="h", marker_color=color,
                               marker_line_width=0))
    else:
        fig = go.Figure(go.Bar(x=x, y=y, marker_color=color, marker_line_width=0))
    fig.update_layout(**_chart_layout())
    return fig


def line_bars(kb, ac):
    fig = go.Figure()
    fig.add_scatter(x=kb["Bulan"], y=kb["Pendapatan Usaha"], name="Pendapatan",
                    line=dict(color=ac, width=2.5),
                    fill='tozeroy', fillcolor='rgba(79,70,229,0.08)')
    fig.add_scatter(x=kb["Bulan"], y=kb["Beban Usaha"], name="Beban",
                    line=dict(color="#DC2626", width=2))
    fig.update_layout(
        **_chart_layout(height=240),
        legend=dict(orientation='h', y=1.12, x=0, font=dict(size=11)))
    return fig


# ============================ SIDEBAR ============================
with st.sidebar:
    initials = "".join(w[0] for w in name.split()[:2]).upper() if name else "?"
    st.markdown(f"""
<div style="padding:8px 4px 16px;">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="background:#4F46E5;width:32px;height:32px;border-radius:9px;
                flex-shrink:0;display:flex;align-items:center;justify-content:center;
                font-weight:700;font-size:14px;color:white;">K</div>
    <div>
      <div style="font-weight:700;font-size:17px;color:white;line-height:1.2;">KostPro</div>
      <div style="font-size:10px;color:#64748B;">Property Suite</div>
    </div>
  </div>
</div>
<p style="font-size:10px;font-weight:600;color:#475569;letter-spacing:.08em;
          margin:0 0 4px 4px;">MENU</p>
""", unsafe_allow_html=True)

    menu = st.radio("", list(ACCENT.keys()))
    st.divider()

    st.markdown(f"""
<div style="background:#1E293B;border-radius:12px;padding:12px 14px;margin:0 2px;">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="background:#4F46E5;border-radius:50%;width:32px;height:32px;flex-shrink:0;
                display:flex;align-items:center;justify-content:center;
                font-weight:700;font-size:12px;color:white;">{initials}</div>
    <div>
      <div style="font-size:12px;font-weight:600;color:white;line-height:1.3;">{name}</div>
      <div style="font-size:10px;color:#64748B;">{menu}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    authenticator.logout("Logout", "sidebar")
    if st.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

DASH = D.read_dashboard()
ac   = ACCENT[menu]


# ============================ EXECUTIVE ============================
if menu == "Executive":
    e = DASH.get("EXECUTIVE", {})
    st.markdown('<h2 style="font-size:24px;font-weight:700;color:#0F172A;margin:0 0 2px;">Ringkasan Eksekutif</h2>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#64748B;margin:0 0 20px;">Kinerja portofolio kost · BOD / Owner</p>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Pendapatan Bulan Ini",
        D.rupiah(e.get("Pendapatan Usaha", 0), juta=True),
        f"Beban {D.rupiah(e.get('Beban Usaha', 0), juta=True)}")
    kpi(c2, "Tingkat Hunian",
        D.persen(e.get("Okupansi Komitmen", 0)),
        f"Fisik {D.persen(e.get('Okupansi Fisik', 0))}", "pos")
    kpi(c3, "Laba / Margin Usaha",
        D.rupiah(e.get("Laba Usaha", 0), juta=True),
        f"Margin {D.persen(e.get('Margin Usaha', 0))}",
        "pos" if D.to_num(e.get("Laba Usaha", 0)) >= 0 else "neg")
    kpi(c4, "RevPAR",
        D.rupiah(e.get("RevPAR (pendapatan/kamar)", 0)),
        f"Penghuni aktif: {e.get('Penghuni Aktif', '-')}")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    g1, g2 = st.columns([2, 1])
    with g1:
        chart_header("Tren Pendapatan vs Biaya Operasional", "12 bulan terakhir (Rp Juta)")
        kb = D.keuangan_per_bulan()
        if kb.empty:
            st.info("Belum ada data 3_KEUANGAN.")
        else:
            st.plotly_chart(line_bars(kb, ac), use_container_width=True)

    with g2:
        chart_header("Status Penghuni", "Komposisi saat ini")
        vc = D.value_counts(D.penghuni(), "Status")
        if vc.empty:
            st.info("Belum ada data 2_PENGHUNI.")
        else:
            st.plotly_chart(donut(vc.index.tolist(), vc.values.tolist(),
                                  ["#16A34A", "#F59E0B", "#94A3B8", "#DC2626"],
                                  f"{int(vc.sum())} org"), use_container_width=True)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    g3, g4 = st.columns(2)
    p = D.penghuni()
    with g3:
        chart_header("Okupansi per Jenis Kamar", "Jumlah kamar terisi")
        if not p.empty and "Jenis Kamar" in p.columns:
            if "Status Okupansi" in p.columns:
                terisi = p[p["Status Okupansi"].astype(str).str.contains("Terisi", na=False)]
            else:
                terisi = p
            vc = D.value_counts(terisi, "Jenis Kamar")
            if not vc.empty:
                st.plotly_chart(bars(vc.index.tolist(), vc.values.tolist(), ac),
                                use_container_width=True)
            else:
                st.info("Belum ada kamar terisi.")
        else:
            st.info("Kolom 'Jenis Kamar' tidak ditemukan.")

    with g4:
        chart_header("Arus Kas", "Pendapatan vs Beban per bulan")
        kb = D.keuangan_per_bulan()
        if not kb.empty:
            fig = go.Figure()
            fig.add_bar(x=kb["Bulan"], y=kb["Pendapatan Usaha"], name="Masuk",
                        marker_color="#22C55E", marker_line_width=0)
            fig.add_bar(x=kb["Bulan"], y=kb["Beban Usaha"], name="Keluar",
                        marker_color="#DC2626", marker_line_width=0)
            fig.update_layout(**_chart_layout(), barmode="group",
                              legend=dict(orientation='h', y=1.12, x=0, font=dict(size=11)))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Belum ada data keuangan.")

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    chart_header("Daftar Penghuni", "Data lengkap penghuni aktif")
    if not p.empty:
        cols = [c for c in ["No Kamar", "Nama Lengkap", "Jenis Kamar", "Status",
                             "Tgl Jatuh Tempo", "Flag Tagih", "Tarif Sewa"] if c in p.columns]
        st.dataframe(p[cols], use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data penghuni.")


# ============================ SALES ============================
elif menu == "Sales":
    s = DASH.get("SALES", {})
    st.markdown('<h2 style="font-size:24px;font-weight:700;color:#0F172A;margin:0 0 2px;">Dashboard Sales</h2>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#64748B;margin:0 0 20px;">Akuisisi penyewa & pipeline</p>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Total Leads", str(s.get("Total Leads", "-")),
        f"Belum di-FU: {s.get('Leads belum di-FU', '-')}")
    kpi(c2, "Konversi Lead→Survey", D.persen(s.get("Konversi Lead->Survey", 0)), "", "pos")
    kpi(c3, "Konversi Survey→Deal", D.persen(s.get("Konversi Survey->Deal", 0)), "", "pos")
    kpi(c4, "Nilai Kontrak Deal",
        D.rupiah(s.get("Nilai Kontrak Deal", 0), juta=True),
        f"Cancel rate {D.persen(s.get('Cancel Rate', 0))}")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        chart_header("Funnel Penjualan", "Lead → Survey → Booking → Deal")
        fn = D.funnel_sales()
        fig = go.Figure(go.Funnel(y=[a for a, _ in fn], x=[b for _, b in fn],
                                  marker=dict(color=ac)))
        fig.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10),
                          paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        chart_header("Sumber Leads", "Distribusi per channel")
        vc = D.value_counts(D.read_tab("6_LEADS", "Nama Leads"), "Sumber Leads")
        if vc.empty:
            st.info("Belum ada data 6_LEADS.")
        else:
            st.plotly_chart(donut(vc.index.tolist(), vc.values.tolist(),
                                  ["#059669", "#34D399", "#3B82F6", "#F59E0B"],
                                  f"{int(vc.sum())}"), use_container_width=True)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    chart_header("Pipeline Booking", "Status transaksi aktif")
    bk = D.read_tab("8_BOOKING", "No Booking")
    if not bk.empty:
        cols = [c for c in ["No Booking", "Nama Penyewa", "Kamar", "Tgl Masuk",
                             "Nilai Kontrak", "Sumber", "Status"] if c in bk.columns]
        st.dataframe(bk[cols], use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data 8_BOOKING.")


# ============================ ADMIN ============================
elif menu == "Admin":
    a = DASH.get("ADMIN", {})
    st.markdown('<h2 style="font-size:24px;font-weight:700;color:#0F172A;margin:0 0 2px;">Dashboard Admin & Keuangan</h2>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#64748B;margin:0 0 20px;">Penagihan, kontrak & hunian</p>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Jatuh Tempo ≤7 hari",  str(a.get("Jatuh tempo <=7 hari", "-")),   "", "neg")
    kpi(c2, "Tunggakan / Overdue",   str(a.get("Tunggakan / overdue", "-")),    "", "neg")
    kpi(c3, "Kamar Kosong",          str(a.get("Kamar kosong", "-")),            "")
    kpi(c4, "Kontrak Berakhir ≤30 hari", str(a.get("Kontrak berakhir <=30 hari", "-")), "", "warn")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    p = D.penghuni()
    g1, g2 = st.columns(2)
    with g1:
        chart_header("Flag Tagih", "Distribusi status tagihan")
        vc = D.value_counts(p, "Flag Tagih")
        if not vc.empty:
            st.plotly_chart(bars(vc.index.tolist(), vc.values.tolist(), ac),
                            use_container_width=True)
        else:
            st.info("Belum ada data flag tagih.")

    with g2:
        chart_header("Status Hunian", "Terisi vs Kosong")
        vc = D.value_counts(p, "Status Okupansi")
        if not vc.empty:
            st.plotly_chart(donut(vc.index.tolist(), vc.values.tolist(),
                                  ["#16A34A", "#DC2626"], f"{int(vc.sum())}"),
                            use_container_width=True)
        else:
            st.info("Belum ada data status hunian.")

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    chart_header("Penghuni Mendekati Jatuh Tempo", "Prioritas penagihan")
    if not p.empty and "Flag Tagih" in p.columns:
        prioritas = p[p["Flag Tagih"].astype(str).str.contains("SEGERA|LEWAT|30", na=False)]
        cols = [c for c in ["No Kamar", "Nama Lengkap", "Tgl Jatuh Tempo",
                             "Sisa Hari", "Flag Tagih", "Tarif Sewa"] if c in p.columns]
        st.dataframe((prioritas if not prioritas.empty else p)[cols],
                     use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data penghuni.")


# ============================ MARKETING ============================
elif menu == "Marketing":
    m = DASH.get("MARKETING", {})
    st.markdown('<h2 style="font-size:24px;font-weight:700;color:#0F172A;margin:0 0 2px;">Dashboard Marketing</h2>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#64748B;margin:0 0 20px;">Konten, kanal & efektivitas iklan</p>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Total Reach",
        f"{int(D.to_num(m.get('Total Reach', 0))):,}".replace(",", "."),
        f"Engagement {int(D.to_num(m.get('Total Engagement', 0)))}")
    kpi(c2, "Avg Engagement Rate", D.persen(m.get("Avg ER", 0)), "", "pos")
    kpi(c3, "Avg CPL", D.rupiah(m.get("Avg CPL", 0)),
        f"Spend {D.rupiah(m.get('Total Spend Ads', 0))}")
    kpi(c4, "Konversi Lead→Booking",
        D.persen(m.get("Conv Lead->Booking", 0)),
        f"Belum tayang: {m.get('Konten belum tayang', '-')}")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        chart_header("Reach per Platform", "Total jangkauan per kanal")
        k = D.konten()
        if not k.empty and "Platform" in k.columns and "Reach" in k.columns:
            k["Reach"] = k["Reach"].map(D.to_num)
            g = k.groupby("Platform")["Reach"].sum().sort_values(ascending=False)
            st.plotly_chart(bars(g.index.tolist(), g.values.tolist(), ac),
                            use_container_width=True)
        else:
            st.info("Belum ada data 4_KONTEN.")

    with g2:
        chart_header("ROI Kotor per Promosi", "Efektivitas campaign")
        pr = D.promosi()
        if not pr.empty and "Nama Promosi" in pr.columns and "ROI Kotor" in pr.columns:
            pr["ROI Kotor"] = pr["ROI Kotor"].map(D.to_num)
            st.plotly_chart(bars(pr["Nama Promosi"].tolist(),
                                 pr["ROI Kotor"].tolist(), ac),
                            use_container_width=True)
        else:
            st.info("Belum ada data 5_PROMOSI.")

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    chart_header("Kinerja Konten", "Performa per postingan")
    k = D.konten()
    if not k.empty:
        cols = [c for c in ["Tgl Post", "Platform", "Tipe Konten", "Status",
                             "Reach", "Engagement", "ER (%)"] if c in k.columns]
        st.dataframe(k[cols], use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data konten.")


# ============================ OPERASIONAL ============================
else:
    o = DASH.get("OPERASIONAL", {})
    st.markdown('<h2 style="font-size:24px;font-weight:700;color:#0F172A;margin:0 0 2px;">Dashboard Operasional</h2>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#64748B;margin:0 0 20px;">Teknisi, perawatan & SLA · Tim Lapangan</p>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Total Tiket", str(o.get("Total Tiket", "-")),
        f"Selesai: {o.get('Selesai', '-')}")
    kpi(c2, "Breach SLA",   str(o.get("Breach SLA", "-")),   "", "neg")
    kpi(c3, "MTTR (hari)",  str(o.get("MTTR (hari)", "-")),   "")
    kpi(c4, "Biaya Maintenance",
        D.rupiah(o.get("Biaya Maintenance", 0)),
        f"Rasio Prev:Korektif {o.get('Rasio Preventif:Korektif', '-')}")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    mt = D.maintenance()
    g1, g2 = st.columns(2)
    with g1:
        chart_header("Tiket per Jenis Perawatan", "Preventif vs Korektif")
        vc = D.value_counts(mt, "Jenis Perawatan")
        if not vc.empty:
            st.plotly_chart(bars(vc.index.tolist(), vc.values.tolist(), ac),
                            use_container_width=True)
        else:
            st.info("Belum ada data maintenance.")

    with g2:
        chart_header("Status Tiket", "Distribusi status penyelesaian")
        vc = D.value_counts(mt, "Status")
        if not vc.empty:
            st.plotly_chart(donut(vc.index.tolist(), vc.values.tolist(),
                                  ["#16A34A", "#F59E0B", "#DC2626"], f"{int(vc.sum())}"),
                            use_container_width=True)
        else:
            st.info("Belum ada data status tiket.")

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    chart_header("Daftar Tiket Maintenance", "Log semua tiket aktif & selesai")
    if not mt.empty:
        cols = [c for c in ["Tgl Lapor/Jadwal", "Lokasi/Item", "Deskripsi",
                             "Prioritas", "Pelaksana", "Biaya", "Status",
                             "SLA OK?", "Jenis Perawatan"] if c in mt.columns]
        st.dataframe(mt[cols], use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data tiket.")

st.divider()
st.caption("🔒 Akses terbatas — hanya pengguna terdaftar. Data live dari Google Sheets (cache 5 menit).")
