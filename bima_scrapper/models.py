import sqlite3
import json
import os
import sys
import re
from thefuzz import process

# ==========================================
# KAMUS KONVERSI
# ==========================================
KONVERSI_GRAM = {
    'sdm': 15,     # 1 Sendok makan = ~15 gram
    'sdt': 5,      # 1 Sendok teh = ~5 gram
    'siung': 5,    # 1 Siung bawang = ~5 gram
    'ekor': 80,    # 1 Ekor ikan rata-rata = ~80 gram
    'genggam': 40,
    'pcs': 50,
    'buah': 100,
    'gram': 1,
    'gr': 1,
    'liter': 1000, 
    'ml': 1,
    'lembar': 3, 
    'ikat': 50, 
    'batang': 15
}

def kalkulasi_nutrisi_bahan(teks_bahan, db_makanan_dict):
    """Mencocokkan bahan resep dengan database dan menghitung nutrisinya"""
    match = re.search(r'([\d\./]+)\s*([a-zA-Z]+)\s*(.*)', teks_bahan)
    
    if not match:
        return None 

    try:
        kuantitas_str = match.group(1).replace('/', '.0/') if '/' in match.group(1) else match.group(1)
        kuantitas = float(eval(kuantitas_str))
    except Exception:
        return None

    satuan = match.group(2).lower()
    nama_bahan = match.group(3).strip()

    list_nama_db = list(db_makanan_dict.keys())
    kecocokan = process.extractOne(nama_bahan, list_nama_db)
    
    if kecocokan and kecocokan[1] >= 70: 
        nama_db = kecocokan[0]
        data_nutrisi = db_makanan_dict[nama_db]
        
        pengali_gram = KONVERSI_GRAM.get(satuan, 50) 
        berat_total = kuantitas * pengali_gram
        
        # Mendukung dictionary dari DBHelper
        kalori = float(data_nutrisi['cal'] if isinstance(data_nutrisi, dict) else data_nutrisi[2])
        protein = float(data_nutrisi['protein'] if isinstance(data_nutrisi, dict) else data_nutrisi[3])
        karbo = float(data_nutrisi['carb'] if isinstance(data_nutrisi, dict) else data_nutrisi[4])
        lemak = float(data_nutrisi['fat'] if isinstance(data_nutrisi, dict) else data_nutrisi[5])

        return {
            'nama_asli': teks_bahan,
            'nama_db': nama_db,
            'berat_g': round(berat_total, 1),
            'kalori': round((berat_total / 100) * kalori, 1),
            'protein': round((berat_total / 100) * protein, 1),
            'karbo': round((berat_total / 100) * karbo, 1),
            'lemak': round((berat_total / 100) * lemak, 1)
        }
    return None

