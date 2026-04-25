import sqlite3

class LogSystem:
    def __init__(self, db_name="nutrisi.db"):
        self.conn = sqlite3.connect(db_name)
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

        # dummy data if empty
        cursor.execute("SELECT COUNT(*) FROM Makanan")
        if cursor.fetchone()[0] == 0:
            data = [
                ("NP", "Nasi Putih", 260, 4.8, 57, 0.4),
                ("TG", "Telur Goreng", 92, 6.3, 0.4, 7.2),
                ("AB", "Ayam Bakar", 280, 31.2, 0, 16)
            ]
            cursor.executemany("INSERT INTO Makanan VALUES (?,?,?,?,?,?)", data)

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
                m.food_name,
                l.porsi,
                l.waktu_makan,
                m.cal, m.protein, m.carb, m.fat
            FROM LogHarian l
            JOIN Makanan m ON l.food_code = m.code
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
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