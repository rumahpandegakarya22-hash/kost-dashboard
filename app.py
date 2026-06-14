"""
app.py — Dashboard Rumah Pandega (Streamlit).
Semua nilai KPI dihitung langsung dari data mentah per sheet.
"""

from datetime import date, datetime

import plotly.graph_objects as go
import streamlit as st
import streamlit_authenticator as stauth

import data as D

# ── Konfig ──────────────────────────────────────────────────────────────────
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

# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.block-container{padding-top:1.5rem;padding-bottom:2rem;max-width:none;}
.stApp{background:#F1F5F9 !important;}
[data-testid="stMain"]{background:#F1F5F9 !important;}
section.main{background:#F1F5F9 !important;}

[data-testid="stForm"]{background:white;border-radius:16px;padding:8px 4px;}
[data-testid="stForm"] p,[data-testid="stForm"] h1,
[data-testid="stForm"] h2,[data-testid="stForm"] h3{color:#0F172A !important;font-weight:700;}
.stTextInput label,.stTextInput > div > label{color:#374151 !important;font-weight:500;font-size:13px;}
.stTextInput input{background:#F8FAFC !important;color:#0F172A !important;
    border:1px solid #E2E8F0 !important;border-radius:8px !important;}
.stTextInput input:focus{border-color:#4F46E5 !important;box-shadow:none !important;}
[data-testid="stFormSubmitButton"] button{background:#4F46E5 !important;color:white !important;
    border:none !important;border-radius:8px !important;font-weight:600 !important;}
[data-testid="stFormSubmitButton"] button:hover{background:#4338CA !important;}

[data-testid="stSidebar"]{background:#0F172A;}
[data-testid="stSidebar"] *{color:#E2E8F0;}
[data-testid="stSidebar"] .stRadio > label{display:none;}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label{
    padding:10px 12px !important;border-radius:10px !important;
    font-size:13px !important;color:#94A3B8 !important;
    font-weight:500 !important;display:block;cursor:pointer;}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked){
    background:#1E293B !important;color:#FFFFFF !important;
    border-left:3px solid #4F46E5 !important;font-weight:600 !important;}
[data-testid="stSidebar"] .stSelectbox > div > div{
    background:#1E293B !important;color:#E2E8F0 !important;
    border-color:#334155 !important;font-size:12px !important;}

.kpi{background:#FFFFFF;border:1px solid #E8EDF3;border-radius:16px;
     padding:16px 20px 12px;margin-bottom:4px;}
.kpi .lab{font-size:12px;color:#64748B;font-weight:500;margin-bottom:4px;}
.kpi .val{font-size:22px;color:#0F172A;font-weight:700;margin:0 0 4px;}
.kpi .sub{font-size:11px;color:#64748B;}
.kpi .sub.pos{color:#16A34A;font-weight:600;}
.kpi .sub.neg{color:#DC2626;font-weight:600;}
.kpi .sub.warn{color:#D97706;font-weight:600;}

.cht-hdr{background:white;border:1px solid #E8EDF3;border-radius:16px 16px 0 0;
         border-bottom:none;padding:16px 20px 12px;margin:0;}
.cht-hdr .cht-t{font-size:15px;font-weight:600;color:#0F172A;margin:0 0 2px;}
.cht-hdr .cht-s{font-size:11px;color:#94A3B8;margin:0;}

[data-testid="stPlotlyChart"]{
    background:white !important;
    border-left:1px solid #E8EDF3 !important;
    border-right:1px solid #E8EDF3 !important;
    border-bottom:1px solid #E8EDF3 !important;
    border-radius:0 0 16px 16px !important;
    padding:0 8px 8px !important;
    margin-bottom:16px !important;}

[data-testid="stDataFrame"]{
    background:white !important;border:1px solid #E8EDF3 !important;
    border-radius:0 0 16px 16px !important;
    margin-bottom:16px !important;overflow:hidden;}

.period-badge{
    display:inline-block;background:#F1F5F9;color:#475569;
    padding:2px 10px;border-radius:99px;font-size:11px;
    border:1px solid #E2E8F0;margin-left:8px;vertical-align:middle;}
</style>
""", unsafe_allow_html=True)


# ── Auth ─────────────────────────────────────────────────────────────────────
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
name        = st.session_state.get("name") or ""
auth_status = st.session_state.get("authentication_status")

if auth_status is False:
    st.error("Username / password salah.")
    st.stop()
if auth_status is None:
    st.info("Silakan login untuk melihat dashboard.")
    st.stop()


# ── UI Helpers ───────────────────────────────────────────────────────────────
_CFG = {"displayModeBar": False, "responsive": True}


def _months_ago_start(n: int) -> date:
    today = date.today()
    m, y = today.month - n, today.year
    while m <= 0:
        m += 12
        y -= 1
    return date(y, m, 1)


def _svg_spark(vals: list, color: str, h: int = 36) -> str:
    """SVG sparkline halus dengan aproksimasi Catmull-Rom Bézier."""
    if not vals or len(vals) < 2:
        return ""
    n, w = len(vals), 120
    mn, mx = min(vals), max(vals)
    rng = mx - mn or 1
    xs = [i * w / (n - 1) for i in range(n)]
    ys = [h - 2 - (v - mn) / rng * (h - 6) for v in vals]
    if n == 2:
        path = f"M{xs[0]:.1f},{ys[0]:.1f} L{xs[1]:.1f},{ys[1]:.1f}"
    else:
        parts = [f"M{xs[0]:.1f},{ys[0]:.1f}"]
        for i in range(1, n):
            x0, y0 = xs[max(0, i-2)], ys[max(0, i-2)]
            x1, y1 = xs[i-1], ys[i-1]
            x2, y2 = xs[i], ys[i]
            x3, y3 = xs[min(n-1, i+1)], ys[min(n-1, i+1)]
            cp1x = x1 + (x2-x0)/6; cp1y = y1 + (y2-y0)/6
            cp2x = x2 - (x3-x1)/6; cp2y = y2 - (y3-y1)/6
            parts.append(f"C{cp1x:.1f},{cp1y:.1f} {cp2x:.1f},{cp2y:.1f} {x2:.1f},{y2:.1f}")
        path = " ".join(parts)
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    fill = path + f" L{xs[-1]:.1f},{h} L{xs[0]:.1f},{h} Z"
    return (
        f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
        f'style="width:100%;height:{h}px;display:block;margin-top:8px;">'
        f'<path d="{fill}" fill="rgba({r},{g},{b},0.12)" stroke="none"/>'
        f'<path d="{path}" fill="none" stroke="{color}" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
        f'</svg>'
    )


def kpi(col, label, value, sub="", sub_type="", spark_y=None, spark_color=None):
    sub_class  = f"sub {sub_type}".strip()
    spark_html = _svg_spark(spark_y, spark_color or "#4F46E5") \
                 if spark_y and len(spark_y) >= 2 else ""
    col.markdown(
        f'<div class="kpi">'
        f'<div class="lab">{label}</div>'
        f'<div class="val">{value}</div>'
        f'<div class="{sub_class}">{sub}</div>'
        f'{spark_html}</div>',
        unsafe_allow_html=True)


def chart_header(title, subtitle=""):
    st.markdown(
        f'<div class="cht-hdr"><p class="cht-t">{title}</p>'
        f'<p class="cht-s">{subtitle}</p></div>',
        unsafe_allow_html=True)


def _layout(height=260, margin=None, ysfx=""):
    m = margin or dict(t=24, b=30, l=10, r=10)
    return dict(
        height=height, margin=m,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color='#374151')),
        yaxis=dict(showgrid=True, gridcolor='#E2E8F0',
                   tickfont=dict(size=10, color='#374151'), ticksuffix=ysfx),
        legend=dict(font=dict(size=11, color='#374151'), bgcolor='rgba(0,0,0,0)'),
        font=dict(color='#374151'),
    )


def donut(labels, values, colors, center=""):
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=.62,
        marker=dict(colors=colors), sort=False,
        textinfo='percent',
        textfont=dict(size=11, color='white'),
        insidetextorientation='horizontal'))
    fig.update_layout(
        height=260, margin=dict(t=10, b=10, l=10, r=100),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        annotations=[dict(text=center, showarrow=False,
                          font_size=16, font_color='#0F172A')],
        showlegend=True,
        legend=dict(orientation='v', x=1.02, y=0.5, xanchor='left',
                    font=dict(size=11, color='#374151'), bgcolor='rgba(0,0,0,0)'))
    return fig


def bar_chart(x, y, colors, horizontal=False, height=260, ysfx=""):
    if isinstance(colors, str):
        colors = [colors] * len(x)
    mx = max((abs(v) for v in y), default=0)
    texts = ([f"{v/1e6:.1f}Jt" for v in y] if mx >= 1_000_000
             else [f"{int(v):,}".replace(",", ".") for v in y])
    if horizontal:
        fig = go.Figure(go.Bar(x=y, y=x, orientation="h",
                               marker_color=colors, marker_line_width=0,
                               text=texts, textposition='outside',
                               textfont=dict(size=10, color='#374151')))
    else:
        fig = go.Figure(go.Bar(x=x, y=y,
                               marker_color=colors, marker_line_width=0,
                               text=texts, textposition='outside',
                               textfont=dict(size=10, color='#374151')))
    fig.update_layout(**_layout(height=height, ysfx=ysfx))
    return fig


def _color_list(labels, cmap, default="#64748B"):
    return [cmap.get(str(l), default) for l in labels]


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    initials = "".join(w[0] for w in name.split()[:2]).upper() if name else "?"
    now = datetime.now()

    st.markdown(f"""
<div style="padding:8px 4px 16px;">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="background:#4F46E5;width:32px;height:32px;border-radius:9px;
                flex-shrink:0;display:flex;align-items:center;justify-content:center;
                font-weight:700;font-size:14px;color:white;">K</div>
    <div>
      <div style="font-weight:700;font-size:17px;color:white;line-height:1.2;">KostPro</div>
      <div style="font-size:10px;color:#64748B;">{now.day} {now.strftime('%b %Y')}</div>
    </div>
  </div>
</div>
<p style="font-size:10px;font-weight:600;color:#475569;letter-spacing:.08em;margin:0 0 4px 4px;">PERIODE</p>
""", unsafe_allow_html=True)

    period = st.selectbox(
        "Periode",
        ["Bulan Ini", "3 Bulan Terakhir", "6 Bulan Terakhir",
         "Tahun Ini", "Semua Data", "Pilih Rentang"],
        index=2, label_visibility="collapsed")

    today = date.today()
    if period == "Bulan Ini":
        d_from: date | None = today.replace(day=1)
        d_to:   date | None = today
    elif period == "3 Bulan Terakhir":
        d_from, d_to = _months_ago_start(3), today
    elif period == "6 Bulan Terakhir":
        d_from, d_to = _months_ago_start(6), today
    elif period == "Tahun Ini":
        d_from, d_to = today.replace(month=1, day=1), today
    elif period == "Semua Data":
        d_from, d_to = None, None
    else:
        d_from = st.date_input("Dari", value=today.replace(day=1), key="df_in")
        d_to   = st.date_input("Hingga", value=today, key="dt_in")

    pbadge = (f"📅 {d_from.strftime('%d %b %Y')} – {d_to.strftime('%d %b %Y')}"
              if d_from and d_to else "📅 Semua Periode")

    st.markdown('<p style="font-size:10px;font-weight:600;color:#475569;letter-spacing:.08em;'
                'margin:12px 0 4px 4px;">MENU</p>', unsafe_allow_html=True)
    menu = st.radio("", list(ACCENT.keys()), label_visibility="collapsed")
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

ac = ACCENT[menu]


# ════════════════════════════ EXECUTIVE ════════════════════════════════════════
if menu == "Executive":
    st.markdown('<h2 style="font-size:24px;font-weight:700;color:#0F172A;margin:0 0 2px;">Ringkasan Eksekutif</h2>',
                unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:13px;color:#64748B;margin:0 0 20px;">'
                f'Kinerja portofolio kost · BOD / Owner '
                f'<span class="period-badge">{pbadge}</span></p>', unsafe_allow_html=True)

    p      = D.penghuni()
    keu_df = D.filter_date(D.read_tab("3_KEUANGAN", "Tanggal"), "Tanggal", d_from, d_to)
    kt     = D.keuangan_trend(keu_df)
    e      = D.kpi_executive(keu_df, p)

    # Sparklines dari tren bulanan
    rev_spark    = kt["Pendapatan Usaha"].tolist() if not kt.empty else []
    laba_spark   = kt["Laba"].tolist()             if not kt.empty else []
    revpar_spark = kt["RevPAR"].tolist()            if not kt.empty else []
    laba_color   = "#16A34A" if e["laba"] >= 0 else "#DC2626"

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Pendapatan Periode",
        D.rupiah(e["pendapatan"], juta=True),
        f"Beban {D.rupiah(e['beban'], juta=True)}",
        spark_y=rev_spark, spark_color=ac)
    kpi(c2, "Tingkat Hunian",
        D.persen(e["occ_komitmen"]),
        f"Fisik {D.persen(e['occ_fisik'])}", "pos")
    kpi(c3, "Laba / Margin Usaha",
        D.rupiah(e["laba"], juta=True),
        f"Margin {D.persen(e['margin'])}",
        "pos" if e["laba"] >= 0 else "neg",
        spark_y=laba_spark, spark_color=laba_color)
    kpi(c4, "RevPAR",
        D.rupiah(e["revpar"]),
        f"Penghuni aktif: {e['penghuni_aktif']}",
        spark_y=revpar_spark, spark_color=ac)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    g1, g2 = st.columns([2, 1])
    with g1:
        chart_header("Tren Pendapatan vs Biaya Operasional",
                     f"Bulanan · Rp Juta · {pbadge}")
        if kt.empty:
            st.info("Belum ada data keuangan pada periode ini.")
        else:
            kt2 = kt.copy()
            kt2["Pendapatan Usaha"] /= 1_000_000
            kt2["Beban Usaha"]      /= 1_000_000
            fig = go.Figure()
            fig.add_scatter(x=kt2["Bulan"], y=kt2["Pendapatan Usaha"], name="Pendapatan",
                            line=dict(color=ac, width=2.5, shape='spline'),
                            fill='tozeroy', fillcolor='rgba(79,70,229,0.08)', mode='lines')
            fig.add_scatter(x=kt2["Bulan"], y=kt2["Beban Usaha"], name="Beban",
                            line=dict(color="#DC2626", width=2, shape='spline'), mode='lines')
            lay = _layout(height=240, ysfx=" Jt")
            lay["legend"] = dict(orientation='h', y=1.15, x=0,
                                 font=dict(size=11, color='#374151'), bgcolor='rgba(0,0,0,0)')
            fig.update_layout(**lay)
            st.plotly_chart(fig, use_container_width=True, config=_CFG)

    with g2:
        chart_header("Status Penghuni", "Komposisi saat ini")
        vc = D.value_counts(p, "Status")
        if vc.empty:
            st.info("Belum ada data penghuni.")
        else:
            SCOL = {"Aktif": "#16A34A", "Booking (DP)": "#F59E0B", "Non Aktif": "#94A3B8"}
            st.plotly_chart(donut(vc.index.tolist(), vc.values.tolist(),
                                  _color_list(vc.index, SCOL), f"{int(vc.sum())} org"),
                            use_container_width=True, config=_CFG)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    g3, g4 = st.columns(2)
    with g3:
        chart_header("Hunian per Jenis Kamar", "Jumlah kamar terisi saat ini")
        if not p.empty and "Jenis Kamar" in p.columns:
            terisi = (p[p["Status Okupansi"].astype(str).str.contains("Terisi", na=False)]
                      if "Status Okupansi" in p.columns else p)
            vc = D.value_counts(terisi, "Jenis Kamar")
            if not vc.empty:
                KCOL = {"Eco": "#4F46E5", "Classic": "#059669", "Comfy": "#F59E0B"}
                st.plotly_chart(bar_chart(vc.index.tolist(), vc.values.tolist(),
                                          _color_list(vc.index, KCOL, "#94A3B8")),
                                use_container_width=True, config=_CFG)
            else:
                st.info("Belum ada kamar terisi.")
        else:
            st.info("Data jenis kamar tidak tersedia.")

    with g4:
        chart_header("Segmen Usia Penghuni", "Distribusi kelompok usia")
        if not p.empty and "Segmen Usia" in p.columns:
            vc_u = D.value_counts(p, "Segmen Usia").sort_index()
            if not vc_u.empty:
                st.plotly_chart(bar_chart(vc_u.index.tolist(), vc_u.values.tolist(), "#7C3AED"),
                                use_container_width=True, config=_CFG)
            else:
                st.info("Belum ada data segmen usia.")
        else:
            st.info("Data segmen usia tidak tersedia.")

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    chart_header("Daftar Penghuni", "Data lengkap & status tagihan")
    if not p.empty:
        cols = [c for c in ["No Kamar", "Nama Lengkap", "Panggilan", "Jenis Kamar",
                             "Status", "Tgl Jatuh Tempo", "Sisa Hari",
                             "Flag Tagih", "Tarif Sewa"] if c in p.columns]
        st.dataframe(p[cols], use_container_width=True, hide_index=True,
                     column_config={
                         "Tarif Sewa": st.column_config.NumberColumn("Tarif Sewa (Rp)", format="Rp %d"),
                         "Sisa Hari":  st.column_config.NumberColumn("Sisa Hari", format="%d hr"),
                     })
    else:
        st.info("Belum ada data penghuni.")


# ════════════════════════════ SALES ═══════════════════════════════════════════
elif menu == "Sales":
    st.markdown('<h2 style="font-size:24px;font-weight:700;color:#0F172A;margin:0 0 2px;">Dashboard Sales</h2>',
                unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:13px;color:#64748B;margin:0 0 20px;">'
                f'Akuisisi penyewa & pipeline '
                f'<span class="period-badge">{pbadge}</span></p>', unsafe_allow_html=True)

    # Raw data (filtered per periode)
    lead_raw = D.read_tab("6_LEADS", "Nama Leads")
    sv_raw   = D.read_tab("7_SURVEY", "Nama Calon")
    bk_raw   = D.read_tab("8_BOOKING", "No Booking")

    # Cari kolom tanggal di survey (defensif)
    sv_date_col = next((c for c in ["Tgl Survey", "Tanggal", "Tgl"]
                        if not sv_raw.empty and c in sv_raw.columns), None)

    lead_df = D.filter_date(lead_raw, "Tanggal",     d_from, d_to)
    sv_df   = D.filter_date(sv_raw,   sv_date_col,   d_from, d_to) if sv_date_col else sv_raw
    bk_df   = D.filter_date(bk_raw,   "Tgl Booking", d_from, d_to)

    s = D.kpi_sales(lead_df, sv_df, bk_df)

    # Sparkline leads bulanan
    lead_mc    = D.monthly_count(lead_df, "Tanggal", "Leads")
    lead_spark = lead_mc["Leads"].tolist() if not lead_mc.empty else []

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Total Leads", str(s["total_leads"]),
        f"Belum di-FU: {s['belum_fu']}", "warn",
        spark_y=lead_spark, spark_color=ac)
    kpi(c2, "Konversi Lead→Survey",
        D.persen(s["conv_lead_survey"]), "", "pos")
    kpi(c3, "Konversi Survey→Deal",
        D.persen(s["conv_survey_deal"]), "", "pos")
    kpi(c4, "Nilai Kontrak Deal",
        D.rupiah(s["nilai_deal"], juta=True),
        f"Cancel rate {D.persen(s['cancel_rate'])}",
        "neg" if s["cancel_rate"] > 0 else "pos")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        chart_header("Funnel Penjualan", f"Lead → Survey → Booking → Deal · {pbadge}")
        # Gunakan data terfilter untuk funnel
        n_leads   = len(lead_df)
        n_survey  = len(sv_df)
        n_booking = s["total_leads"] - s.get("belum_fu", 0)  # fallback
        # Hitung ulang dari bk_df langsung
        n_bk = 0
        n_deal = 0
        if not bk_df.empty and "Status" in bk_df.columns:
            st_c = bk_df["Status"].astype(str).str.strip()
            n_bk   = int((~st_c.str.contains("Batal", case=False, na=False)).sum())
            n_deal = int(st_c.str.contains("Check-in|Konfirmasi", case=False, na=False).sum())
        fn = [("Leads", n_leads), ("Survey", n_survey), ("Booking", n_bk), ("Deal", n_deal)]
        fig = go.Figure(go.Funnel(
            y=[a for a, _ in fn], x=[b for _, b in fn],
            textinfo="value+percent initial",
            textfont=dict(size=12, color='#374151'),
            marker=dict(color=["#4F46E5", "#059669", "#F59E0B", "#16A34A"]),
            connector=dict(line=dict(color="#E2E8F0", width=2))
        ))
        fig.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10),
                          paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#374151'))
        st.plotly_chart(fig, use_container_width=True, config=_CFG)

    with g2:
        chart_header("Sumber Leads", f"Distribusi per channel · {pbadge}")
        vc = D.value_counts(lead_df if not lead_df.empty else lead_raw, "Sumber Leads")
        if vc.empty:
            st.info("Belum ada data leads.")
        else:
            st.plotly_chart(donut(vc.index.tolist(), vc.values.tolist(),
                                  ["#059669", "#34D399", "#3B82F6", "#F59E0B", "#94A3B8"],
                                  f"{int(vc.sum())}"),
                            use_container_width=True, config=_CFG)

    if not lead_mc.empty and len(lead_mc) >= 2:
        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
        chart_header("Tren Leads Bulanan", f"Jumlah leads per bulan · {pbadge}")
        fig = go.Figure(go.Bar(
            x=lead_mc["Bulan"], y=lead_mc["Leads"],
            marker_color=ac, marker_line_width=0,
            text=lead_mc["Leads"].tolist(), textposition='outside',
            textfont=dict(size=10, color='#374151')))
        fig.update_layout(**_layout(height=200))
        st.plotly_chart(fig, use_container_width=True, config=_CFG)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    chart_header("Pipeline Booking", f"Status transaksi · {pbadge}")
    disp_bk = bk_df if not bk_df.empty else bk_raw
    if not disp_bk.empty:
        cols = [c for c in ["No Booking", "Nama Penyewa", "Kamar", "Tgl Masuk",
                             "Durasi (Bln)", "Nilai Kontrak", "Per Bulan",
                             "Sumber", "Status"] if c in disp_bk.columns]
        st.dataframe(disp_bk[cols], use_container_width=True, hide_index=True,
                     column_config={
                         "Per Bulan": st.column_config.NumberColumn("Per Bulan (Rp)", format="Rp %d"),
                     })
    else:
        st.info("Belum ada data booking.")


# ════════════════════════════ ADMIN ═══════════════════════════════════════════
elif menu == "Admin":
    st.markdown('<h2 style="font-size:24px;font-weight:700;color:#0F172A;margin:0 0 2px;">Dashboard Admin & Keuangan</h2>',
                unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:13px;color:#64748B;margin:0 0 20px;">'
                f'Penagihan, kontrak & hunian '
                f'<span class="period-badge">{pbadge}</span></p>', unsafe_allow_html=True)

    p        = D.penghuni()
    a        = D.kpi_admin(p)
    keu_df   = D.filter_date(D.read_tab("3_KEUANGAN", "Tanggal"), "Tanggal", d_from, d_to)
    kt_admin = D.keuangan_trend(keu_df)

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Jatuh Tempo ≤7 Hari",      str(a["jatuh_tempo_7"]),
        "Perlu ditagih segera", "neg")
    kpi(c2, "Tunggakan / Overdue",       str(a["overdue"]),
        "Melewati jatuh tempo", "neg")
    kpi(c3, "Kamar Kosong",              str(a["kosong"]),
        "Siap disewa")
    kpi(c4, "Kontrak Berakhir ≤30 Hari", str(a["kontrak_30"]),
        "Perlu diperpanjang", "warn")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        chart_header("Status Tagihan", "Distribusi flag penagihan")
        vc = D.value_counts(p, "Flag Tagih")
        if not vc.empty:
            FCOL = {"Aman": "#16A34A", "<30 hari": "#F59E0B",
                    "SEGERA": "#D97706", "LEWAT": "#DC2626"}
            st.plotly_chart(bar_chart(vc.index.tolist(), vc.values.tolist(),
                                      _color_list(vc.index, FCOL, "#94A3B8")),
                            use_container_width=True, config=_CFG)
        else:
            st.info("Belum ada data tagihan.")

    with g2:
        chart_header("Status Hunian", "Terisi vs Kosong")
        vc = D.value_counts(p, "Status Okupansi")
        if not vc.empty:
            OCOL = {"Terisi": "#16A34A", "Kosong": "#94A3B8"}
            st.plotly_chart(donut(vc.index.tolist(), vc.values.tolist(),
                                  _color_list(vc.index, OCOL), f"{int(vc.sum())}"),
                            use_container_width=True, config=_CFG)
        else:
            st.info("Belum ada data hunian.")

    if not kt_admin.empty and len(kt_admin) >= 2:
        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
        chart_header("Tren Pendapatan Bulanan", f"Rp Juta · {pbadge}")
        kt2 = kt_admin.copy()
        kt2["Pendapatan Usaha"] /= 1_000_000
        kt2["Beban Usaha"]      /= 1_000_000
        fig = go.Figure()
        fig.add_scatter(x=kt2["Bulan"], y=kt2["Pendapatan Usaha"], name="Pendapatan",
                        line=dict(color=ac, width=2.5, shape='spline'),
                        fill='tozeroy', fillcolor='rgba(37,99,235,0.08)')
        fig.add_scatter(x=kt2["Bulan"], y=kt2["Beban Usaha"], name="Beban",
                        line=dict(color="#DC2626", width=2, shape='spline'))
        lay = _layout(height=220, ysfx=" Jt")
        lay["legend"] = dict(orientation='h', y=1.15, x=0,
                             font=dict(size=11, color='#374151'), bgcolor='rgba(0,0,0,0)')
        fig.update_layout(**lay)
        st.plotly_chart(fig, use_container_width=True, config=_CFG)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    chart_header("Prioritas Penagihan", "Penghuni mendekati / melewati jatuh tempo")
    if not p.empty and "Flag Tagih" in p.columns:
        prioritas = p[p["Flag Tagih"].astype(str).str.contains("SEGERA|LEWAT|<30", na=False)]
        cols = [c for c in ["No Kamar", "Nama Lengkap", "Panggilan", "Tgl Jatuh Tempo",
                             "Sisa Hari", "Flag Tagih", "Tarif Sewa",
                             "Kontak Darurat"] if c in p.columns]
        st.dataframe((prioritas if not prioritas.empty else p)[cols],
                     use_container_width=True, hide_index=True,
                     column_config={
                         "Tarif Sewa": st.column_config.NumberColumn("Tarif Sewa (Rp)", format="Rp %d"),
                         "Sisa Hari":  st.column_config.NumberColumn("Sisa Hari", format="%d hr"),
                     })
    else:
        st.info("Belum ada data penghuni.")


# ════════════════════════════ MARKETING ═══════════════════════════════════════
elif menu == "Marketing":
    st.markdown('<h2 style="font-size:24px;font-weight:700;color:#0F172A;margin:0 0 2px;">Dashboard Marketing</h2>',
                unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:13px;color:#64748B;margin:0 0 20px;">'
                f'Konten, kanal & efektivitas iklan '
                f'<span class="period-badge">{pbadge}</span></p>', unsafe_allow_html=True)

    kon_full = D.konten()
    pr_full  = D.promosi()
    lead_raw = D.read_tab("6_LEADS", "Nama Leads")
    bk_raw   = D.read_tab("8_BOOKING", "No Booking")

    kon_df  = D.filter_date(kon_full,  "Tgl Post",    d_from, d_to)
    lead_df = D.filter_date(lead_raw,  "Tanggal",     d_from, d_to)
    bk_df   = D.filter_date(bk_raw,   "Tgl Booking", d_from, d_to)

    m = D.kpi_marketing(kon_df, pr_full, lead_df, bk_df)

    reach_ms   = D.monthly_sum(kon_df if not kon_df.empty else kon_full,
                               "Tgl Post", "Reach", "Reach")
    reach_spark = reach_ms["Reach"].tolist() if not reach_ms.empty else []

    reach_str = f"{m['total_reach']:,}".replace(",", ".")
    eng_str   = f"{m['total_engagement']:,}".replace(",", ".")

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Total Reach", reach_str, f"Engagement {eng_str}",
        spark_y=reach_spark, spark_color=ac)
    kpi(c2, "Avg Engagement Rate", D.persen(m["avg_er"]), "", "pos")
    kpi(c3, "Avg CPL",
        D.rupiah(m["avg_cpl"]),
        f"Total spend {D.rupiah(m['total_spend'], juta=True)}")
    kpi(c4, "Konversi Lead→Booking",
        D.persen(m["conv_lead_booking"]),
        f"Konten belum tayang: {m['belum_tayang']}", "warn")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        chart_header("Reach per Platform", f"Total jangkauan · {pbadge}")
        k = kon_df if not kon_df.empty else kon_full
        if not k.empty and "Platform" in k.columns and "Reach" in k.columns:
            k = k.copy()
            k["Reach"] = k["Reach"].map(D.to_num)
            g = k.groupby("Platform")["Reach"].sum().sort_values(ascending=False)
            st.plotly_chart(bar_chart(g.index.tolist(), g.values.tolist(), ac),
                            use_container_width=True, config=_CFG)
        else:
            st.info("Belum ada data konten.")

    with g2:
        chart_header("ROI Kotor per Promosi", "Hijau = ROI ≥ target")
        if not pr_full.empty and "Nama Promosi" in pr_full.columns and "ROI Kotor" in pr_full.columns:
            pr = pr_full.copy()
            pr["ROI Kotor"] = pr["ROI Kotor"].map(D.to_num)
            param  = D.get_parameter()
            target = D.to_num(param.get("Target ROI campaign (%)", 1)) or 1
            roi_c  = ["#16A34A" if v >= target else "#DC2626" for v in pr["ROI Kotor"]]
            fig = go.Figure(go.Bar(
                x=pr["Nama Promosi"].tolist(), y=pr["ROI Kotor"].tolist(),
                marker_color=roi_c, marker_line_width=0,
                text=[f"{v:.1f}x" for v in pr["ROI Kotor"]], textposition='outside',
                textfont=dict(size=10, color='#374151')))
            fig.update_layout(**_layout())
            st.plotly_chart(fig, use_container_width=True, config=_CFG)
        else:
            st.info("Belum ada data promosi.")

    if not reach_ms.empty and len(reach_ms) >= 2:
        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
        chart_header("Tren Reach Bulanan", f"Total jangkauan per bulan · {pbadge}")
        fig = go.Figure(go.Bar(
            x=reach_ms["Bulan"], y=reach_ms["Reach"],
            marker_color=ac, marker_line_width=0,
            text=[f"{int(v):,}".replace(",", ".") for v in reach_ms["Reach"]],
            textposition='outside', textfont=dict(size=10, color='#374151')))
        fig.update_layout(**_layout(height=200))
        st.plotly_chart(fig, use_container_width=True, config=_CFG)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    chart_header("Kinerja Konten", f"Performa per postingan · {pbadge}")
    disp_k = kon_df if not kon_df.empty else kon_full
    if not disp_k.empty:
        cols = [c for c in ["Tgl Post", "Platform", "Tipe Konten", "Judul/Caption",
                             "Status", "Reach", "Likes", "Komentar",
                             "Engagement", "ER (%)"] if c in disp_k.columns]
        st.dataframe(disp_k[cols], use_container_width=True, hide_index=True,
                     column_config={"ER (%)": st.column_config.NumberColumn("ER (%)", format="%.4f")})
    else:
        st.info("Belum ada data konten.")


# ════════════════════════════ OPERASIONAL ═════════════════════════════════════
else:
    st.markdown('<h2 style="font-size:24px;font-weight:700;color:#0F172A;margin:0 0 2px;">Dashboard Operasional</h2>',
                unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:13px;color:#64748B;margin:0 0 20px;">'
                f'Teknisi, perawatan & SLA · Tim Lapangan '
                f'<span class="period-badge">{pbadge}</span></p>', unsafe_allow_html=True)

    mt_full  = D.maintenance()
    mt_df    = D.filter_date(mt_full, "Tgl Lapor/Jadwal", d_from, d_to)
    mt_use   = mt_df if not mt_df.empty else mt_full
    o        = D.kpi_operasional(mt_use)

    tk_mc        = D.monthly_count(mt_use, "Tgl Lapor/Jadwal", "Tiket")
    biaya_ms     = D.monthly_sum(mt_use, "Tgl Lapor/Jadwal", "Biaya", "Biaya")
    ticket_spark = tk_mc["Tiket"].tolist()   if not tk_mc.empty    else []
    biaya_spark  = biaya_ms["Biaya"].tolist() if not biaya_ms.empty else []

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Total Tiket",
        str(o["total_tiket"]),
        f"Selesai: {o['selesai']}",
        spark_y=ticket_spark, spark_color=ac)
    kpi(c2, "Breach SLA",
        str(o["breach_sla"]),
        "Ada pelanggaran SLA!" if o["breach_sla"] > 0 else "Semua dalam SLA",
        "neg" if o["breach_sla"] > 0 else "pos")
    kpi(c3, "MTTR",
        f"{o['mttr']} hari", "Mean Time to Resolve")
    kpi(c4, "Biaya Maintenance",
        D.rupiah(o["biaya"]),
        f"Prev:Korektif = {o['rasio']}",
        spark_y=biaya_spark, spark_color=ac)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        chart_header("Jenis Perawatan", f"Preventif vs Korektif · {pbadge}")
        vc = D.value_counts(mt_use, "Jenis Perawatan")
        if not vc.empty:
            MCOL = {"Preventif": "#4F46E5", "Korektif": "#EA580C"}
            st.plotly_chart(bar_chart(vc.index.tolist(), vc.values.tolist(),
                                      _color_list(vc.index, MCOL)),
                            use_container_width=True, config=_CFG)
        else:
            st.info("Belum ada data maintenance.")

    with g2:
        chart_header("Status Tiket", f"Distribusi penyelesaian · {pbadge}")
        vc = D.value_counts(mt_use, "Status")
        if not vc.empty:
            STCOL = {"Selesai": "#16A34A", "Proses": "#F59E0B",
                     "Pending": "#94A3B8", "Batal": "#DC2626"}
            st.plotly_chart(donut(vc.index.tolist(), vc.values.tolist(),
                                  _color_list(vc.index, STCOL), f"{int(vc.sum())}"),
                            use_container_width=True, config=_CFG)
        else:
            st.info("Belum ada data tiket.")

    if not tk_mc.empty and len(tk_mc) >= 2:
        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
        chart_header("Tren Tiket Bulanan", f"Jumlah tiket per bulan · {pbadge}")
        fig = go.Figure(go.Bar(
            x=tk_mc["Bulan"], y=tk_mc["Tiket"],
            marker_color=ac, marker_line_width=0,
            text=tk_mc["Tiket"].tolist(), textposition='outside',
            textfont=dict(size=10, color='#374151')))
        fig.update_layout(**_layout(height=200))
        st.plotly_chart(fig, use_container_width=True, config=_CFG)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    chart_header("Log Tiket Maintenance", f"Semua tiket · {pbadge}")
    if not mt_use.empty:
        cols = [c for c in ["Tgl Lapor/Jadwal", "Tgl Selesai", "Lokasi/Item",
                             "Deskripsi", "Prioritas", "Pelaksana", "Vendor",
                             "Biaya", "Status", "SLA OK?",
                             "Jenis Perawatan"] if c in mt_use.columns]
        st.dataframe(mt_use[cols], use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data tiket.")

st.divider()
st.caption("🔒 Akses terbatas · Data live dari Google Sheets · Cache 5 menit")
