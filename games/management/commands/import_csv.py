# games/management/commands/import_csv.py - VERSI FINAL

import csv
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from games.models import Game, Genre, Platform, Publisher, Tag

class Command(BaseCommand):
    help = 'Updates or creates game data from a CSV file into the database'

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'games_with_images.csv')
        self.stdout.write(self.style.SUCCESS(f'Membaca data dari {file_path}...'))

        try:
            with open(file_path, 'r', encoding='latin-1') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Baris ini akan mencetak semua nama kolom yang terdeteksi
                # Cek di terminal apakah 'ImageURL' ada di daftar ini & tidak ada spasi
                self.stdout.write(f"Header yang terdeteksi: {reader.fieldnames}")

                for row_number, row in enumerate(reader, 1):
                    game_name = row.get('Name')
                    if not game_name or not game_name.strip():
                        self.stdout.write(self.style.WARNING(f'Melewatkan baris ke-{row_number} karena nama game kosong.'))
                        continue

                    # Menggunakan update_or_create untuk memperbarui data yang sudah ada
                    game_obj, created = Game.objects.update_or_create(
                        name=game_name.strip(),
                        defaults={
                            'released': row.get('Released') or None,
                            'rating': float(row.get('Rating')) if row.get('Rating') else 0.0,
                            'metacritic': int(row.get('Metacritic')) if row.get('Metacritic') else 0,
                            'description': row.get('Description', ''),
                            'cover_image_url': row.get('ImageURL', '').strip() or None,
                            'esrb': row.get('ESRB', '').strip() or None,
                        }
                    )

                    # Bagian ini hanya perlu dijalankan jika entri baru dibuat
                    if created:
                        for model, field, key in [
                            (Genre, game_obj.genres, 'Genres'),
                            (Platform, game_obj.platforms, 'Platforms'),
                            (Publisher, game_obj.publishers, 'Publishers'),
                            (Tag, game_obj.tags, 'Tags')
                        ]:
                            if row.get(key):
                                item_names = [name.strip() for name in row[key].split(',') if name.strip()]
                                for name in item_names:
                                    item, _ = model.objects.get_or_create(name=name)
                                    field.add(item)

                    status = "dibuat" if created else "diperbarui"
                    self.stdout.write(self.style.SUCCESS(f"Berhasil memproses ({status}): {game_obj.name}"))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File {file_path} tidak ditemukan.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Terjadi error: {e}'))