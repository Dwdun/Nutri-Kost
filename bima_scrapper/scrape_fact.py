import requests
from bs4 import BeautifulSoup
import json
import os

def scrape_food_facts():
    url = "https://www.halodoc.com/kesehatan/makanan-sehat"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    
    print(f"Mengambil data dari {url}...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Gagal mengakses website: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    lists = soup.find_all('ul', class_='wp-block-list')
    
    if not lists:
        print("Elemen list tidak ditemukan. Struktur web mungkin berubah atau diblokir.")
        return

    food_facts = []

    for ul in lists:
        list_items = ul.find_all('li')
        
        for li in list_items:
            strong_tag = li.find('strong')
            
            if strong_tag:

                judul = strong_tag.get_text(strip=True)

                if judul.endswith(':'):
                    judul = judul[:-1].strip()

                full_text = li.get_text(strip=True)
                strong_text = strong_tag.get_text(strip=True)

                isi = full_text.replace(strong_text, '', 1).strip()

                food_facts.append({
                    "judul": judul,
                    "isi": isi
                })
                
                print(f"-> Berhasil mengambil: {judul}")

    if not food_facts:
        print("Tidak ada data fakta yang berhasil diekstrak.")
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, 'FoodFact.json')
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(food_facts, f, indent=4, ensure_ascii=False)
        
    print(f"\nSelesai! {len(food_facts)} fakta berhasil disimpan ke: {json_path}")

if __name__ == '__main__':
    scrape_food_facts()