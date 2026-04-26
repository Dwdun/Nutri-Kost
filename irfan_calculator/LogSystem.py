import os
import sqlite3

class LogSystem:
    def __init__(self, db_name="nutrikost.db"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Go up one level, then into the target folder
        # Change "bima_scrapper" if your folder name is different
        db_path = os.path.join(base_dir, "..", "bima_scrapper", db_name)
        db_path = os.path.abspath(db_path)

        # CHECK BEFORE CONNECTING
        if not os.path.exists(db_path):
            print(f"CRITICAL ERROR: Database file missing at {db_path}")
            # This stops the app immediately with a clear message 
            # instead of letting it create an empty file.
            raise FileNotFoundError(f"Could not find the database at {db_path}")

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_table_log()
        self._create_table_makanan()
        
    def _create_table_log(self):
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

    def _create_table_makanan(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Makanan (
                code TEXT PRIMARY KEY,
                food_name TEXT,
                cal REAL,
                protein REAL,
                carb REAL,
                fat REAL
            )
        ''')
        self.conn.commit()

    # --- CREATE ---
    def CreateLog(self, food_code, porsi, waktu_makan, tanggal):
        query = """
            INSERT INTO LogHarian (food_code, porsi, waktu_makan, tanggal)
            VALUES (?, ?, ?, ?)
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (food_code, porsi, waktu_makan, tanggal))
        self.conn.commit()

    # --- READ ---
    def ReadLog(self):
        query = """
            SELECT 
                l.id as log_id,
                l.food_code,
                m.food_name,
                l.porsi,
                l.waktu_makan,
                ROUND(m.cal * (l.porsi / 100.0), 2) as cal,
                ROUND(m.protein * (l.porsi / 100.0), 2) as protein,
                ROUND(m.carb * (l.porsi / 100.0), 2) as carb,
                ROUND(m.fat * (l.porsi / 100.0), 2) as fat
            FROM LogHarian l
            JOIN Makanan m ON l.food_code = m.code
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    # --- UPDATE ---
    def UpdateLog(self, log_id: int, food_code: str, porsi: float, waktu_makan: str, tanggal: str):
        query = """
            UPDATE LogHarian 
            SET food_code = ?, porsi = ?, waktu_makan = ?, tanggal = ?
            WHERE id = ?
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (food_code, porsi, waktu_makan, tanggal, log_id))
        self.conn.commit()

    # --- DELETE ---
    def DeleteLog(self, log_id):
        query = "DELETE FROM LogHarian WHERE id = ?"
        cursor = self.conn.cursor()
        cursor.execute(query, (log_id,))
        self.conn.commit()

    # --- GET ALL FOODS ---
    def GetAllFoods(self):
        query = "SELECT * FROM Makanan"
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    # --- NUTRITION CALC ---
    def kalkulator_nutrisi(self, code, porsi_user):
        query = "SELECT * FROM Makanan WHERE code = ?"
        cursor = self.conn.cursor()
        cursor.execute(query, (code,))
        makanan = cursor.fetchone()

        if not makanan:
            return None

        multiplier = porsi_user / 100.0

        return {
            "cal": round(makanan["cal"] * multiplier, 2),
            "protein": round(makanan["protein"] * multiplier, 2),
            "carb": round(makanan["carb"] * multiplier, 2),
            "fat": round(makanan["fat"] * multiplier, 2),
        }