class DBHelper:
    def __init__(self, db_name='nutrikost.db'):
        # Saat dikemas sebagai .exe, __file__ menunjuk ke folder temp (read-only).
        # Kita harus menyimpan database di folder yang bisa ditulis:
        #   - mode .exe  → folder sejajar executable
        #   - mode dev   → folder models.py (bima_scrapper/)
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        db_dir = os.path.join(base, 'bima_scrapper') if getattr(sys, 'frozen', False) else base
        os.makedirs(db_dir, exist_ok=True)
        self.db_path = os.path.join(db_dir, db_name)

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # ==========================================
    # CRUD: PROFIL USER
    # ==========================================
    def create_user(self, user_data_dict):
        conn = self._get_connection()
        cursor = conn.cursor()
        columns = ', '.join(user_data_dict.keys())
        placeholders = ', '.join(['?'] * len(user_data_dict))
        values = tuple(user_data_dict.values())
        query = f"INSERT INTO ProfilUser ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def get_user_by_id(self, id_user):
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM ProfilUser WHERE id_user = ?", (id_user,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_users(self):
        """Mengambil semua data user dari database."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM ProfilUser")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_user(self, id_user, update_dict):
        conn = self._get_connection()
        cursor = conn.cursor()
        set_clause = ', '.join([f"{key} = ?" for key in update_dict.keys()])
        values = list(update_dict.values())
        values.append(id_user)
        query = f"UPDATE ProfilUser SET {set_clause} WHERE id_user = ?"
        cursor.execute(query, tuple(values))
        conn.commit()
        conn.close()
        return True

    def delete_user(self, id_user):
        conn = self._get_connection()
        conn.execute("DELETE FROM ProfilUser WHERE id_user = ?", (id_user,))
        conn.commit()
        conn.close()
        return True

    # ==========================================
    # BACA DATA: MAKANAN (MASTER)
    # ==========================================
    def search_makanan(self, keyword):
        conn = self._get_connection()
        search_term = f"%{keyword}%"
        cursor = conn.execute("SELECT * FROM Makanan WHERE food_name LIKE ?", (search_term,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_makanan_by_code(self, code):
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM Makanan WHERE code = ?", (code,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_makanan(self):
        """Mengambil semua data makanan (katalog lengkap)."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM Makanan")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # ==========================================
    # PAGINATION HELPER
    # ==========================================
    def get_all_makanan_paginated(self, page=1, per_page=10):
        offset = (page - 1) * per_page

        conn = self._get_connection()
        
        cursor_total = conn.execute("SELECT COUNT(*) FROM Makanan")
        total_items = cursor_total.fetchone()[0]

        query = "SELECT * FROM Makanan LIMIT ? OFFSET ?"
        cursor = conn.execute(query, (per_page, offset))
        rows = cursor.fetchall()
        conn.close()

        start_item = offset + 1 if total_items > 0 else 0
        end_item = offset + len(rows)
        
        total_pages = (total_items + per_page - 1) // per_page

        return {
            "data": [dict(row) for row in rows],
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total_items": total_items,
                "total_pages": total_pages,
                "showing_start": start_item, # Menampilkan dari nomor urut sekian
                "showing_end": end_item      # Sampai nomor urut sekian
            }
        }

    # ==========================================
    # CRUD: LOG HARIAN (MEAL LOG)
    # ==========================================
    def add_meal_log(self, log_dict):
        conn = self._get_connection()
        cursor = conn.cursor()
        columns = ', '.join(log_dict.keys())
        placeholders = ', '.join(['?'] * len(log_dict))
        values = tuple(log_dict.values())
        query = f"INSERT INTO LogHarian ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        return True

    def get_log_by_date(self, id_user, date_string):
        conn = self._get_connection()
        query = """
            SELECT l.*, m.food_name 
            FROM LogHarian l
            JOIN Makanan m ON l.kode_makanan = m.code
            WHERE l.id_user = ? AND date(l.meal_time) = ?
        """
        cursor = conn.execute(query, (id_user, date_string))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_all_logs(self, limit=100):
        """
        Mengambil semua data log harian dari semua user.
        Dilengkapi dengan limit agar aplikasi tidak hang jika data sudah jutaan.
        """
        conn = self._get_connection()
        query = """
            SELECT l.*, p.full_name, m.food_name 
            FROM LogHarian l
            LEFT JOIN ProfilUser p ON l.id_user = p.id_user
            LEFT JOIN Makanan m ON l.kode_makanan = m.code
            ORDER BY l.meal_time DESC
            LIMIT ?
        """
        cursor = conn.execute(query, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_daily_summary(self, id_user, date_string):
        conn = self._get_connection()
        query = """
            SELECT 
                SUM(cal) as total_cal,
                SUM(protein) as total_protein,
                SUM(carb) as total_carb,
                SUM(fat) as total_fat
            FROM LogHarian 
            WHERE id_user = ? AND date(meal_time) = ?
        """
        cursor = conn.execute(query, (id_user, date_string))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else {'total_cal': 0, 'total_protein': 0, 'total_carb': 0, 'total_fat': 0}

    # ==========================================
    # OPERASI CACHE RESEP & INSERT MAKANAN
    # ==========================================
    def init_cache_table(self):
        conn = self._get_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS CacheResep (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_makanan TEXT UNIQUE,
                data_json_bahan TEXT,
                cal     REAL,
                protein REAL,
                carb    REAL,
                fat     REAL
            )
        ''')
        # Migrasi: tambah kolom nutrisi jika tabel lama belum punya
        kolom_baru = {'cal': 'REAL', 'protein': 'REAL', 'carb': 'REAL', 'fat': 'REAL', 'status': 'INTEGER DEFAULT 1'}
        kolom_ada = {row[1] for row in conn.execute("PRAGMA table_info(CacheResep)")}
        for nama_kolom, tipe in kolom_baru.items():
            if nama_kolom not in kolom_ada:
                conn.execute(f"ALTER TABLE CacheResep ADD COLUMN {nama_kolom} {tipe}")
        conn.commit()
        conn.close()

    def get_all_cache_names(self):
        conn = self._get_connection()
        cursor = conn.execute("SELECT nama_makanan FROM CacheResep")
        rows = cursor.fetchall()
        conn.close()
        return [row['nama_makanan'] for row in rows]

    def get_cache_by_name(self, nama_makanan):
        conn = self._get_connection()
        cursor = conn.execute("SELECT data_json_bahan FROM CacheResep WHERE nama_makanan = ?", (nama_makanan,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def insert_cache_resep(self, nama_makanan, data_json_bahan):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO CacheResep (nama_makanan, data_json_bahan) VALUES (?, ?)", 
                (nama_makanan, data_json_bahan)
            )
            conn.commit()
            success = True
        except sqlite3.IntegrityError:
            success = False
        conn.close()
        return success

    def insert_makanan(self, code, food_name, water, cal, protein, fat, carb, fiber):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO Makanan (code, food_name, water, cal, protein, fat, carb, fiber)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (code, food_name, water, cal, protein, fat, carb, fiber))
            conn.commit()
            success = True
        except sqlite3.IntegrityError:
            success = False
        conn.close()
        return success

    def accept_cache_to_makanan(self, nama_makanan, cal, protein, carb, fat):
        """
        Pindahkan satu entri CacheResep ke tabel Makanan dengan kode unik.
        Mengembalikan (success: bool, code: str, pesan: str).
        """
        import uuid
        # Format kode: CR-XXXXXXXX (8 hex acak, huruf besar)
        unique_code = "CR-" + uuid.uuid4().hex[:8].upper()

        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''INSERT INTO Makanan (code, food_name, water, cal, protein, fat, carb, fiber)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (unique_code, nama_makanan.title(), 0.0,
                 round(cal, 2), round(protein, 2), round(fat, 2), round(carb, 2), 0.0)
            )
            cursor.execute(
                "UPDATE CacheResep SET status = 2 WHERE LOWER(nama_makanan) = LOWER(?)",
                (nama_makanan,)
            )
            conn.commit()
            conn.close()
            return True, unique_code, f"'{nama_makanan.title()}' berhasil ditambahkan dengan kode {unique_code}."
        except sqlite3.IntegrityError:
            conn.close()
            return False, "", f"'{nama_makanan.title()}' sudah ada di tabel Makanan."
        except Exception as e:
            conn.close()
            return False, "", f"Gagal menyimpan: {e}"
            
    def decline_cache(self, nama_makanan):
        """Menolak request makanan (set status = 3)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE CacheResep SET status = 3 WHERE LOWER(nama_makanan) = LOWER(?)",
                (nama_makanan,)
            )
            conn.commit()
            conn.close()
            return True, f"'{nama_makanan.title()}' berhasil ditolak."
        except Exception as e:
            conn.close()
            return False, f"Gagal menolak: {e}"
    

    def get_all_requests(self):
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM request_makanan")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]


class JsonHelper:
    def __init__(self):
        # Saat dikemas .exe, JSON dibundel di _MEIPASS/bima_scrapper/
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.join(sys._MEIPASS, 'bima_scrapper')
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def _read_json(self, filename):
        file_path = os.path.join(self.base_dir, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def get_akg(self):
        return self._read_json('akg.json')

    def get_food_facts(self):
        return self._read_json('FoodFact.json')

    def get_resep_harian(self):
        return self._read_json('Resep.json')