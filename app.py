"""
app.py — Dashboard Rumah Pandega (Streamlit).

Login ditangani di BACKEND:
- Kredensial (username + hash bcrypt) ada di st.secrets -> tersimpan server-side,
  tidak pernah dikirim ke browser. Password plaintext TIDAK ADA di kode/repo.
- Verifikasi hash dilakukan oleh streamlit-authenticator di server.

Data:
- KPI cards  -> tab 10_DASHBOARD (sumber kebenaran, formula dirawat di Sheets).
- Chart/tabel -> tab mentah (2_PENGHUNI, 3_KEUANGAN, 4_KONTEN, 5_PROMOSI,
  6_LEADS, 7_SURVEY, 8_BOOKING, 9/10_MAINTENANCE).
"""

import plotly.graph_objects as go
import streamlit as st
import streamlit_authenticator as stauth

import data as D

# ============================ KONFIG HALAMAN ============================
st.set_page_config(page_title="Rumah Pandega — Dashboard",
                   page_icon="🏠", layout="wide",
                   initial_sidebar_state="expanded")

ACCENT = {"Executive": "#4F46E5", "Sales": "#059669", "Admin": "#2563EB",
          "Marketing": "#7C3AED", "Operasional": "#EA580C"}

st.markdown("""
<style>
.block-container {padding-top: 2rem;}
.kpi {background:#FFFFFF;border:1px solid #E8EDF3;border-radius:16px;padding:18px 20px;}
.kpi .lab {font-size:12px;color:#64748B;font-weight:500;}
.kpi .val {font-size:24px;color:#0F172A;font-weight:700;margin:6px 0 2px;}
.kpi .sub {font-size:11px;color:#64748B;}
[data-testid="stSidebar"] {background:#0F172A;}
[data-testid="stSidebar"] * {color:#E2E8F0;}
</style>
""", unsafe_allow_html=True)


# ============================ AUTENTIKASI (BACKEND) ============================
def build_authenticator():
    """Bangun objek auth dari kredensial di st.secrets (server-side)."""
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
name = st.session_state.get("name")
auth_status = st.session_state.get("authentication_status")
username = st.session_state.get("username")

if auth_status is False:
    st.error("Username / password salah.")
    st.stop()
if auth_status is None:
    st.info("Silakan login untuk melihat dashboard.")
    st.stop()


# ============================ KOMPONEN UI ============================
def kpi(col, label, value, sub=""):
    col.markdown(
        f'<div class="kpi"><div class="lab">{label}</div>'
        f'<div class="val">{value}</div><div class="sub">{sub}</div></div>',
        unsafe_allow_html=True)


def donut(labels, values, colors, total_label=""):
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=.62,
                           marker=dict(colors=colors), sort=False))
    fig.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10),
                      annotations=[dict(text=total_label, showarrow=False,
                                        font_size=16)])
    return fig


def bars(x, y, color, horizontal=False):
    fig = (go.Figure(go.Bar(x=y, y=x, orientation="h", marker_color=color))
           if horizontal else go.Figure(go.Bar(x=x, y=y, marker_color=color)))
    fig.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10))
    return fig


# ============================ SIDEBAR ============================
st.sidebar.markdown("### 🏠 Rumah Pandega")
st.sidebar.caption("Property Suite")
menu = st.sidebar.radio("Divisi", list(ACCENT.keys()))
st.sidebar.divider()
st.sidebar.write(f"👤 **{name}**")
authenticator.logout("Logout", "sidebar")
if st.sidebar.button("🔄 Refresh data"):
    st.cache_data.clear()
    st.rerun()

DASH = D.read_dashboard()
ac = ACCENT[menu]


