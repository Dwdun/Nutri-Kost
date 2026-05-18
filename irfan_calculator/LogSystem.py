import os
import sqlite3

class LogSystem:
    def __init__(self, db_name="nutrikost.db"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "..", "bima_scrapper", db_name)
        db_path = os.path.abspath(db_path)

        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found at {db_path}")

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    # --- CREATE ---
    def CreateLog(self, id_user, kode_makanan, meal_time, portion, cal, protein, carb, fat, category):
        query = """
            INSERT INTO LogHarian 
            (id_user, kode_makanan, meal_time, portion, cal, protein, carb, fat, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (
            id_user, kode_makanan, meal_time, portion,
            cal, protein, carb, fat, category
        ))
        self.conn.commit()

    # --- READ ---
    def ReadLog(self, id_user=None):
        if id_user is not None:
            query = """
                SELECT 
                    l.id_log,
                    l.id_user,
                    l.kode_makanan,
                    m.food_name,
                    l.portion,
                    l.meal_time,
                    l.cal,
                    l.protein,
                    l.carb,
                    l.fat,
                    l.category
                FROM LogHarian l
                JOIN Makanan m ON l.kode_makanan = m.code
                WHERE l.id_user = ?
            """
            cursor = self.conn.cursor()
            cursor.execute(query, (id_user,))
        else:
            query = """
                SELECT 
                    l.id_log,
                    l.id_user,
                    l.kode_makanan,
                    m.food_name,
                    l.portion,
                    l.meal_time,
                    l.cal,
                    l.protein,
                    l.carb,
                    l.fat,
                    l.category
                FROM LogHarian l
                JOIN Makanan m ON l.kode_makanan = m.code
            """
            cursor = self.conn.cursor()
            cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    # --- UPDATE ---
    def UpdateLog(self, id_log, id_user, kode_makanan, meal_time, portion, cal, protein, carb, fat, category):
        query = """
            UPDATE LogHarian 
            SET id_user = ?, 
                kode_makanan = ?, 
                meal_time = ?, 
                portion = ?, 
                cal = ?, 
                protein = ?, 
                carb = ?, 
                fat = ?, 
                category = ?
            WHERE id_log = ?
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (
            id_user, kode_makanan, meal_time, portion,
            cal, protein, carb, fat, category, id_log
        ))
        self.conn.commit()

    # --- DELETE ---
    def DeleteLog(self, id_log):
        query = "DELETE FROM LogHarian WHERE id_log = ?"
        cursor = self.conn.cursor()
        cursor.execute(query, (id_log,))
        self.conn.commit()

    # --- GET ALL FOODS ---
    def GetAllFoods(self):
        query = "SELECT * FROM Makanan"
        cursor = self.conn.cursor()
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    # --- NUTRITION CALCULATOR ---
    def kalkulator_nutrisi(self, kode_makanan, portion_user):
        query = "SELECT * FROM Makanan WHERE code = ?"
        cursor = self.conn.cursor()
        cursor.execute(query, (kode_makanan,))
        makanan = cursor.fetchone()

        if not makanan:
            return None

        multiplier = portion_user / 100.0

        return {
            "cal": round(makanan["cal"] * multiplier, 2),
            "protein": round(makanan["protein"] * multiplier, 2),
            "carb": round(makanan["carb"] * multiplier, 2),
            "fat": round(makanan["fat"] * multiplier, 2),
        }