import requests
from bs4 import BeautifulSoup
import json
import os

def clean_number(text):
    """
    Membersihkan teks menjadi angka Float.
    Menghapus tanda koma, titik, dan tanda plus (+) untuk ibu hamil/menyusui.
    """
    text = text.strip().replace('+', '')
    
    if not text or text == '-':
        return 0.0

    cleaned = text.replace('.', '').replace(',', '.')
    
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def scrape_akg_to_json():
    url = "https://www.andrafarm.com/_andra.php?_i=daftar-akg"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    print(f"Mengambil data AKG dari {url}...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Gagal mengakses website: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table', class_='akgtabel')
    if not table:
        print("Tabel AKG tidak ditemukan!")
        return

    akg_data = {}
    current_category = "Umum"

    categories_marker = [
        "Bayi / Anak", 
        "Laki-laki", 
        "Perempuan", 
        "Hamil (+ tambahan)", 
        "Menyusui (+ tambahan)"
    ]

    rows = table.find_all('tr')

    for row in rows:
        if row.get('align') == 'center':
            cols = row.find_all('td')
            
            if len(cols) > 0:
                first_col_text = cols[0].get_text(strip=True)
                
                if first_col_text in categories_marker:
                    current_category = first_col_text
                    if current_category not in akg_data:
                        akg_data[current_category] = []
                    continue 
                
                age_tag = cols[0].find(['a', 'u'])
                
                if age_tag and len(cols) >= 11:
                    age_group = age_tag.get_text(strip=True)
                    
                    data_nutrisi = {
                        "kelompok_umur": age_group,
                        "cal": clean_number(cols[3].get_text(strip=True)),
                        "protein": clean_number(cols[4].get_text(strip=True)),
                        "fat": clean_number(cols[5].get_text(strip=True)),
                        "carb": clean_number(cols[8].get_text(strip=True)),
                        "fiber": clean_number(cols[9].get_text(strip=True)),
                        "water": clean_number(cols[10].get_text(strip=True))
                    }

                    if current_category not in akg_data:
                        akg_data[current_category] = []
                        
                    akg_data[current_category].append(data_nutrisi)
                    print(f"  -> Disimpan: {current_category} | {age_group}")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, 'akg.json')
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(akg_data, f, indent=4, ensure_ascii=False)
        
    print(f"\nSelesai! Data AKG berhasil disimpan ke: {json_path}")

if __name__ == '__main__':
    scrape_akg_to_json()