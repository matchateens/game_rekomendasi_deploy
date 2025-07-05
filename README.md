# 🎮 Game Recommender System (Django)
![CI](https://github.com/matchateens/game_rekomendasi_deploy/actions/workflows/django.yml/badge.svg?branch=master)
Sistem rekomendasi game berbasis Django dengan personalisasi berdasarkan interaksi pengguna. Menggunakan hybrid recommendation engine (content-based + collaborative filtering) dan UI yang ramah pengguna.

🚀 Dideploy di **Google Cloud Platform** menggunakan:
- Google Compute Engine (VM Instance)
- Gunicorn sebagai WSGI server
- Nginx sebagai reverse proxy

---

## 🌐 Live Demo

👉 http://34.101.51.219  
⚠️ Saat ini masih menggunakan HTTP (belum SSL)

---

## 🖼️ Screenshot

Halaman rekomendasi dan eksplorasi game populer:

![Game Recommender Screenshot](https://raw.githubusercontent.com/matchateens/game_rekomendasi_deploy/assets/screenshot_home.png)

---

## 🔧 Teknologi yang Digunakan

- Python 3.9
- Django Framework
- Gunicorn (WSGI HTTP server)
- Nginx (reverse proxy)
- Google Compute Engine
- SQLite / PostgreSQL
- HTML + CSS (tanpa framework frontend berat)

---

## 📦 Fitur Utama

- 🔍 Pencarian game pintar dengan hybrid query
- 💡 Rekomendasi personal berdasarkan histori pengguna
- 📊 Eksplorasi berdasarkan genre, publisher, ESRB, dan rating
- 📌 Bookmark dan rating game
- 👤 Dashboard pengguna (riwayat, rekomendasi, statistik)
- 🎨 UI responsif dan ringan

---

## ⚙️ Langkah Deploy di Google Cloud Platform (GCE)

### 1. Buat VM Instance

- Gunakan OS: Ubuntu 20.04
- Tambahkan firewall rule untuk HTTP dan HTTPS
- Tambahkan IP static (opsional)

### 2. Update Server & Install Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx git -y
```

### 3. Clone Repository & Setup Environment

```bash
git clone https://github.com/matchateens/game_rekomendasi_deploy.git
cd game-recommender-system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Setup Django

```bash
python manage.py migrate
python manage.py collectstatic
```

> Sesuaikan `ALLOWED_HOSTS` di `config/settings.py`:
```python
ALLOWED_HOSTS = ['34.101.51.219']
```

### 5. Uji Gunicorn Secara Lokal

```bash
gunicorn --bind 0.0.0.0:8000 config.wsgi:application
```

Buka: `http://34.101.51.219:8000` → pastikan aplikasi tampil.

### 6. Setup Gunicorn sebagai systemd Service

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

```ini
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/home/youruser/game-recommender-system
ExecStart=/home/youruser/game-recommender-system/venv/bin/gunicorn --workers 3 --bind unix:/home/youruser/game-recommender-system/gunicorn.sock config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Aktifkan dan mulai Gunicorn:

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
```

### 7. Konfigurasi Nginx

```bash
sudo nano /etc/nginx/sites-available/game_recommender
```

```nginx
server {
    listen 80;
    server_name 34.101.51.219;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/youruser/game-recommender-system;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/youruser/game-recommender-system/gunicorn.sock;
    }
}
```

Aktifkan konfigurasi:

```bash
sudo ln -s /etc/nginx/sites-available/game_recommender /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

---

## 📂 Struktur Direktori

```bash
game-recommender-system/
├── config/
├── games/
├── static/
├── templates/
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🔌 API Endpoint

| Endpoint                    | Keterangan                      |
|----------------------------|----------------------------------|
| `/api/rate/`               | Submit rating game              |
| `/api/bookmark/`           | Bookmark game                   |
| `/api/recommendations/`    | Get rekomendasi user            |
| `/api/search-suggestions/` | Search autocomplete             |

---

## 🤝 Kontribusi

Pull Request dan kontribusi sangat disambut.

---

## 📄 Lisensi

MIT License — bebas digunakan untuk keperluan apapun dengan mencantumkan atribusi.

---

## ✨ Dibuat oleh

**Fatin Cahya Ramadhan**  
[GitHub](https://github.com/matchateens)
