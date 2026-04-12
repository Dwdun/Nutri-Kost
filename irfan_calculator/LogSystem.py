import sqlite3

class DBHelper:
    def __init__(self, db_name="nutrisi.db"):
        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = sqlite3.Row 

    def _create_table_log(self):
        """Membuat tabel log jika belum ada"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS LogHarian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                food_code TEXT,
                porsi REAL,
                waktu_makan TEXT,
                tanggal TEXT,
                FOREIGN KEY (food_code) REFERENCES Makanan(code)
            )
        ''')
        self.conn.commit()

    # --- CREATE (C) ---
    def CreateLog(self, makanan_id: int, porsi: float, kategori_waktu: str, tanggal: str):
        """Menyimpan makanan yang dipilih ke log harian"""
        query = """
            INSERT INTO daily_logs (makanan_id, porsi, kategori_waktu, tanggal)
            VALUES (?, ?, ?, ?)
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (makanan_id, porsi, kategori_waktu, tanggal))
        self.conn.commit()

    # --- READ (R) ---
    def ReadLog(self):
        """Mengambil semua makanan yang dimakan HARI INI beserta detail nutrisinya"""
        query = """
            SELECT 
                l.id as log_id,
                m.food_name,
                m.cal, m.protein, m.carb, m.fat,
                l.serving_size,
                l.meal_time
            FROM daily_logs l
            JOIN makanan m ON l.food_id = m.id
            WHERE l.log_date = CURRENT_DATE
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    # --- UPDATE (U) ---
    def UpdateLog(self, log_id: int, new_porsi: float, new_waktu: str):
        """Mengubah porsi atau waktu makan pada log yang sudah ada"""
        query = """
            UPDATE daily_logs 
            SET serving_size = ?, meal_time = ? 
            WHERE id = ?
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (new_porsi, new_waktu, log_id))
        self.conn.commit()

    # --- DELETE (D) ---
    def DeleteLog(self, log_idx: int):
        """Menghapus entri log berdasarkan ID"""
        query = "DELETE FROM daily_logs WHERE id = ?"
        cursor = self.conn.cursor()
        cursor.execute(query, (log_idx,))
        self.conn.commit()

    def kalkulator_nutrisi(self, code: str, porsi_user: float):
        query = "SELECT * FROM Makanan WHERE code = ?"
        cursor = self.conn.cursor()
        cursor.execute(query, (code,))
        makanan = cursor.fetchone()

        if not makanan:
            return None

        multiplier = porsi_user / 100.0

        return {
            "name": makanan["food_name"],
            "porsi": porsi_user,
            "cal": round(makanan["cal"] * multiplier, 2),
            "protein": round(makanan["protein"] * multiplier, 2),
            "fat": round(makanan["fat"] * multiplier, 2),
            "carb": round(makanan["carb"] * multiplier, 2),
            "fiber": round(makanan["fiber"] * multiplier, 2),
            "water": round(makanan["water"] * multiplier, 2)
        }

    