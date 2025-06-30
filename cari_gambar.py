# Versi baru cari_gambar.py yang lebih cerdas

import requests
import csv
import time
import os

# --- GANTI DENGAN API KEY ANDA ---
API_KEY = "ead7e838d51f4f5987a7427e8883e185"
# ---------------------------------

# Nama file input dan output
INPUT_CSV = 'games.csv'
OUTPUT_CSV = 'games_with_images.csv'

# Header untuk file CSV baru
# Pastikan header ini sesuai dengan kolom di file games.csv Anda + ImageURL
new_headers = ['Name', 'Released', 'ESRB', 'Rating', 'Genres', 'Platforms', 'Metacritic', 'Publishers', 'Tags', 'Description', 'ImageURL']

# Header untuk request ke API, ini praktik yang baik
http_headers = {
    'User-Agent': 'VideogamesBrowserProject/1.0'
}

# Cek apakah file input ada
if not os.path.exists(INPUT_CSV):
    print(f"Error: File input '{INPUT_CSV}' tidak ditemukan.")
    exit()

try:
    # Buka file output untuk ditulis
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=new_headers, extrasaction='ignore')
        writer.writeheader()

        # Buka file input untuk dibaca
        with open(INPUT_CSV, 'r', encoding='latin-1') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                game_name = row.get('Name')
                if not game_name or not game_name.strip():
                    continue

                print(f"Mencari gambar untuk: {game_name}...")
                image_url = "" # Reset image_url untuk setiap game

                try:
                    # Buat request ke API RAWG
                    response = requests.get(
                        "https://api.rawg.io/api/games",
                        headers=http_headers,
                        params={'key': API_KEY, 'search': game_name, 'page_size': 5} # Ambil 5 hasil untuk dicari
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Cek jika ada error dari API, misal API Key salah
                    if data.get('error'):
                        print(f"  -> Error dari API: {data['error']}")
                        break # Hentikan skrip jika API key salah

                    # Loop melalui hasil pencarian untuk menemukan gambar pertama yang valid
                    if data.get('results'):
                        for result in data['results']:
                            if result.get('background_image'):
                                image_url = result['background_image']
                                print(f"  -> Gambar ditemukan!")
                                break # Hentikan loop jika gambar sudah ditemukan
                    
                    if not image_url:
                         print("  -> Gambar tidak ditemukan di semua hasil.")

                except requests.exceptions.RequestException as e:
                    print(f"  -> Terjadi error request: {e}")
                
                # Tulis baris baru ke file output, bahkan jika image_url kosong
                row['ImageURL'] = image_url
                writer.writerow(row)
                
                # Beri jeda sedikit agar tidak membebani API
                time.sleep(0.5) 

    print(f"\nProses selesai! Data baru disimpan di {OUTPUT_CSV}")

except Exception as e:
    print(f"Terjadi error tak terduga: {e}")