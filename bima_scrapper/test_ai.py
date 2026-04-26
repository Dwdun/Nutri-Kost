import os
import json
import re
import google.generativeai as genai
from thefuzz import process

# Import class dan konstanta dari file models.py Anda
from models import DBHelper, KONVERSI_GRAM 

# ==========================================
# KONFIGURASI GEMINI
# ==========================================
genai.configure(api_key="AIzaSyBu5Ce7b1inSfAUJQFEblWqUMRu9uUIhzs")
model = genai.GenerativeModel('gemini-flash-latest')

def bongkar_resep_dengan_gemini(nama_makanan):
    """
    Meminta Gemini membongkar resep dengan format takaran yang spesifik
    agar bisa diproses oleh regex di sistem.
    """
    prompt = f"""
    Sebutkan bahan-bahan mentah utama untuk membuat masakan '{nama_makanan}'.
    Berikan respons HANYA dalam format JSON array of strings.
    Setiap string HARUS memiliki format yang kaku: "[Angka] [Satuan] [Nama Bahan]".
    Pilihan satuan yang diperbolehkan hanya: gram, gr, sdm, sdt, siung, ekor, genggam, pcs, buah.
    Contoh output yang benar: ["100 gram daging ayam", "2 siung bawang putih", "1 sdm minyak goreng", "5 buah cabai rawit"]
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1 # Suhu rendah agar AI patuh pada format
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"\n[Error] Gagal menghubungi Gemini: {e}")
        return []

def proses_nutrisi_terminal(nama_makanan):
    print(f"\nMeminta Gemini menganalisis resep '{nama_makanan}'...")
    daftar_bahan_mentah = bongkar_resep_dengan_gemini(nama_makanan)

    if not daftar_bahan_mentah:
        print("Tidak ada bahan yang berhasil diuraikan.")
        return

    print(f"Bahan baku dari AI: {daftar_bahan_mentah}\n")
    print("=" * 60)
    print(" MENCOCOKKAN DENGAN DATABASE LOKAL (nutrikost.db)".center(60))
    print("=" * 60)

    # Inisialisasi koneksi database menggunakan helper Anda
    db = DBHelper('nutrikost.db')
    conn = db._get_connection()
    cursor = conn.cursor()

    # Ambil semua katalog makanan untuk fuzzy matching
    cursor.execute("SELECT code, food_name, cal, protein, carb, fat FROM Makanan")
    db_makanan = cursor.fetchall()
    
    # Buat dictionary untuk akses cepat data nutrisi berdasarkan nama
    nama_makanan_db = {row['food_name']: row for row in db_makanan}
    list_nama_db = list(nama_makanan_db.keys())

    total_kalori = 0
    total_protein = 0

    for teks_bahan in daftar_bahan_mentah:
        # Menggunakan regex dari models.py Anda untuk memisahkan kuantitas, satuan, dan nama
        match = re.search(r'([\d\./]+)\s*([a-zA-Z]+)\s*(.*)', teks_bahan)
        
        if match:
            # Handle kasus angka pecahan (misal "1/2")
            kuantitas_str = match.group(1).replace('/', '.0/')
            try:
                kuantitas = float(eval(kuantitas_str))
            except:
                kuantitas = 1.0
                
            satuan = match.group(2).lower()
            nama_bahan_mentah = match.group(3).strip()

            # Mencari kecocokan nama bahan menggunakan thefuzz
            kecocokan_terbaik = process.extractOne(nama_bahan_mentah, list_nama_db)

            # Batas toleransi kemiripan (threshold) disetel ke 70
            if kecocokan_terbaik and kecocokan_terbaik[1] >= 70:
                nama_ditemukan = kecocokan_terbaik[0]
                skor = kecocokan_terbaik[1]
                data_nutrisi = nama_makanan_db[nama_ditemukan]

                # Konversi berat menggunakan kamus di models.py
                pengali_gram = KONVERSI_GRAM.get(satuan, 100) # Default 100g jika satuan tidak dikenali
                total_berat_gram = kuantitas * pengali_gram

                # Hitung proporsi nutrisi berdasarkan berat
                kalori_bahan = (total_berat_gram / 100) * float(data_nutrisi['cal'])
                protein_bahan = (total_berat_gram / 100) * float(data_nutrisi['protein'])

                total_kalori += kalori_bahan
                total_protein += protein_bahan

                print(f"[ ✓ ] {teks_bahan}")
                print(f"      Terdeteksi sebagai : {nama_ditemukan} (Akurasi: {skor}%)")
                print(f"      Estimasi Berat   : {total_berat_gram} gram")
                print(f"      Nutrisi          : {round(kalori_bahan, 1)} kcal | {round(protein_bahan, 1)}g Protein\n")
            else:
                print(f"[ X ] {teks_bahan}")
                print("      -> Tidak ditemukan kecocokan yang memadai di database.\n")
        else:
            print(f"[ ! ] {teks_bahan}")
            print("      -> Format dari AI gagal diparsing oleh regex.\n")

    conn.close()

    print("=" * 60)
    print(f" ESTIMASI TOTAL NUTRISI: {nama_makanan.upper()} ".center(60, '-'))
    print(f" Kalori Keseluruhan : {round(total_kalori, 1)} kcal")
    print(f" Protein Keseluruhan: {round(total_protein, 1)} g")
    print("=" * 60)

if __name__ == "__main__":
    print("=== PROGRAM ANALISIS NUTRISI AI (CLI) ===")
    while True:
        makanan_input = input("\nMasukkan nama makanan (atau ketik 'q' untuk keluar): ")
        if makanan_input.lower() in ['q', 'quit', 'exit']:
            print("Program dihentikan.")
            break
        
        if makanan_input.strip():
            proses_nutrisi_terminal(makanan_input)