# ============================ EXECUTIVE ============================
if menu == "Executive":
    e = DASH.get("EXECUTIVE", {})
    st.title("Ringkasan Eksekutif")
    st.caption("Kinerja portofolio kost · BOD / Owner")

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Pendapatan Usaha", D.rupiah(e.get("Pendapatan Usaha", 0), juta=True),
        f"Beban {D.rupiah(e.get('Beban Usaha', 0), juta=True)}")
    kpi(c2, "Okupansi Komitmen", D.persen(e.get("Okupansi Komitmen", 0)),
        f"Fisik {D.persen(e.get('Okupansi Fisik', 0))}")
    kpi(c3, "Laba / Margin Usaha", D.rupiah(e.get("Laba Usaha", 0), juta=True),
        f"Margin {D.persen(e.get('Margin Usaha', 0))}")
    kpi(c4, "RevPAR", D.rupiah(e.get("RevPAR (pendapatan/kamar)", 0)),
        f"Penghuni aktif {e.get('Penghuni Aktif', '-')}")

    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Pendapatan vs Beban per Bulan")
        kb = D.keuangan_per_bulan()
        if kb.empty:
            st.info("Belum ada data 3_KEUANGAN.")
        else:
            fig = go.Figure()
            fig.add_bar(x=kb["Bulan"], y=kb["Pendapatan Usaha"], name="Pendapatan",
                        marker_color=ac)
            fig.add_bar(x=kb["Bulan"], y=kb["Beban Usaha"], name="Beban",
                        marker_color="#DC2626")
            fig.update_layout(height=300, barmode="group",
                              margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
    with g2:
        st.subheader("Status Penghuni")
        vc = D.value_counts(D.penghuni(), "Status")
        if vc.empty:
            st.info("Belum ada data 2_PENGHUNI.")
        else:
            st.plotly_chart(donut(vc.index.tolist(), vc.values.tolist(),
                                  ["#16A34A", "#F59E0B", "#94A3B8", "#DC2626"],
                                  f"{int(vc.sum())} org"), use_container_width=True)

    st.subheader("Okupansi per Jenis Kamar")
    p = D.penghuni()
    if not p.empty and "Jenis Kamar" in p.columns:
        if "Status Okupansi" in p.columns:
            terisi = p[p["Status Okupansi"].astype(str).str.contains("Terisi", na=False)]
        else:
            terisi = p
        vc = D.value_counts(terisi, "Jenis Kamar")
        if not vc.empty:
            st.plotly_chart(bars(vc.index.tolist(), vc.values.tolist(), ac),
                            use_container_width=True)
    st.subheader("Daftar Penghuni")
    if not p.empty:
        cols = [c for c in ["No Kamar", "Nama Lengkap", "Jenis Kamar", "Status",
                            "Tgl Jatuh Tempo", "Flag Tagih", "Tarif Sewa"] if c in p.columns]
        st.dataframe(p[cols], use_container_width=True, hide_index=True)


# ============================ SALES ============================
elif menu == "Sales":
    s = DASH.get("SALES", {})
    st.title("Dashboard Sales")
    st.caption("Akuisisi penyewa & pipeline")

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Total Leads", s.get("Total Leads", "-"),
        f"Belum di-FU: {s.get('Leads belum di-FU', '-')}")
    kpi(c2, "Konversi Lead→Survey", D.persen(s.get("Konversi Lead->Survey", 0)))
    kpi(c3, "Konversi Survey→Deal", D.persen(s.get("Konversi Survey->Deal", 0)))
    kpi(c4, "Nilai Kontrak Deal", D.rupiah(s.get("Nilai Kontrak Deal", 0), juta=True),
        f"Cancel rate {D.persen(s.get('Cancel Rate', 0))}")

    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Funnel Penjualan")
        fn = D.funnel_sales()
        fig = go.Figure(go.Funnel(y=[a for a, _ in fn], x=[b for _, b in fn],
                                  marker=dict(color=ac)))
        fig.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        st.subheader("Sumber Leads")
        vc = D.value_counts(D.read_tab("6_LEADS", "Nama Leads"), "Sumber Leads")
        if vc.empty:
            st.info("Belum ada data 6_LEADS.")
        else:
            st.plotly_chart(donut(vc.index.tolist(), vc.values.tolist(),
                                  ["#059669", "#34D399", "#3B82F6", "#F59E0B"],
                                  f"{int(vc.sum())}"), use_container_width=True)

    st.subheader("Pipeline Booking")
    bk = D.read_tab("8_BOOKING", "No Booking")
    if not bk.empty:
        cols = [c for c in ["No Booking", "Nama Penyewa", "Kamar", "Tgl Masuk",
                            "Nilai Kontrak", "Sumber", "Status"] if c in bk.columns]
        st.dataframe(bk[cols], use_container_width=True, hide_index=True)


# ============================ ADMIN ============================
elif menu == "Admin":
    a = DASH.get("ADMIN", {})
    st.title("Dashboard Admin & Keuangan")
    st.caption("Penagihan, kontrak & hunian")

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Jatuh Tempo ≤7 hari", a.get("Jatuh tempo <=7 hari", "-"))
    kpi(c2, "Tunggakan / Overdue", a.get("Tunggakan / overdue", "-"))
    kpi(c3, "Kamar Kosong", a.get("Kamar kosong", "-"))
    kpi(c4, "Kontrak Berakhir ≤30 hari", a.get("Kontrak berakhir <=30 hari", "-"))

    p = D.penghuni()
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Flag Tagih")
        vc = D.value_counts(p, "Flag Tagih")
        if not vc.empty:
            st.plotly_chart(bars(vc.index.tolist(), vc.values.tolist(), ac),
                            use_container_width=True)
    with g2:
        st.subheader("Status Hunian")
        vc = D.value_counts(p, "Status Okupansi")
        if not vc.empty:
            st.plotly_chart(donut(vc.index.tolist(), vc.values.tolist(),
                                  ["#16A34A", "#DC2626"], f"{int(vc.sum())}"),
                            use_container_width=True)

    st.subheader("Penghuni Mendekati Jatuh Tempo")
    if not p.empty and "Flag Tagih" in p.columns:
        prioritas = p[p["Flag Tagih"].astype(str).str.contains("SEGERA|LEWAT|30", na=False)]
        cols = [c for c in ["No Kamar", "Nama Lengkap", "Tgl Jatuh Tempo",
                            "Sisa Hari", "Flag Tagih", "Tarif Sewa"] if c in p.columns]
        st.dataframe((prioritas if not prioritas.empty else p)[cols],
                     use_container_width=True, hide_index=True)


