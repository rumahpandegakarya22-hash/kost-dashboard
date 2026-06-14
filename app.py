"""
app.py — Dashboard Rumah Pandega (Streamlit).
"""

from datetime import datetime

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
/* Layout */
.block-container{padding-top:1.5rem;padding-bottom:2rem;max-width:none;}
.stApp{background:#F1F5F9 !important;}
[data-testid="stMain"]{background:#F1F5F9 !important;}
section.main{background:#F1F5F9 !important;}

/* Login */
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

/* Sidebar */
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

/* KPI Card */
.kpi{background:#FFFFFF;border:1px solid #E8EDF3;border-radius:16px;
     padding:16px 20px;margin-bottom:4px;min-height:108px;}
.kpi .lab{font-size:12px;color:#64748B;font-weight:500;margin-bottom:4px;}
.kpi .val{font-size:22px;color:#0F172A;font-weight:700;margin:0 0 6px;}
.kpi .sub{font-size:11px;color:#64748B;}
.kpi .sub.pos{color:#16A34A;font-weight:600;}
.kpi .sub.neg{color:#DC2626;font-weight:600;}
.kpi .sub.warn{color:#D97706;font-weight:600;}

/* Chart card — top */
.cht-hdr{background:white;border:1px solid #E8EDF3;border-radius:16px 16px 0 0;
         border-bottom:none;padding:16px 20px 12px;margin:0;}
.cht-hdr .cht-t{font-size:15px;font-weight:600;color:#0F172A;margin:0 0 2px;}
.cht-hdr .cht-s{font-size:11px;color:#94A3B8;margin:0;}

/* Chart card — bottom (plotly renders here) */
[data-testid="stPlotlyChart"]{
    background:white !important;
    border-left:1px solid #E8EDF3 !important;
    border-right:1px solid #E8EDF3 !important;
    border-bottom:1px solid #E8EDF3 !important;
    border-radius:0 0 16px 16px !important;
    padding:0 8px 8px !important;
    margin-bottom:16px !important;}

/* Dataframe card */
[data-testid="stDataFrame"]{
    background:white !important;border:1px solid #E8EDF3 !important;
    border-radius:0 0 16px 16px !important;
    margin-bottom:16px !important;overflow:hidden;}
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
username    = st.session_state.get("username") or ""

if auth_status is False:
    st.error("Username / password salah.")
    st.stop()
if auth_status is None:
    st.info("Silakan login untuk melihat dashboard.")
    st.stop()


# ── Helpers UI ───────────────────────────────────────────────────────────────
_CFG = {"displayModeBar": False, "responsive": True}


def kpi(col, label, value, sub="", sub_type=""):
    sub_class = f"sub {sub_type}".strip()
    col.markdown(
        f'<div class="kpi"><div class="lab">{label}</div>'
        f'<div class="val">{value}</div>'
        f'<div class="{sub_class}">{sub}</div></div>',
        unsafe_allow_html=True)


def chart_header(title, subtitle=""):
    st.markdown(
        f'<div class="cht-hdr"><p class="cht-t">{title}</p>'
        f'<p class="cht-s">{subtitle}</p></div>',
        unsafe_allow_html=True)


def _layout(height=260, margin=None, ysfx=""):
    m = margin or dict(t=10, b=30, l=10, r=10)
    return dict(
        height=height, margin=m,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickfont=dict(size=9, color='#94A3B8')),
        yaxis=dict(showgrid=True, gridcolor='#F1F5F9',
                   tickfont=dict(size=9, color='#94A3B8'),
                   ticksuffix=ysfx),
    )


def donut(labels, values, colors, center=""):
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=.62,
                           marker=dict(colors=colors), sort=False))
    fig.update_layout(
        height=260, margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        annotations=[dict(text=center, showarrow=False, font_size=16)],
        legend=dict(orientation='v', x=1.05, y=0.5, font=dict(size=11)))
    return fig


def bar_chart(x, y, colors, horizontal=False, height=260):
    if isinstance(colors, str):
        colors = [colors] * len(x)
    if horizontal:
        fig = go.Figure(go.Bar(x=y, y=x, orientation="h",
                               marker_color=colors, marker_line_width=0))
    else:
        fig = go.Figure(go.Bar(x=x, y=y,
                               marker_color=colors, marker_line_width=0))
    fig.update_layout(**_layout(height=height))
    return fig


def _color_list(labels, cmap, default="#64748B"):
    return [cmap.get(str(l), default) for l in labels]


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    initials = "".join(w[0] for w in name.split()[:2]).upper() if name else "?"
    now = datetime.now()
    date_str = f"{now.day} {now.strftime('%b %Y')}"

    st.markdown(f"""
<div style="padding:8px 4px 16px;">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="background:#4F46E5;width:32px;height:32px;border-radius:9px;
                flex-shrink:0;display:flex;align-items:center;justify-content:center;
                font-weight:700;font-size:14px;color:white;">K</div>
    <div>
      <div style="font-weight:700;font-size:17px;color:white;line-height:1.2;">KostPro</div>
      <div style="font-size:10px;color:#64748B;">{date_str}</div>
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


# ════════════════════════════ EXECUTIVE ════════════════════════════════════════
if menu == "Executive":
    e = DASH.get("EXECUTIVE", {})
    st.markdown('<h2 style="font-size:24px;font-weight:700;color:#0F172A;margin:0 0 2px;">Ringkasan Eksekutif</h2>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#64748B;margin:0 0 20px;">Kinerja portofolio kost · BOD / Owner</p>', unsafe_allow_html=True)

    laba = D.to_num(e.get("Laba Usaha", 0))

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Pendapatan Bulan Ini",
        D.rupiah(e.get("Pendapatan Usaha", 0), juta=True),
        f"Beban {D.rupiah(e.get('Beban Usaha', 0), juta=True)}")
    kpi(c2, "Tingkat Hunian",
        D.persen(e.get("Okupansi Komitmen", 0)),
        f"Fisik {D.persen(e.get('Okupansi Fisik', 0))}", "pos")
    kpi(c3, "Laba / Margin Usaha",
        D.rupiah(laba, juta=True),
        f"Margin {D.persen(e.get('Margin Usaha', 0))}",
        "pos" if laba >= 0 else "neg")
    kpi(c4, "RevPAR",
        D.rupiah(e.get("RevPAR (pendapatan/kamar)", 0)),
        f"Penghuni aktif: {e.get('Penghuni Aktif', '-')}")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    p = D.penghuni()

    # Row 1: Tren + Status Penghuni
    g1, g2 = st.columns([2, 1])
    with g1:
        chart_header("Tren Pendapatan vs Biaya Operasional", "Bulanan · Rp Juta")
        kb = D.keuangan_per_bulan()
        if kb.empty:
            st.info("Belum ada data keuangan.")
        else:
            kb2 = kb.copy()
            kb2["Pendapatan Usaha"] = kb2["Pendapatan Usaha"] / 1_000_000
            kb2["Beban Usaha"]      = kb2["Beban Usaha"]      / 1_000_000
            fig = go.Figure()
            fig.add_scatter(x=kb2["Bulan"], y=kb2["Pendapatan Usaha"], name="Pendapatan",
                            line=dict(color=ac, width=2.5),
                            fill='tozeroy', fillcolor='rgba(79,70,229,0.08)')
            fig.add_scatter(x=kb2["Bulan"], y=kb2["Beban Usaha"], name="Beban",
                            line=dict(color="#DC2626", width=2))
            lay = _layout(height=240, ysfx=" Jt")
            lay["legend"] = dict(orientation='h', y=1.12, x=0, font=dict(size=11))
            fig.update_layout(**lay)
            st.plotly_chart(fig, use_container_width=True, config=_CFG)

    with g2:
        chart_header("Status Penghuni", "Komposisi saat ini")
        vc = D.value_counts(p, "Status")
        if vc.empty:
            st.info("Belum ada data penghuni.")
        else:
            SCOL = {"Aktif": "#16A34A", "Booking (DP)": "#F59E0B", "Non Aktif": "#94A3B8"}
            colors = _color_list(vc.index, SCOL)
            st.plotly_chart(donut(vc.index.tolist(), vc.values.tolist(),
                                  colors, f"{int(vc.sum())} org"),
                            use_container_width=True, config=_CFG)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # Row 2: Hunian per Jenis Kamar + Segmen Usia
    g3, g4 = st.columns(2)
    with g3:
        chart_header("Hunian per Jenis Kamar", "Jumlah kamar terisi saat ini")
        if not p.empty and "Jenis Kamar" in p.columns:
            if "Status Okupansi" in p.columns:
                terisi = p[p["Status Okupansi"].astype(str).str.contains("Terisi", na=False)]
            else:
                terisi = p
            vc = D.value_counts(terisi, "Jenis Kamar")
            if not vc.empty:
                KCOL = {"Eco": "#4F46E5", "Classic": "#059669", "Comfy": "#F59E0B"}
                colors = _color_list(vc.index, KCOL, "#94A3B8")
                st.plotly_chart(bar_chart(vc.index.tolist(), vc.values.tolist(), colors),
                                use_container_width=True, config=_CFG)
            else:
                st.info("Belum ada kamar terisi.")
        else:
            st.info("Data jenis kamar tidak tersedia.")

    with g4:
        chart_header("Segmen Usia Penghuni", "Distribusi kelompok usia")
        if not p.empty and "Segmen Usia" in p.columns:
            vc_u = D.value_counts(p, "Segmen Usia")
            if not vc_u.empty:
                vc_u = vc_u.sort_index()
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
                         "Sisa Hari": st.column_config.NumberColumn("Sisa Hari", format="%d hr"),
                     })
    else:
        st.info("Belum ada data penghuni.")


# ════════════════════════════ SALES ═══════════════════════════════════════════
elif menu == "Sales":
    s = DASH.get("SALES", {})
    st.markdown('<h2 style="font-size:24px;font-weight:700;color:#0F172A;margin:0 0 2px;">Dashboard Sales</h2>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#64748B;margin:0 0 20px;">Akuisisi penyewa & pipeline</p>', unsafe_allow_html=True)

    cancel = D.to_num(s.get("Cancel Rate", 0))
    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Total Leads", str(s.get("Total Leads", "-")),
        f"Belum di-FU: {s.get('Leads belum di-FU', '-')}", "warn")
    kpi(c2, "Konversi Lead→Survey", D.persen(s.get("Konversi Lead->Survey", 0)), "", "pos")
    kpi(c3, "Konversi Survey→Deal", D.persen(s.get("Konversi Survey->Deal", 0)), "", "pos")
    kpi(c4, "Nilai Kontrak Deal",
        D.rupiah(s.get("Nilai Kontrak Deal", 0), juta=True),
        f"Cancel rate {D.persen(cancel)}",
        "neg" if cancel > 0 else "pos")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        chart_header("Funnel Penjualan", "Lead → Survey → Booking → Deal")
        fn = D.funnel_sales()
        fig = go.Figure(go.Funnel(
            y=[a for a, _ in fn], x=[b for _, b in fn],
            textinfo="value+percent initial",
            marker=dict(color=["#4F46E5", "#059669", "#F59E0B", "#16A34A"]),
            connector=dict(line=dict(color="#E2E8F0", width=2))
        ))
        fig.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10),
                          paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True, config=_CFG)

    with g2:
        chart_header("Sumber Leads", "Distribusi per channel")
        vc = D.value_counts(D.read_tab("6_LEADS", "Nama Leads"), "Sumber Leads")
        if vc.empty:
            st.info("Belum ada data leads.")
        else:
            st.plotly_chart(donut(vc.index.tolist(), vc.values.tolist(),
                                  ["#059669", "#34D399", "#3B82F6", "#F59E0B", "#94A3B8"],
                                  f"{int(vc.sum())}"),
                            use_container_width=True, config=_CFG)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    chart_header("Pipeline Booking", "Status transaksi")
    bk = D.read_tab("8_BOOKING", "No Booking")
    if not bk.empty:
        cols = [c for c in ["No Booking", "Nama Penyewa", "Kamar", "Tgl Masuk",
                             "Durasi (Bln)", "Nilai Kontrak", "Per Bulan",
                             "Sumber", "Status"] if c in bk.columns]
        st.dataframe(bk[cols], use_container_width=True, hide_index=True,
                     column_config={
                         "Per Bulan": st.column_config.NumberColumn("Per Bulan (Rp)", format="Rp %d"),
                     })
    else:
        st.info("Belum ada data booking.")


# ════════════════════════════ ADMIN ═══════════════════════════════════════════
elif menu == "Admin":
    a = DASH.get("ADMIN", {})
    st.markdown('<h2 style="font-size:24px;font-weight:700;color:#0F172A;margin:0 0 2px;">Dashboard Admin & Keuangan</h2>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#64748B;margin:0 0 20px;">Penagihan, kontrak & hunian</p>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Jatuh Tempo ≤7 Hari",  str(a.get("Jatuh tempo <=7 hari", "-")), "Perlu ditagih segera", "neg")
    kpi(c2, "Tunggakan / Overdue",   str(a.get("Tunggakan / overdue", "-")), "Melewati jatuh tempo", "neg")
    kpi(c3, "Kamar Kosong",          str(a.get("Kamar kosong", "-")),         "Siap disewa")
    kpi(c4, "Kontrak Berakhir ≤30 Hari", str(a.get("Kontrak berakhir <=30 hari", "-")), "Perlu diperpanjang", "warn")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    p = D.penghuni()

    g1, g2 = st.columns(2)
    with g1:
        chart_header("Status Tagihan", "Distribusi flag penagihan")
        vc = D.value_counts(p, "Flag Tagih")
        if not vc.empty:
            FCOL = {"Aman": "#16A34A", "<30 hari": "#F59E0B",
                    "SEGERA": "#D97706", "LEWAT": "#DC2626"}
            colors = _color_list(vc.index, FCOL, "#94A3B8")
            st.plotly_chart(bar_chart(vc.index.tolist(), vc.values.tolist(), colors),
                            use_container_width=True, config=_CFG)
        else:
            st.info("Belum ada data tagihan.")

    with g2:
        chart_header("Status Hunian", "Terisi vs Kosong")
        vc = D.value_counts(p, "Status Okupansi")
        if not vc.empty:
            OCOL = {"Terisi": "#16A34A", "Kosong": "#94A3B8"}
            colors = _color_list(vc.index, OCOL)
            st.plotly_chart(donut(vc.index.tolist(), vc.values.tolist(),
                                  colors, f"{int(vc.sum())}"),
                            use_container_width=True, config=_CFG)
        else:
            st.info("Belum ada data hunian.")

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    chart_header("Prioritas Penagihan", "Penghuni mendekati / melewati jatuh tempo")
    if not p.empty and "Flag Tagih" in p.columns:
        prioritas = p[p["Flag Tagih"].astype(str).str.contains("SEGERA|LEWAT|<30", na=False)]
        cols = [c for c in ["No Kamar", "Nama Lengkap", "Panggilan", "Tgl Jatuh Tempo",
                             "Sisa Hari", "Flag Tagih", "Tarif Sewa",
                             "Kontak Darurat"] if c in p.columns]
        display_df = (prioritas if not prioritas.empty else p)[cols]
        st.dataframe(display_df, use_container_width=True, hide_index=True,
                     column_config={
                         "Tarif Sewa": st.column_config.NumberColumn("Tarif Sewa (Rp)", format="Rp %d"),
                         "Sisa Hari": st.column_config.NumberColumn("Sisa Hari", format="%d hr"),
                     })
    else:
        st.info("Belum ada data penghuni.")


# ════════════════════════════ MARKETING ═══════════════════════════════════════
elif menu == "Marketing":
    m = DASH.get("MARKETING", {})
    st.markdown('<h2 style="font-size:24px;font-weight:700;color:#0F172A;margin:0 0 2px;">Dashboard Marketing</h2>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#64748B;margin:0 0 20px;">Konten, kanal & efektivitas iklan</p>', unsafe_allow_html=True)

    reach_str = f"{int(D.to_num(m.get('Total Reach', 0))):,}".replace(",", ".")
    eng_str   = f"{int(D.to_num(m.get('Total Engagement', 0))):,}".replace(",", ".")
    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Total Reach", reach_str, f"Engagement {eng_str}")
    kpi(c2, "Avg Engagement Rate", D.persen(m.get("Avg ER", 0)), "", "pos")
    kpi(c3, "Avg CPL", D.rupiah(m.get("Avg CPL", 0)),
        f"Total spend {D.rupiah(m.get('Total Spend Ads', 0), juta=True)}")
    kpi(c4, "Konversi Lead→Booking",
        D.persen(m.get("Conv Lead->Booking", 0)),
        f"Konten belum tayang: {m.get('Konten belum tayang', '-')}", "warn")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        chart_header("Reach per Platform", "Total jangkauan per kanal")
        k = D.konten()
        if not k.empty and "Platform" in k.columns and "Reach" in k.columns:
            k["Reach"] = k["Reach"].map(D.to_num)
            g = k.groupby("Platform")["Reach"].sum().sort_values(ascending=False)
            st.plotly_chart(bar_chart(g.index.tolist(), g.values.tolist(), ac),
                            use_container_width=True, config=_CFG)
        else:
            st.info("Belum ada data konten.")

    with g2:
        chart_header("ROI Kotor per Promosi", "Hijau = ROI ≥ target")
        pr = D.promosi()
        if not pr.empty and "Nama Promosi" in pr.columns and "ROI Kotor" in pr.columns:
            pr["ROI Kotor"] = pr["ROI Kotor"].map(D.to_num)
            target = D.to_num(D.read_tab("1_PARAMETER", "Parameter")
                              .set_index("Parameter")["Nilai"]
                              .get("Target ROI campaign (%)", 1)
                              if not D.read_tab("1_PARAMETER", "Parameter").empty else 1)
            roi_colors = ["#16A34A" if v >= target else "#DC2626" for v in pr["ROI Kotor"]]
            fig = go.Figure(go.Bar(x=pr["Nama Promosi"].tolist(),
                                   y=pr["ROI Kotor"].tolist(),
                                   marker_color=roi_colors, marker_line_width=0))
            fig.update_layout(**_layout())
            st.plotly_chart(fig, use_container_width=True, config=_CFG)
        else:
            st.info("Belum ada data promosi.")

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    chart_header("Kinerja Konten", "Performa per postingan")
    k = D.konten()
    if not k.empty:
        cols = [c for c in ["Tgl Post", "Platform", "Tipe Konten", "Judul/Caption",
                             "Status", "Reach", "Likes", "Komentar",
                             "Engagement", "ER (%)"] if c in k.columns]
        st.dataframe(k[cols], use_container_width=True, hide_index=True,
                     column_config={
                         "ER (%)": st.column_config.NumberColumn("ER (%)", format="%.4f"),
                     })
    else:
        st.info("Belum ada data konten.")


# ════════════════════════════ OPERASIONAL ═════════════════════════════════════
else:
    o = DASH.get("OPERASIONAL", {})
    st.markdown('<h2 style="font-size:24px;font-weight:700;color:#0F172A;margin:0 0 2px;">Dashboard Operasional</h2>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#64748B;margin:0 0 20px;">Teknisi, perawatan & SLA · Tim Lapangan</p>', unsafe_allow_html=True)

    breach = D.to_num(o.get("Breach SLA", 0))
    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Total Tiket", str(o.get("Total Tiket", "-")),
        f"Selesai: {o.get('Selesai', '-')}")
    kpi(c2, "Breach SLA", str(o.get("Breach SLA", "-")),
        "Ada pelanggaran SLA!" if breach > 0 else "Semua dalam SLA",
        "neg" if breach > 0 else "pos")
    kpi(c3, "MTTR", f"{o.get('MTTR (hari)', '-')} hari", "Mean Time to Resolve")
    kpi(c4, "Biaya Maintenance",
        D.rupiah(o.get("Biaya Maintenance", 0)),
        f"Prev:Korektif = {o.get('Rasio Preventif:Korektif', '-')}")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    mt = D.maintenance()

    g1, g2 = st.columns(2)
    with g1:
        chart_header("Jenis Perawatan", "Preventif vs Korektif")
        vc = D.value_counts(mt, "Jenis Perawatan")
        if not vc.empty:
            MCOL = {"Preventif": "#4F46E5", "Korektif": "#EA580C"}
            colors = _color_list(vc.index, MCOL)
            st.plotly_chart(bar_chart(vc.index.tolist(), vc.values.tolist(), colors),
                            use_container_width=True, config=_CFG)
        else:
            st.info("Belum ada data maintenance.")

    with g2:
        chart_header("Status Tiket", "Distribusi penyelesaian")
        vc = D.value_counts(mt, "Status")
        if not vc.empty:
            STCOL = {"Selesai": "#16A34A", "Proses": "#F59E0B",
                     "Pending": "#94A3B8", "Batal": "#DC2626"}
            colors = _color_list(vc.index, STCOL)
            st.plotly_chart(donut(vc.index.tolist(), vc.values.tolist(),
                                  colors, f"{int(vc.sum())}"),
                            use_container_width=True, config=_CFG)
        else:
            st.info("Belum ada data tiket.")

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    chart_header("Log Tiket Maintenance", "Semua tiket aktif & selesai")
    if not mt.empty:
        cols = [c for c in ["Tgl Lapor/Jadwal", "Tgl Selesai", "Lokasi/Item",
                             "Deskripsi", "Prioritas", "Pelaksana", "Vendor",
                             "Biaya", "Status", "SLA OK?",
                             "Jenis Perawatan"] if c in mt.columns]
        st.dataframe(mt[cols], use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data tiket.")

st.divider()
st.caption("🔒 Akses terbatas · Data live dari Google Sheets · Cache 5 menit")
