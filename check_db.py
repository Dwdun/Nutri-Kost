import sqlite3
import os

db_path = r'c:\Users\Faqih sh\OneDrive\Dokumen\NutriKos\Nutri-Kost\bima_scrapper\nutrikost.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print('bima_scrapper/nutrikost.db Tables:', cur.fetchall())
