# Dashboard Rumah Pandega — Streamlit

Dashboard online untuk kost Rumah Pandega. 5 divisi (Executive, Sales, Admin,
Marketing, Operasional), data **live** dari Google Sheets `Rumah_Pandega_LIVE_v2`,
login ditangani di **backend**, hosting **gratis** (Streamlit Cloud).

---

## 0. Bagaimana ini bekerja (singkat)

- **KPI cards** dibaca dari tab **`10_DASHBOARD`** — tab itu sudah meng-compute
  angka per divisi lewat formula. Kamu cukup merawat formula di Sheets; dashboard
  ikut update otomatis.
- **Chart & tabel** dibaca dari tab mentah (`2_PENGHUNI`, `3_KEUANGAN`,
  `4_KONTEN`, `5_PROMOSI`, `6_LEADS`, `7_SURVEY`, `8_BOOKING`,
  `9_PREVENTIVE MAINTENANCE`, `10_CORRECTIVE MAINTENANCE`).
- **Login backend**: username + **hash bcrypt** disimpan di `secrets.toml`
  (server-side). Password asli tidak pernah ada di kode, repo, atau browser.
- **Desain** mengikuti UI Figma: sidebar gelap, warna aksen per divisi, kartu KPI,
  chart, tabel.

> Catatan jujur: di Streamlit, *seluruh* Python (termasuk cek password) memang
> jalan di server — jadi password tidak pernah "di frontend". Yang kita perbaiki
> di sini: password kini **di-hash**, bukan dibandingkan sebagai teks polos.

---

## 1. Isi file

```
kost-dashboard/
├── app.py                         # aplikasi utama (UI + login)
├── data.py                        # koneksi & pembacaan Google Sheets
├── hash_password.py               # bikin hash password (jalan sekali)
├── requirements.txt               # dependency
├── .gitignore
└── .streamlit/
    └── secrets.toml.example       # template rahasia (login + koneksi Sheets)
```

---

## 2. Setup lokal (15 menit)

```bash
cd kost-dashboard
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2a. Buat password (backend)
```bash
python hash_password.py
```
Masukkan password yang kamu mau → keluar string `$2b$12$...`. Salin string itu.

### 2b. Siapkan secrets
```bash
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```
Buka `.streamlit/secrets.toml`, lalu:
- tempel hash bcrypt ke field `password` (ganti satu per user),
- isi `[auth.cookie] key` dengan string acak panjang,
- bagian `[connections.gsheets]` diisi setelah langkah 3.

---

## 3. Sambungkan Google Sheets via Service Account (10 menit)

Cara paling aman & gratis untuk membaca sheet **privat**.

1. Buka <https://console.cloud.google.com> → buat / pilih project.
2. **APIs & Services → Enable APIs**: aktifkan **Google Sheets API** dan
   **Google Drive API**.
3. **IAM & Admin → Service Accounts → Create**: beri nama (mis. `dashboard`).
4. Pada service account → **Keys → Add key → JSON** → unduh file JSON.
5. Buka file JSON, salin nilainya ke `[connections.gsheets]` di `secrets.toml`
   (`project_id`, `private_key_id`, `private_key`, `client_email`, dst).
   - `spreadsheet` sudah diisi URL `Rumah_Pandega_LIVE_v2`.
6. **Share spreadsheet** ke `client_email` service account (akses **Viewer**).
   (Di Google Sheets → Share → tempel email service account.)

> Alternatif cepat (kurang aman): set spreadsheet "Anyone with link – Viewer",
> lalu cukup isi `spreadsheet = "<url>"` tanpa kredensial. Untuk data penghuni
> (ada email & no HP), sebaiknya **pakai service account**, jangan dibuat publik.

---

## 4. Tes lokal

```bash
streamlit run app.py
```
Buka <http://localhost:8501> → login → cek 5 divisi, tabel & chart terisi dari
data nyata. Tombol **Refresh data** di sidebar mengosongkan cache (5 menit).

---

## 5. Deploy gratis ke Streamlit Cloud (10 menit)

1. Push folder ini ke **GitHub** (repo boleh public — rahasia TIDAK ikut karena
   `.gitignore` mengecualikan `secrets.toml`):
   ```bash
   git init && git add . && git commit -m "dashboard rumah pandega"
   git branch -M main
   git remote add origin https://github.com/<user>/kost-dashboard.git
   git push -u origin main
   ```
2. Buka <https://share.streamlit.io> → **New app** → pilih repo, branch `main`,
   file `app.py` → **Deploy**.
3. **App → Settings → Secrets**: tempel **seluruh isi** `secrets.toml` kamu
   (login hash + koneksi gsheets) → Save. App auto-rerun.
4. Selesai. URL publik muncul (mis. `https://<app>.streamlit.app`).
   Siapa pun yang buka **harus login** dulu.

---

## 6. Operasional harian

- **Update data**: edit Google Sheets seperti biasa → dashboard ikut berubah
  (maksimal 5 menit, atau tekan Refresh).
- **Tambah/ubah user**: tambah blok `[auth.credentials.usernames.<user>]` di
  Secrets (hash dari `hash_password.py`).
- **Ganti angka KPI**: cukup perbaiki formula di tab `10_DASHBOARD`.

---

## 7. Keamanan — ringkas

| Aspek | Status |
|---|---|
| Password | hash bcrypt, di Secrets backend, tidak di repo |
| Sesi | cookie bertenggat (`expiry_days`) |
| Akses Sheets | service account privat (bukan link publik) |
| Yang bisa lihat | hanya user terdaftar yang berhasil login |

**Opsi lebih aman (opsional):** ganti login password dengan **Login Google
(OIDC)** bawaan Streptlit `st.login()` — tidak ada password sama sekali, identitas
diverifikasi Google. Perlu setup OAuth Client di Google Cloud. Bisa diterapkan
nanti tanpa mengubah bagian data.

---

## 8. Troubleshooting

- **`KeyError: 'auth'` / `connections`** → Secrets belum diisi/ belum di-Save.
- **`WorksheetNotFound`** → nama tab di Sheets beda dari yang dipakai di `data.py`
  (mis. spasi). Samakan nama tab.
- **Chart kosong / "Belum ada data"** → tab mentah masih kosong; isi datanya.
  KPI cards tetap muncul dari `10_DASHBOARD`.
- **Login gagal terus** → pastikan hash di Secrets dibuat oleh `hash_password.py`
  dan password yang diketik benar.