# ============================ MARKETING ============================
elif menu == "Marketing":
    m = DASH.get("MARKETING", {})
    st.title("Dashboard Marketing")
    st.caption("Konten, kanal & efektivitas iklan")

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Total Reach", f"{int(D.to_num(m.get('Total Reach', 0))):,}".replace(",", "."),
        f"Engagement {int(D.to_num(m.get('Total Engagement', 0)))}")
    kpi(c2, "Avg Engagement Rate", D.persen(m.get("Avg ER", 0)))
    kpi(c3, "Avg CPL", D.rupiah(m.get("Avg CPL", 0)),
        f"Spend {D.rupiah(m.get('Total Spend Ads', 0))}")
    kpi(c4, "Konversi Lead→Booking", D.persen(m.get("Conv Lead->Booking", 0)),
        f"Konten belum tayang: {m.get('Konten belum tayang', '-')}")

    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Reach per Platform")
        k = D.konten()
        if not k.empty and "Platform" in k.columns and "Reach" in k.columns:
            k["Reach"] = k["Reach"].map(D.to_num)
            g = k.groupby("Platform")["Reach"].sum().sort_values(ascending=False)
            st.plotly_chart(bars(g.index.tolist(), g.values.tolist(), ac),
                            use_container_width=True)
        else:
            st.info("Belum ada data 4_KONTEN.")
    with g2:
        st.subheader("ROI Kotor per Promosi")
        pr = D.promosi()
        if not pr.empty and "Nama Promosi" in pr.columns and "ROI Kotor" in pr.columns:
            pr["ROI Kotor"] = pr["ROI Kotor"].map(D.to_num)
            st.plotly_chart(bars(pr["Nama Promosi"].tolist(),
                                 pr["ROI Kotor"].tolist(), ac),
                            use_container_width=True)
        else:
            st.info("Belum ada data 5_PROMOSI.")

    st.subheader("Kinerja Konten")
    k = D.konten()
    if not k.empty:
        cols = [c for c in ["Tgl Post", "Platform", "Tipe Konten", "Status",
                            "Reach", "Engagement", "ER (%)"] if c in k.columns]
        st.dataframe(k[cols], use_container_width=True, hide_index=True)


# ============================ OPERASIONAL ============================
else:
    o = DASH.get("OPERASIONAL", {})
    st.title("Dashboard Operasional")
    st.caption("Teknisi, perawatan & SLA · Tim Lapangan")

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Total Tiket", o.get("Total Tiket", "-"),
        f"Selesai: {o.get('Selesai', '-')}")
    kpi(c2, "Breach SLA", o.get("Breach SLA", "-"))
    kpi(c3, "MTTR (hari)", o.get("MTTR (hari)", "-"))
    kpi(c4, "Biaya Maintenance", D.rupiah(o.get("Biaya Maintenance", 0)),
        f"Rasio Prev:Korektif {o.get('Rasio Preventif:Korektif', '-')}")

    mt = D.maintenance()
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Tiket per Jenis Perawatan")
        vc = D.value_counts(mt, "Jenis Perawatan")
        if not vc.empty:
            st.plotly_chart(bars(vc.index.tolist(), vc.values.tolist(), ac),
                            use_container_width=True)
        else:
            st.info("Belum ada data maintenance.")
    with g2:
        st.subheader("Status Tiket")
        vc = D.value_counts(mt, "Status")
        if not vc.empty:
            st.plotly_chart(donut(vc.index.tolist(), vc.values.tolist(),
                                  ["#16A34A", "#F59E0B", "#DC2626"], f"{int(vc.sum())}"),
                            use_container_width=True)

    st.subheader("Daftar Tiket Maintenance")
    if not mt.empty:
        cols = [c for c in ["Tgl Lapor/Jadwal", "Lokasi/Item", "Deskripsi",
                            "Prioritas", "Pelaksana", "Biaya", "Status",
                            "SLA OK?", "Jenis Perawatan"] if c in mt.columns]
        st.dataframe(mt[cols], use_container_width=True, hide_index=True)

st.divider()
st.caption("🔒 Akses terbatas — hanya pengguna terdaftar. Data live dari Google Sheets (cache 5 menit).")
