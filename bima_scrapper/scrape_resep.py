import requests
from bs4 import BeautifulSoup
import json
import os
import time
def scrape_cookpad():
    print("Mulai mengambil resep makanan sehat...")
    base_url = "https://cookpad.com"
    search_url = f"{base_url}/id/cari/makanan%20sehat"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Gagal membuka halaman pencarian: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    recipe_items = soup.find_all('li', class_='ranked-list__item')[:15]
    
    resep_harian = []

    for item in recipe_items:
        title_tag = item.find('a', class_='block-link__main')
        if not title_tag:
            continue
            
        judul = title_tag.get_text(strip=True)
        link = base_url + title_tag['href']
        
        img_tag = item.find('img')
        gambar = img_tag['src'] if img_tag else ""
        
        summary_tag = item.find('div', attrs={'data-ingredients-redesign-target': 'ingredients'})
        komposisi_singkat = summary_tag.get_text(strip=True) if summary_tag else ""

        print(f"-> Memproses: {judul}")
        
        time.sleep(2)
        
        try:
            detail_response = requests.get(link, headers=headers)
            detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
            
            bahan_detail = []
            ingredients_div = detail_soup.find('div', id='ingredients')
            if ingredients_div:
                lis = ingredients_div.find_all('li')
                for li in lis:
                    bahan_text = ' '.join(li.get_text(strip=True).split())
                    bahan_detail.append(bahan_text)
            
            langkah_langkah = []
            steps_div = detail_soup.find('div', id='steps')
            if steps_div:
                step_lis = steps_div.find_all('li', class_='step')
                for sli in step_lis:
                    p_tag = sli.find('p')
                    if p_tag:
                        langkah_langkah.append(p_tag.get_text(strip=True))
                        
            resep_harian.append({
                "judul": judul,
                "link": link,
                "gambar": gambar,
                "komposisi_singkat": komposisi_singkat,
                "bahan_detail": bahan_detail,
                "langkah_langkah": langkah_langkah
            })
            
        except Exception as e:
            print(f"   [!] Gagal mengambil detail {judul}: {e}")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, 'Resep.json')
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(resep_harian, f, indent=4, ensure_ascii=False)
        
    print(f"\n[v] Selesai! {len(resep_harian)} resep telah diperbarui di {json_path}")

    