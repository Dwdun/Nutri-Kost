import sqlite3

class DBHelper:
    def __init__(self, db_name="nutrisi.db"):
        self.conn = sqlite3.connect(db_name)
        # Aktifkan factory agar hasil query berbentuk dictionary (memudahkan UI)
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

    

    