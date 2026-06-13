"""
hash_password.py — buat hash bcrypt untuk password login.

Jalankan SEKALI di laptop kamu (password tidak dikirim ke mana-mana):

    python hash_password.py

Lalu salin hash yang muncul ke .streamlit/secrets.toml
(field `password` di bawah tiap username). Password asli TIDAK PERNAH
disimpan di kode atau repo — hanya hash-nya.
"""

import getpass
import bcrypt

if __name__ == "__main__":
    while True:
        pw = getpass.getpass("Masukkan password baru (kosong = selesai): ")
        if not pw:
            break
        h = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
        print("hash :", h)
        print("-> tempel string di atas ke field password secrets.toml\n")
