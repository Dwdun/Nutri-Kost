import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nutrikost.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Menghapus semua isi data di tabel CacheResep
cursor.execute("DELETE FROM CacheResep")

# 2. Mereset urutan ID (Auto Increment) kembali ke 1
cursor.execute("DELETE FROM sqlite_sequence WHERE name='CacheResep'")

conn.commit()
conn.close()

print("🧹 Tabel CacheResep berhasil dikosongkan!")