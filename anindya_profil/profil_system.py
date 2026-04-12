import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scrapper'))
from models import DBHelper, JsonHelper

class ProfilSystem:

    def __init__(self):
        self.data_helper = DBHelper()
        self.current_profil = None

    def validasiInput(self, data):
        # Cek nama tidak boleh kosong
        if not data.get('full_name') or not data['full_name'].strip():
            print("Nama tidak boleh kosong.")
            return False

        # Cek usia: harus angka, antara 1 sampai 120
        usia = data.get('age')
        if not isinstance(usia, int) or usia <= 0 or usia > 120:
            print("Usia tidak valid (harus 1-120).")
            return False

        # Cek gender: hanya boleh 'Male' atau 'Female'
        if data.get('gender') not in ['Male', 'Female']:
            print("Gender harus 'Male' atau 'Female'.")
            return False

        # Cek berat badan: tidak boleh 0 atau negatif
        bb = data.get('weight')
        if not isinstance(bb, (int, float)) or bb <= 0 or bb > 300:
            print("Berat badan tidak valid (harus > 0 kg).")
            return False

        # Cek tinggi badan: tidak boleh 0 atau negatif
        tb = data.get('height')
        if not isinstance(tb, (int, float)) or tb <= 0 or tb > 300:
            print("Tinggi badan tidak valid (harus > 0 cm).")
            return False

        # Cek email: harus ada '@' dan '.'
        email = data.get('email', '')
        if not email or '@' not in email or '.' not in email:
            print("Format email tidak valid.")
            return False

        # Cek password: minimal 6 karakter
        password = data.get('password', '')
        if not password or len(password) < 6:
            print("Password minimal 6 karakter.")
            return False

        print("Semua input valid.")
        return True