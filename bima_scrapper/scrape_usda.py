import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import os

def clean_number(text):
    """Membersihkan format angka Indonesia (koma) menjadi standar (titik)."""
    if not text or text.strip() == '-' or text.strip() == '':
        return 0.0
    cleaned = text.strip().replace('.', '').replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def scrape_and_save_usda():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'nutrikost.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Makanan (
          code TEXT PRIMARY KEY,
          food_name TEXT,
          water REAL,
          cal REAL,
          protein REAL,
          fat REAL,
          carb REAL,
          fiber REAL
        )
    ''')
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    total_saved = 0
    page = 1
    
    print("=== Memulai Scraping Data USDA ===")
    
    while True:
        if page == 1:
            url = "https://www.andrafarm.com/_andra.php?_i=daftar-usda"
        else:
            no1 = (page - 2) * 40 + 1
            no2 = (page - 1) * 40
            url = f"https://www.andrafarm.com/_andra.php?_i=daftar-usda&jobs=&perhal=40&urut=1&asc=0000000000&sby=&no1={no1}&no2={no2}&kk={page}#Tabel%20USDA"

        print(f"\n[+] Mengambil Halaman {page}...")
        
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            table = soup.find('table', class_='adrtabel2')
            if not table:
                print(f"[-] Tabel tidak ditemukan di halaman {page}. Pencarian mencapai akhir halaman.")
                break

            rows = table.find_all('tr')
            page_count = 0
            
            for row in rows:
                if row.get('align') == 'center':
                    cols = row.find_all('td')
                    
                    if len(cols) >= 9:
                        code = cols[1].get_text(strip=True)
                        if not code or code.lower() == 'kode':
                            continue
                            
                        name_tag = cols[2].find('a')
                        name = name_tag.get_text(strip=True) if name_tag else cols[2].get_text(strip=True)
                        
                        water   = clean_number(cols[3].get_text(strip=True))
                        cal     = clean_number(cols[4].get_text(strip=True))
                        protein = clean_number(cols[5].get_text(strip=True))
                        fat     = clean_number(cols[6].get_text(strip=True))
                        carb    = clean_number(cols[7].get_text(strip=True))
                        fiber   = clean_number(cols[8].get_text(strip=True))

                        try:
                            cursor.execute('''
                                INSERT OR REPLACE INTO Makanan (code, food_name, water, cal, protein, fat, carb, fiber)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (code, name, water, cal, protein, fat, carb, fiber))
                            
                            page_count += 1
                            total_saved += 1
                        except sqlite3.Error as e:
                            print(f"DB Error pada {code}: {e}")

            conn.commit()
            
            if page_count == 0:
                print(f"[-] Tidak ada data baru di halaman {page}. Proses scraping selesai.")
                break
                
            print(f"[v] Halaman {page} selesai. {page_count} makanan ditambahkan. (Total sementara: {total_saved})")
            
            page += 1
            time.sleep(2)
            
        except Exception as e:
            print(f"[!] Error koneksi/parsing saat mengakses halaman {page}: {e}")
            break
            
    conn.close()
    print(f"\n=== SCRAPING USDA SELESAI! Total {total_saved} data makanan berhasil disimpan ke database. ===")

if __name__ == '__main__':
    scrape_and_save_usda()