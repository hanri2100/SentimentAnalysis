# Prapemrosesan Teks & Analisis (Streamlit)

Aplikasi Streamlit interaktif untuk prapemrosesan teks (case folding, tokenisasi, normalisasi ke kata baku, penghapusan stopword, stemming/lemmatization) dan analisis visual
sederhana (frekuensi kata dan word cloud). Label antarmuka sebagian besar sudah dalam Bahasa Indonesia; README ini kini juga dalam Bahasa Indonesia.

## Kebutuhan Sistem

- Python 3.12 (lihat `.python-version`)
- Internet untuk mengunduh NLTK secara otomatis
- OS: Windows/macOS/Linux

Dependensi didefinisikan di `pyproject.toml` dan dikunci di `uv.lock` (dikelola oleh uv).

### Instal uv

uv adalah package manager untuk Python

1) Cara Instal uv

- Windows (PowerShell):
    - `powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- macOS/Linux:
    - `curl -LsSf https://astral.sh/uv/install.sh | sh`

2) Update dependensi:

```
uv sync
```

3) Jalankan aplikasi:

```
uv run streamlit run app.py
```

Hasil dari command ini berupa link yg bisa diklik. silahkan klik output terminal (biasanya http://localhost:8501).


## Tahapan aplikasi: Data NLTK

Saat aplikasi pertamakali diluncurkan, akan ada proses unduh NLTK yang diperlukan (punkt, stopwords, wordnet, punkt_tab). Pastikan koneksi internet aktif. Jika jaringan Anda
memblokir unduhan, Anda bisa mengunduh terlebih dahulu melalui Python:

```
python -c "import nltk; [nltk.download(p, quiet=True) for p in ['punkt','stopwords','wordnet','punkt_tab']]"
```

## Cara Menggunakan Aplikasi

1) Unggah data

- Gunakan sidebar untuk mengunggah satu atau lebih file CSV.
- Setelah unggah, pilih dataset aktif lalu klik “Buka Dataset”.

2) Pilih bahasa dan kolom

- Pilih bahasa: Bahasa Indonesia atau English.
- Pilih kolom teks yang akan diproses.

3) Konfigurasi pipeline prapemrosesan

- Case folding, tokenisasi, normalisasi (menggunakan `kamuskatabaku.xlsx` jika tersedia), penghapusan stopword, stemming (ID) atau lemmatization (EN).

4) Jalankan dan tinjau

- Klik tombol pemrosesan untuk menghasilkan kolom-kolom baru yang berisi hasil antara dan hasil akhir.
- Unduh data yang telah diproses sebagai CSV bila diperlukan.

5) Visualisasi

- Buka tab Visualisasi untuk melihat bar frekuensi kata dan word cloud untuk teks mentah maupun hasil proses.

## Berkas Proyek

- `app.py` — entry point aplikasi Streamlit
- `preprocessing_logic.py` — fungsi prapemrosesan teks dan utilitas NLTK/Sastrawi
- `visualization_logic.py` — helper untuk frekuensi kata dan word cloud
- `kamuskatabaku.xlsx` — kamus opsional untuk normalisasi kata tidak baku ke kata baku (Bahasa Indonesia)
- `pyproject.toml`, `uv.lock` — definisi dependensi
- `nltk.txt` — catatan opsional terkait data NLTK (jika ada)

## Pemecahan Masalah (Troubleshooting)

- Streamlit tidak ditemukan: pastikan environment uv aktif dan dependensi terpasang (`uv sync`).
- Gagal unduh NLTK: jalankan perintah pra-unduh di atas, atau pastikan firewall/proxy mengizinkan unduhan.
- Masalah Sastrawi (stemming Bahasa Indonesia): pastikan paket terpasang (mis. `uv add sastrawi`).
- Masalah font WordCloud atau matplotlib: coba instal font tambahan atau tambahkan Pillow jika belum ada (mis. `uv add pillow`).
- Port sudah digunakan: jalankan dengan port lain, mis. `uv run streamlit run app.py --server.port 8502`.

## Ringkas Perintah (Windows PowerShell)

- Menggunakan uv: `uv run streamlit run app.py`
