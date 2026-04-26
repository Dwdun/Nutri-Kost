import sqlite3
import json
import os
import re
from thefuzz import process

KONVERSI_GRAM = {
    'sdm': 15,     # 1 Sendok makan = ~15 gram
    'sdt': 5,      # 1 Sendok teh = ~5 gram
    'siung': 5,    # 1 Siung bawang = ~5 gram
    'ekor': 80,    # 1 Ekor ikan rata-rata = ~80 gram
    'genggam': 40,
    'pcs': 50,
    'buah': 100,
    'gram': 1,
    'gr': 1
}



class DBHelper:
    def __init__(self, db_name='nutrikost.db'):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name)

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


class JsonHelper:
    def __init__(self):
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
        return self._read_json('resep.json')
    
    def hitung_nutrisi_bahan(teks_bahan_resep, conn):
        cursor = conn.cursor()
    
        cursor.execute("SELECT code, food_name, cal, protein, carb, fat FROM Makanan")
        db_makanan = cursor.fetchall()
    
        nama_makanan_db = {row[1]: row for row in db_makanan} 

        match = re.search(r'([\d\./]+)\s*([a-zA-Z]+)\s*(.*)', teks_bahan_resep)
        
        if match:
            kuantitas = float(eval(match.group(1).replace('/', '.0/')))
            satuan = match.group(2).lower()
            nama_bahan_mentah = match.group(3).strip()
        else:
            return None 
        
        list_nama_db = list(nama_makanan_db.keys())
        kecocokan_terbaik = process.extractOne(nama_bahan_mentah, list_nama_db)
        
        if kecocokan_terbaik and kecocokan_terbaik[1] >= 75:
            nama_ditemukan = kecocokan_terbaik[0]
            data_nutrisi = nama_makanan_db[nama_ditemukan] 
            
            pengali_gram = KONVERSI_GRAM.get(satuan, 100)
            total_berat_gram = kuantitas * pengali_gram
            
            hasil_kalkulasi = {
                'nama_asli_resep': teks_bahan_resep,
                'dikenali_sebagai': nama_ditemukan,
                'berat_estimasi_gram': total_berat_gram,
                'kalori': round((total_berat_gram / 100) * float(data_nutrisi[2]), 2),
                'protein': round((total_berat_gram / 100) * float(data_nutrisi[3]), 2),
                'karbohidrat': round((total_berat_gram / 100) * float(data_nutrisi[4]), 2),
                'lemak': round((total_berat_gram / 100) * float(data_nutrisi[5]), 2),
            }
            return hasil_kalkulasi
        else:
            return None