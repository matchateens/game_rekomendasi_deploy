# Game Recommender System
![CI](https://github.com/matchateens/game-recommender-system/actions/workflows/django.yml/badge.svg?branch=master)

Sistem rekomendasi game menggunakan machine learning dengan antarmuka Streamlit.

## Fitur

- Pencarian game
- Rekomendasi berdasarkan:
  - Content-based filtering
  - Cluster-based filtering
  - Hybrid filtering
- Visualisasi data game
- Filter berdasarkan rating, genre, dan platform

## Cara Menjalankan Aplikasi Secara Lokal

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Jalankan aplikasi:
```bash
streamlit run streamlit_app.py
```

## Deploy ke Streamlit Cloud

1. Buat akun di [Streamlit Cloud](https://streamlit.io/cloud)
2. Hubungkan dengan repository GitHub Anda
3. Deploy aplikasi dengan langkah berikut:
   - Klik "New app"
   - Pilih repository dan branch
   - Pilih file: streamlit_app.py
   - Klik "Deploy"

## Dataset

File `games.csv` berisi data game dengan kolom:
- Name: Nama game
- Rating: Rating game (0-5)
- Genres: Genre game
- Platforms: Platform yang didukung
- ESRB: Rating konten game

## Struktur Kode

- `streamlit_app.py`: File utama aplikasi Streamlit
- `requirements.txt`: Daftar package Python yang diperlukan
- `games.csv`: Dataset game

## Teknologi yang Digunakan

- Python 3.9+
- Streamlit
- Pandas
- Scikit-learn
- NumPy
- Plotly
- Seaborn
- Matplotlib
