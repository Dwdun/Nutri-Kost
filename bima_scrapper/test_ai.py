import os
import sys
import json
import re
import sqlite3
import random
import google.generativeai as genai
from thefuzz import process

from models import DBHelper, KONVERSI_GRAM 

#Gemini
api_key = os.environ.get("GEMINI_API_KEY") or "AIzaSyBu5Ce7b1inSfAUJQFEblWqUMRu9uUIhzs"
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-flash-latest')

#cache makanan di db
def init_cache_table(db_name='nutrikost.db'):
    #cek tabel CacheResep
    db_path = DBHelper(db_name).db_path
    
    conn = sqlite3.connect(db_path)


    # Buat tabel dengan skema lengkap jika belum ada
    conn.execute('''
        CREATE TABLE IF NOT EXISTS CacheResep (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_makanan TEXT UNIQUE,
            data_json_bahan TEXT,
            cal     REAL,
            protein REAL,
            carb    REAL,
            fat     REAL,
            water   REAL,
            fiber   REAL
        )
    ''')

    # Migrasi: tambah kolom baru jika tabel lama belum punya kolom nutrisi
    kolom_baru = {
        'cal':     'REAL',
        'protein': 'REAL',
        'carb':    'REAL',
        'fat':     'REAL',
        'water':   'REAL',
        'fiber':   'REAL',
        'status':  'INTEGER DEFAULT 1',
    }
    kolom_ada = {row[1] for row in conn.execute("PRAGMA table_info(CacheResep)")}
    for nama_kolom, tipe in kolom_baru.items():
        if nama_kolom not in kolom_ada:
            conn.execute(f"ALTER TABLE CacheResep ADD COLUMN {nama_kolom} {tipe}")
            print(f"[🔧 MIGRASI] Kolom '{nama_kolom}' berhasil ditambahkan ke CacheResep.")

    conn.commit()
    conn.close()

def get_or_fetch_resep(nama_makanan_input):
    #Cek Nama makanan
    db_path = DBHelper('nutrikost.db').db_path
    conn = sqlite3.connect(db_path)

    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    #Ambil semua nama makanan yang pernah disimpan di Cache
    cursor.execute("SELECT nama_makanan FROM CacheResep")
    semua_cache = cursor.fetchall()
    daftar_nama_cache = [row['nama_makanan'] for row in semua_cache]

    #Cek apakah input user mirip dengan yang ada di Cache (Fuzzy Matching > 85%)
    if daftar_nama_cache:
        kecocokan, skor = process.extractOne(nama_makanan_input.lower(), daftar_nama_cache)
        
        if skor >= 85:
            print(f"\n[⚡ CACHE HIT] Menggunakan data lokal (Mirip dengan: '{kecocokan}' - Skor: {skor}%)")
            cursor.execute("SELECT data_json_bahan FROM CacheResep WHERE nama_makanan = ?", (kecocokan,))
            row = cursor.fetchone()
            conn.close()
            return json.loads(row['data_json_bahan'])

    #Jika tidak ada di Cache, panggil Gemini API
    print(f"\n[🤖 CACHE MISS] Meminta bantuan Gemini membongkar resep '{nama_makanan_input}'...")
    bahan_dari_ai = bongkar_resep_dengan_gemini(nama_makanan_input)

    # Simpan hasil AI ke CacheResep
    if bahan_dari_ai is not None:
        json_string = json.dumps(bahan_dari_ai)
        try:
            cursor.execute(
                "INSERT INTO CacheResep (nama_makanan, data_json_bahan, status) VALUES (?, ?, ?)", 
                (nama_makanan_input.lower(), json_string, 1)
            )
            conn.commit()
            print(f"[💾 SAVED] Resep '{nama_makanan_input}' berhasil disimpan ke memori lokal!")
        except sqlite3.IntegrityError:
            pass # Abaikan jika terjadi duplikasi 
            
    conn.close()
    return bahan_dari_ai

