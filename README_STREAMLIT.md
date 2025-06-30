# 🎮 Game Recommender System - Streamlit Deployment

Sistem rekomendasi game menggunakan Machine Learning dengan K-Means Clustering dan Content-Based Filtering.

## 📋 Files yang Diperlukan untuk Deployment Streamlit

### File Utama:
1. **`streamlit_app.py`** - Aplikasi Streamlit utama
2. **`games.csv`** - Dataset game (wajib ada)
3. **`requirements_streamlit.txt`** - Dependencies untuk Streamlit

### File Opsional:
- **`README_STREAMLIT.md`** - Dokumentasi deployment
- **`.streamlit/config.toml`** - Konfigurasi Streamlit (opsional)

## 🚀 Cara Deploy di Streamlit Cloud

### 1. Persiapan Repository
```bash
# Upload files ke GitHub repository
git add streamlit_app.py games.csv requirements_streamlit.txt
git commit -m "Add Streamlit app for deployment"
git push origin main
```

### 2. Deploy di Streamlit Cloud
1. Buka [share.streamlit.io](https://share.streamlit.io)
2. Login dengan GitHub
3. Klik "New app"
4. Pilih repository Anda
5. Set:
   - **Main file path**: `streamlit_app.py`
   - **Requirements file**: `requirements_streamlit.txt`
6. Klik "Deploy!"

### 3. Deploy di Platform Lain

#### Heroku:
```bash
# Tambahkan Procfile
echo "web: streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0" > Procfile
```

#### Railway/Render:
- Upload semua file yang diperlukan
- Set start command: `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`

## 📁 Struktur File untuk Upload

```
your-repo/
├── streamlit_app.py          # ✅ WAJIB - Aplikasi utama
├── games.csv                 # ✅ WAJIB - Dataset
├── requirements_streamlit.txt # ✅ WAJIB - Dependencies
├── README_STREAMLIT.md       # ⚪ Opsional - Dokumentasi
└── .streamlit/
    └── config.toml           # ⚪ Opsional - Konfigurasi
```

## 🔧 Fitur Aplikasi

### Machine Learning Features:
- **K-Means Clustering**: Mengelompokkan game berdasarkan karakteristik
- **Content-Based Filtering**: Rekomendasi berdasarkan kesamaan konten
- **Hybrid Approach**: Kombinasi clustering dan content-based

### User Interface:
- **Game Search**: Pencarian game dengan autocomplete
- **Multiple Recommendation Types**: Content-based, Cluster-based, Hybrid
- **Interactive Metrics**: Silhouette score, jumlah cluster, dll
- **Dataset Visualization**: Distribusi genre dan rating

### Performance:
- **Caching**: Streamlit caching untuk performa optimal
- **Real-time Processing**: Rekomendasi dihasilkan secara real-time
- **Responsive Design**: UI yang responsif dan user-friendly

## 📊 Dataset Requirements

File `games.csv` harus memiliki kolom:
- `Name`: Nama game
- `Rating`: Rating game (0-5)
- `Genres`: Genre game (dipisah koma)
- `Platforms`: Platform game (dipisah koma)
- `ESRB_Rating`: Rating ESRB

## 🛠️ Local Testing

```bash
# Install dependencies
pip install -r requirements_streamlit.txt

# Run aplikasi
streamlit run streamlit_app.py
```

## 📝 Notes

1. **File Size Limit**: Pastikan `games.csv` < 100MB untuk Streamlit Cloud
2. **Memory Usage**: Aplikasi dioptimalkan untuk memory usage minimal
3. **Loading Time**: First load mungkin butuh waktu untuk training model
4. **Browser Compatibility**: Tested di Chrome, Firefox, Safari

## 🔗 Demo

Setelah deploy, aplikasi akan tersedia di:
- Streamlit Cloud: `https://[your-app-name].streamlit.app`
- Custom domain (jika dikonfigurasi)

## 🆘 Troubleshooting

### Error "File not found":
- Pastikan `games.csv` ada di root directory
- Check case-sensitive filename

### Memory Error:
- Reduce dataset size jika terlalu besar
- Optimize pandas operations

### Slow Loading:
- Enable Streamlit caching
- Reduce number of clusters jika perlu

## 📞 Support

Jika ada masalah deployment, check:
1. Streamlit logs di dashboard
2. Requirements compatibility
3. File permissions dan structure
