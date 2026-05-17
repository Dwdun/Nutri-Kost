import sys
import os
import hashlib

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bima_scrapper'))
from models import DBHelper, JsonHelper

class ProfilSystem:

    def _hash_password(self, password):
        # Enkripsi password pakai SHA-256
        # algoritma hash yang mengubah password jadi kode unik
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, email_input, password):
        # Hash password yang diinput dulu sebelum dibandingkan
        password_hash = self._hash_password(password)

        # Ambil semua user dari database
        try:
            semua_user = self.data_helper.get_all_users()
        except Exception:
            semua_user = self._mock_db

        user_exists = False
        for user in semua_user:
            if user.get('email') == email_input:
                user_exists = True
                if user.get('password') == password_hash:
                    self.current_profil = user
                    print(f"Login berhasil! Selamat datang, {user.get('full_name')}")
                    return True, "Berhasil"
                else:
                    return False, "Password yang Anda masukkan salah."

        if not user_exists:
             return False, "Akun tidak ditemukan. Silakan daftar terlebih dahulu."
             
        return False, "Email atau Password salah!"

    def __init__(self):
        self.data_helper = DBHelper()
        self.current_profil = None
        self._mock_db = []
        self._mock_id_counter = 1

    def validasiInput(self, data):
        # Cek nama tidak boleh kosong
        if not data.get('full_name') or not data['full_name'].strip():
            return False, "Nama tidak boleh kosong."

        # Cek usia: harus angka, antara 1 sampai 120
        usia = data.get('age')
        if not isinstance(usia, int) or usia <= 0 or usia > 120:
            return False, "Usia tidak valid (harus 1-120)."

        # Cek gender: hanya boleh 'Laki-laki' atau 'Perempuan'
        if data.get('gender') not in ['Laki-laki', 'Perempuan']:
            return False, "Gender harus 'Laki-laki' atau 'Perempuan'."

        # Cek berat badan: tidak boleh 0 atau negatif
        bb = data.get('weight')
        if not isinstance(bb, (int, float)) or bb <= 0 or bb > 300:
            return False, "Berat badan tidak valid (harus > 0 kg, maks 300 kg)."

        # Cek tinggi badan: tidak boleh 0 atau negatif
        tb = data.get('height')
        if not isinstance(tb, (int, float)) or tb <= 0 or tb > 300:
            return False, "Tinggi badan tidak valid (harus > 0 cm, maks 300 cm)."

        # Cek email: harus ada '@' dan '.'
        email = data.get('email', '')
        if not email or '@' not in email or '.' not in email:
            return False, "Format email tidak valid."

        # Cek password: minimal 6 karakter
        password = data.get('password', '')
        if not password or len(password) < 6:
            return False, "Password minimal 6 karakter."

        return True, "Semua input valid."

    def cekEmailTerdaftar(self, email):
        """Mengecek apakah email sudah ada di database atau mock memory."""
        email_input = email.strip()
        try:
            semua_user = self.data_helper.get_all_users()
        except Exception:
            semua_user = self._mock_db
            
        for user in semua_user:
            if user.get('email') == email_input:
                return True
        return False
    
    def createProfil(self, data):
        # validasi dulu sebelum simpan ke database
        valid, msg = self.validasiInput(data)
        if not valid:
            return False, msg

        # Hitung target kalori manual (atau dengan kalkulator)
        aktivitas = data.get('activity', 'Sedentary (Jarang Olahraga)')
        target_cal = self.calculatorHarrisBenedict(data['gender'], data['weight'], data['height'], data['age'], aktivitas)
        if target_cal is None:
             target_cal = 2100

        # siapkan data sesuai format database 
        user_data = {
            'full_name' : data['full_name'].strip(),
            'age'       : data['age'],
            'gender'    : data['gender'],
            'weight'    : data['weight'],
            'height'    : data['height'],
            'activity'  : aktivitas,
            'diet_goal' : data.get('diet_goal', 'Maintain Berat Badan'),
            'calory'    : target_cal,
            'email'     : data['email'].strip(),
            'password'  : self._hash_password(data['password'])
        }

        # panggil create_user() 
        try:
            id_user = self.data_helper.create_user(user_data)
            self.current_profil = self.data_helper.get_user_by_id(id_user)
            print(f"Profil berhasil dibuat! ID user: {id_user}")
            return True, "Profil berhasil dibuat!"
        except Exception as e:
            user_data['id_user'] = self._mock_id_counter
            self._mock_id_counter += 1
            self._mock_db.append(user_data)
            self.current_profil = user_data
            print("Profil berhasil dibuat di Mock Memory!")
            return True, "Profil berhasil dibuat!"
    
    def readProfil(self):
        # Cek dulu apakah current_profil sudah ada
        # current_profil diisi waktu createProfil() dipanggil
        if self.current_profil is None:
            print("Belum ada profil yang aktif.")
            return None

        # Ambil data terbaru dari database
        # Pakai id_user dari current_profil untuk cari datanya
        id_user = self.current_profil['id_user']
        try:
            profil = self.data_helper.get_user_by_id(id_user)
            if profil:
                self.current_profil = profil
        except Exception:
            for user in self._mock_db:
                if user['id_user'] == id_user:
                    self.current_profil = user
                    break
        
        if self.current_profil:
            print(f"Profil ditemukan: {self.current_profil['full_name']}")
        return self.current_profil
    
    def calculatorBMI(self, berat, tinggi):
        # Validasi input: berat dan tinggi tidak boleh 0 atau negatif
        if berat <= 0 or tinggi <= 0:
            print("Error: Berat dan tinggi harus lebih dari 0.")
            return None

        # Konversi tinggi dari cm ke meter
        tinggi_meter = tinggi / 100

        # Hitung BMI dengan rumus
        # round() untuk bulatkan 2 angka di belakang koma
        bmi = round(berat / (tinggi_meter ** 2), 2)

        # Tentukan status berdasarkan nilai BMI
        # Standar WHO (World Health Organization)
        if bmi < 18.5:
            status = "Kurus"
        elif bmi < 25.0:
            status = "Normal"
        elif bmi < 30.0:
            status = "Gemuk"
        else:
            status = "Obesitas"

        print(f"BMI kamu: {bmi} -> {status}")

        # Return string gabungan nilai BMI dan statusnya
        return f"{bmi} ({status})"
    
    def calculatorHarrisBenedict(self, jk, bb, tb, usia, aktivitas_level='Sedentary (Jarang Olahraga)'):
        # Validasi input
        if bb <= 0 or tb <= 0 or usia <= 0:
            print("Error: BB, TB, dan usia harus lebih dari 0.")
            return None

        if jk not in ['Laki-laki', 'Perempuan']:
            print("Error: Gender harus 'Laki-laki' atau 'Perempuan'.")
            return None

        # Hitung BMR berdasarkan jenis kelamin
        if jk == 'Laki-laki':
            bmr = 88.362 + (13.397 * bb) + (4.799 * tb) - (5.677 * usia)
        else:
            bmr = 447.593 + (9.247 * bb) + (3.098 * tb) - (4.330 * usia)

        # Kalikan BMR dengan faktor aktivitas
        if 'Sedentary' in aktivitas_level:
            faktor_aktivitas = 1.2
        elif 'Ringan' in aktivitas_level:
            faktor_aktivitas = 1.375
        elif 'Sedang' in aktivitas_level:
            faktor_aktivitas = 1.55
        elif 'Berat' in aktivitas_level:
            faktor_aktivitas = 1.725
        else:
            faktor_aktivitas = 1.2

        total_kalori = round(bmr * faktor_aktivitas, 1)

        print(f"BMR        : {round(bmr, 1)} kkal")
        print(f"Target kalori harian: {total_kalori} kkal")

        return total_kalori
    
    def updateProfil(self, data):
        # Cek dulu apakah ada user yang aktif
        if self.current_profil is None:
            print("Error: Belum ada profil yang aktif.")
            return False

        # Validasi field yang mau diupdate
        if 'weight' in data:
            if not isinstance(data['weight'], (int, float)) or data['weight'] <= 0 or data['weight'] > 300:
                print("Validasi gagal: Berat badan tidak valid.")
                return False

        if 'height' in data:
            if not isinstance(data['height'], (int, float)) or data['height'] <= 0 or data['height'] > 300:
                print("Validasi gagal: Tinggi badan tidak valid.")
                return False

        if 'age' in data:
            if not isinstance(data['age'], int) or data['age'] <= 0 or data['age'] > 120:
                print("Validasi gagal: Usia tidak valid.")
                return False

        if 'gender' in data:
            if data['gender'] not in ['Laki-laki', 'Perempuan']:
                print("Validasi gagal: Gender harus 'Laki-laki' atau 'Perempuan'.")
                return False

        if 'full_name' in data:
            if not data['full_name'] or not data['full_name'].strip():
                print("Validasi gagal: Nama tidak boleh kosong.")
                return False

        # Ambil id_user dari current_profil
        id_user = self.current_profil['id_user']

        # Panggil update_user() untuk update ke database
        try:
            self.data_helper.update_user(id_user, data)
            self.current_profil = self.data_helper.get_user_by_id(id_user)
        except Exception:
            for user in self._mock_db:
                if user['id_user'] == id_user:
                    user.update(data)
                    self.current_profil = user
                    break

        print(f"Profil berhasil diupdate!")
        return True
    
    def deleteProfil(self):
        # Cek dulu apakah ada user yang aktif
        # Tidak bisa hapus kalau belum ada profil
        if self.current_profil is None:
            print("Error: Belum ada profil yang aktif.")
            return False

        # Simpan dulu nama dan id sebelum dihapus
        # Karena setelah dihapus current_profil jadi None
        id_user = self.current_profil['id_user']
        nama    = self.current_profil['full_name']

        # Panggil delete_user() untuk hapus dari database
        # Otomatis hapus semua log harian user ini juga
        try:
            self.data_helper.delete_user(id_user)
        except Exception:
            self._mock_db = [u for u in self._mock_db if u['id_user'] != id_user]

        # Kosongkan current_profil karena user sudah dihapus
        self.current_profil = None

        print(f"Profil '{nama}' berhasil dihapus.")
        return True
    
    def getRealisasiKalori(self):
        # Cek dulu apakah ada user yang aktif
        if self.current_profil is None:
            print("Error: Belum ada profil yang aktif.")
            return 0.0

        # Ambil id_user dari current_profil
        id_user = self.current_profil['id_user']

        # Ambil tanggal hari ini format 'YYYY-MM-DD'
        from datetime import date
        hari_ini = str(date.today())

        # Panggil get_daily_summary()
        # Mengembalikan dict berisi total kalori, protein, karbo, lemak
        ringkasan = self.data_helper.get_daily_summary(id_user, hari_ini)

        # Ambil hanya total kalorinya saja
        # Kalau belum ada log hari ini, return 0
        total_kalori = ringkasan['total_cal'] or 0.0

        print(f"Kalori hari ini: {total_kalori} kkal")
        return float(total_kalori)
    
    def getAKGUser(self):
        # Cek dulu apakah ada user yang aktif
        if self.current_profil is None:
            print("Error: Belum ada profil yang aktif.")
            return None

        # Ambil usia dan gender dari current_profil
        usia   = self.current_profil['age']
        gender = self.current_profil['gender']

        # Konversi gender ke key yang ada di akg.json
        if gender == 'Laki-laki':
            kategori = 'Laki-laki'
        else:
            kategori = 'Perempuan'

        # Baca data AKG dari file akg.json
        jh  = JsonHelper()
        akg = jh.get_akg()

        # Strukturnya: {'Laki-laki': [...], 'Perempuan': [...]}
        # Jadi harus masuk ke key-nya dulu
        for data_akg in akg[kategori]:
            kelompok = data_akg.get('kelompok_umur', '')
            try:
                bagian      = kelompok.replace('tahun', '').strip().split('-')
                batas_bawah = int(bagian[0].strip())
                batas_atas  = int(bagian[1].strip())

                if batas_bawah <= usia <= batas_atas:
                    print(f"AKG ditemukan untuk usia {usia}, kategori {kategori}")
                    print(f"Kebutuhan kalori: {data_akg.get('cal')} kkal")
                    return data_akg
            except:
                continue

        print("Data AKG tidak ditemukan.")
        return None