#Prompt Gemini
def bongkar_resep_dengan_gemini(nama_makanan):
    prompt = f"""
    Sebutkan bahan-bahan mentah utama untuk membuat 1 PORSI masakan '{nama_makanan}'.
    
    ATURAN SANGAT PENTING:
    1. VALIDASI MAKANAN: Analisis secara logis apakah '{nama_makanan}' benar-benar makanan/minuman yang wajar dikonsumsi manusia. Jika itu adalah benda mati (misal: monitor, meja, laptop), nama orang, bangunan, atau hal absurd, kamu WAJIB menolak dan HANYA mengembalikan JSON array kosong: []
    2. SKALA PORSI: Takaran HARUS disesuaikan untuk 1 PORSI standar makan 1 orang.
    3. KONVERSI WAJIB KE GRAM: Kamu HARUS menakar dan mengonversi SEMUA bahan ke dalam satuan "gram". 
       - JANGAN PERNAH menggunakan satuan buah, siung, sdm, sdt, ikat, atau lembar.
       - Gunakan logika dan pengetahuanmu tentang berat asli bahan! (Contoh: 5 buah cabai rawit = ~10 gram, 1 siung bawang putih = ~3 gram, 1 sdm minyak = ~15 gram).
       - Jika angkanya desimal, gunakan titik (misal: 2.5 gram).
    4. PENAMAAN BAHAN: Nama bahan HARUS spesifik ke bahan mentah (misal: "daging ayam", "beras putih matang"). 
    5. FORMAT: Berikan respons HANYA dalam format JSON array of strings tanpa blok markdown.
    6. STRUKTUR TEKS: Setiap string HARUS memiliki format kaku: "[Angka] gram [Nama Bahan Baku]".
    
    Contoh output yang benar untuk 1 porsi (misal input: ayam geprek): 
    ["150 gram daging ayam", "6 gram bawang putih", "15 gram minyak goreng", "10 gram cabai rawit", "20 gram tepung terigu"]
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"\n[Error] Gagal menghubungi Gemini: {e}")
        raise e

def proses_nutrisi_terminal(nama_makanan):
    db = DBHelper('nutrikost.db')
    conn = db._get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT code, food_name, cal, protein, carb, fat, water, fiber FROM Makanan")
    db_makanan = cursor.fetchall()
    
    nama_makanan_db = {row['food_name']: row for row in db_makanan}
    list_nama_db = list(nama_makanan_db.keys())

    #1. Cek di db TKPI USDA
    kecocokan_master, skor_master = process.extractOne(nama_makanan.lower(), list_nama_db)
    
    if kecocokan_master and skor_master >= 95:
        print(f"\n[🌟 MASTER DB HIT] Makanan langsung ditemukan di database sebagai '{kecocokan_master}' (Akurasi: {skor_master}%)")
        data_nutrisi = nama_makanan_db[kecocokan_master]
        
        print("=" * 60)
        print(f" INFORMASI NUTRISI (Per 100 gram): {kecocokan_master.upper()} ".center(60, '-'))
        print(f" Kalori : {data_nutrisi['cal']} kcal")
        print(f" Protein: {data_nutrisi['protein']} g")
        print(f" Karbo  : {data_nutrisi['carb']} g")
        print(f" Lemak  : {data_nutrisi['fat']} g")
        print("=" * 60)
        
        conn.close()
        return "EXISTS", kecocokan_master

    #2. Cek di tabel cache, jika tidak ada, panggil AI
    print(f"\n[INFO] '{nama_makanan}' tidak ada di database utama. Memulai proses dekonstruksi bahan...")
    
    daftar_bahan_mentah = get_or_fetch_resep(nama_makanan)

    if not daftar_bahan_mentah:
        print("Tidak ada bahan yang berhasil diuraikan.")
        conn.close()
        return "EMPTY", None

    print(f"\nBahan baku: {daftar_bahan_mentah}\n")
    print("=" * 60)
    print(" KALKULASI NUTRISI DARI BAHAN MENTAH ".center(60))
    print("=" * 60)

    total_kalori = 0
    total_protein = 0
    total_karbo = 0
    total_lemak = 0
    total_air = 0
    total_serat = 0
    total_berat_semua = 0

    for teks_bahan in daftar_bahan_mentah:
        match = re.search(r'([\d\./]+)\s*([a-zA-Z]+)\s*(.*)', teks_bahan)
        
        if match:
            kuantitas_str = match.group(1).replace('/', '.0/')
            try:
                kuantitas = float(eval(kuantitas_str))
            except:
                kuantitas = 1.0
                
            satuan = match.group(2).lower()
            nama_bahan_mentah = match.group(3).strip()

            kecocokan_terbaik, skor_bahan = process.extractOne(nama_bahan_mentah, list_nama_db)

            if kecocokan_terbaik and skor_bahan >= 70:
                data_nutrisi = nama_makanan_db[kecocokan_terbaik]

                pengali_gram = KONVERSI_GRAM.get(satuan, 100) 
                total_berat_gram = kuantitas * pengali_gram
                total_berat_semua += total_berat_gram

                kalori_bahan  = (total_berat_gram / 100) * float(data_nutrisi['cal'])
                protein_bahan = (total_berat_gram / 100) * float(data_nutrisi['protein'])
                karbo_bahan   = (total_berat_gram / 100) * float(data_nutrisi['carb'])
                lemak_bahan   = (total_berat_gram / 100) * float(data_nutrisi['fat'])
                air_bahan     = (total_berat_gram / 100) * float(data_nutrisi['water'] or 0)
                serat_bahan   = (total_berat_gram / 100) * float(data_nutrisi['fiber'] or 0)

                total_kalori  += kalori_bahan
                total_protein += protein_bahan
                total_karbo   += karbo_bahan
                total_lemak   += lemak_bahan
                total_air     += air_bahan
                total_serat   += serat_bahan

                print(f"[ ✓ ] {teks_bahan}")
                print(f"      Terdeteksi sebagai : {kecocokan_terbaik} (Akurasi: {skor_bahan}%)")
                print(f"      Estimasi Berat     : {total_berat_gram} gram")
                print(f"      Nutrisi            : {round(kalori_bahan, 1)} kcal | {round(protein_bahan, 1)}g Protein | {round(lemak_bahan, 1)}g Lemak\n")
            else:
                print(f"[ X ] {teks_bahan}")
                print("      -> Tidak ditemukan kecocokan yang memadai di database.\n")
        else:
            print(f"[ ! ] {teks_bahan}")
            print("      -> Format dari AI gagal diparsing oleh regex.\n")

    # --- Simpan hasil nutrisi ke CacheResep ---
    if total_berat_semua > 0 and total_kalori > 0:
        # Normalisasi ke per-100-gram agar konsisten dengan kolom di tabel Makanan
        faktor = 100 / total_berat_semua
        cal_per100     = round(total_kalori  * faktor, 2)
        protein_per100 = round(total_protein * faktor, 2)
        carb_per100    = round(total_karbo   * faktor, 2)
        fat_per100     = round(total_lemak   * faktor, 2)
        water_per100   = round(total_air     * faktor, 2)
        fiber_per100   = round(total_serat   * faktor, 2)

        db_path = DBHelper('nutrikost.db').db_path
        conn_cache = sqlite3.connect(db_path)

        try:
            conn_cache.execute(
                """
                UPDATE CacheResep
                SET cal = ?, protein = ?, carb = ?, fat = ?, water = ?, fiber = ?
                WHERE nama_makanan = ?
                """,
                (cal_per100, protein_per100, carb_per100, fat_per100,
                 water_per100, fiber_per100, nama_makanan.lower())
            )
            conn_cache.commit()
            print(f"\n[💾 NUTRISI TERSIMPAN] Hasil nutrisi '{nama_makanan}' (per 100g) disimpan ke CacheResep.")
        except Exception as e:
            print(f"\n[⚠️  GAGAL SIMPAN] Tidak bisa memperbarui CacheResep: {e}")
        finally:
            conn_cache.close()

    conn.close()

    print("=" * 60)
    print(f" ESTIMASI TOTAL NUTRISI: {nama_makanan.upper()} ".center(60, '-'))
    print(f" Kalori Keseluruhan : {round(total_kalori, 1)} kcal")
    print(f" Total Berat Masakan: {round(total_berat_semua, 1)} g")
    print(f" Protein Keseluruhan: {round(total_protein, 1)} g")
    print(f" Karbo Keseluruhan  : {round(total_karbo, 1)} g")
    print(f" Lemak Keseluruhan  : {round(total_lemak, 1)} g")
    print(f" Air Keseluruhan    : {round(total_air, 1)} g")
    print(f" Serat Keseluruhan  : {round(total_serat, 1)} g")
    if total_berat_semua > 0:
        print("-" * 60)
        f = 100 / total_berat_semua
        print(f" Nutrisi Per 100g   : {round(total_kalori * f, 1)} kcal | "
              f"{round(total_protein * f, 1)}g Protein | "
              f"{round(total_karbo * f, 1)}g Karbo | "
              f"{round(total_lemak * f, 1)}g Lemak | "
              f"{round(total_air * f, 1)}g Air | "
              f"{round(total_serat * f, 1)}g Serat")
    print("=" * 60)
    return "SUCCESS", None

if __name__ == "__main__":
    init_cache_table()
    
    print("=== PROGRAM ANALISIS NUTRISI AI (CLI) ===")
    while True:
        makanan_input = input("\nMasukkan nama makanan (atau ketik 'q' untuk keluar): ")
        if makanan_input.lower() in ['q', 'quit', 'exit']:
            print("Program dihentikan.")
            break
        
        if makanan_input.strip():
            proses_nutrisi_terminal(makanan_input)