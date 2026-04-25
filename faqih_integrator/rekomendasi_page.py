import json
import sqlite3
import re
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QDialog, QLabel, QHeaderView, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt
from thefuzz import process

# Import scraper 
try:
    from scrape_resep import scrape_cookpad
except ImportError:
    def scrape_cookpad():
        print("Error: scrape_resep.py tidak ditemukan.")

# ── Kamus konversi satuan → gram ──────────────────────────────────────────────
KONVERSI_GRAM = {
    'sdm': 15, 'sdt': 5, 'siung': 5, 'ekor': 80, 'genggam': 40,
    'pcs': 50, 'buah': 100, 'gram': 1, 'gr': 1, 'liter': 1000, 'ml': 1,
    'lembar': 3, 'ikat': 50, 'batang': 15
}

def hitung_nutrisi_bahan(teks_bahan, db_makanan_dict):
    match = re.search(r'([\d\./]+)\s*([a-zA-Z]+)\s*(.*)', teks_bahan)
    if not match:
        return None
    try:
        kuantitas_str = match.group(1).replace('/', '.0/') if '/' in match.group(1) else match.group(1)
        kuantitas = float(eval(kuantitas_str))
    except Exception:
        return None

    satuan    = match.group(2).lower()
    nama_bahan = match.group(3).strip()

    list_nama_db = list(db_makanan_dict.keys())
    kecocokan = process.extractOne(nama_bahan, list_nama_db)

    if kecocokan and kecocokan[1] >= 70:
        nama_db      = kecocokan[0]
        data_nutrisi = db_makanan_dict[nama_db]
        berat_total  = kuantitas * KONVERSI_GRAM.get(satuan, 50)
        return {
            'nama_asli': teks_bahan,
            'nama_db':   nama_db,
            'berat_g':   round(berat_total, 1),
            'kalori':    round((berat_total / 100) * float(data_nutrisi[2]), 1),
            'protein':   round((berat_total / 100) * float(data_nutrisi[3]), 1),
            'karbo':     round((berat_total / 100) * float(data_nutrisi[4]), 1),
            'lemak':     round((berat_total / 100) * float(data_nutrisi[5]), 1),
        }
    return None


class DetailResepDialog(QDialog):
    def __init__(self, resep, db_makanan_dict):
        super().__init__()
        self.setWindowTitle(f"Nutrisi: {resep.get('judul', 'Resep')}")
        self.resize(700, 500)
        self.resep = resep
        self.db_makanan_dict = db_makanan_dict
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        judul = QLabel(f"<b>{self.resep.get('judul', 'Tanpa Judul')}</b>")
        judul.setStyleSheet("font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(judul)

        tabel = QTableWidget()
        tabel.setColumnCount(6)
        tabel.setHorizontalHeaderLabels(
            ["Bahan Mentah", "Dikenali Sbg (DB)", "Berat (g)", "Kalori", "Protein", "Karbo"]
        )
        tabel.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(tabel)

        bahan_list = self.resep.get('bahan_detail', [])
        tabel.setRowCount(len(bahan_list))

        total_kal = total_pro = total_kar = total_lem = 0
        for row, teks in enumerate(bahan_list):
            tabel.setItem(row, 0, QTableWidgetItem(teks))
            hasil = hitung_nutrisi_bahan(teks, self.db_makanan_dict)
            if hasil:
                tabel.setItem(row, 1, QTableWidgetItem(hasil['nama_db']))
                tabel.setItem(row, 2, QTableWidgetItem(str(hasil['berat_g'])))
                tabel.setItem(row, 3, QTableWidgetItem(f"{hasil['kalori']} kcal"))
                tabel.setItem(row, 4, QTableWidgetItem(f"{hasil['protein']} g"))
                tabel.setItem(row, 5, QTableWidgetItem(f"{hasil['karbo']} g"))
                total_kal += hasil['kalori']
                total_pro += hasil['protein']
                total_kar += hasil['karbo']
                total_lem += hasil['lemak']
            else:
                tabel.setItem(row, 1, QTableWidgetItem("Tidak Dikenali"))
                for col in range(2, 6):
                    tabel.setItem(row, col, QTableWidgetItem("-"))

        ringkasan = QLabel(
            f"<b>Estimasi Total Nutrisi Resep:</b><br>"
            f"Kalori: {round(total_kal, 1)} kcal | "
            f"Protein: {round(total_pro, 1)} g | "
            f"Karbohidrat: {round(total_kar, 1)} g | "
            f"Lemak: {round(total_lem, 1)} g"
        )
        ringkasan.setStyleSheet("background-color: #e0f7fa; padding: 10px; border-radius: 5px;")
        layout.addWidget(ringkasan)
        self.setLayout(layout)


class RekomendasiPage(QWidget):
    """Widget halaman Rekomendasi Resep — drop-in ke MainWindow._stack."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resep_data      = []
        self.db_makanan_dict = {}
        self._muat_database()
        self._init_ui()

    def _muat_database(self):
        """Load nutrikost.db dari folder bima_scrapper."""
        try:
            # bima_scrapper sudah di sys.path, jadi cukup cari lewat path relatif
            base_dir = os.path.join(os.path.dirname(__file__), '..', 'bima_scrapper')
            db_path  = os.path.normpath(os.path.join(base_dir, 'nutrikost.db'))
            conn     = sqlite3.connect(db_path)
            cursor   = conn.cursor()
            cursor.execute("SELECT code, food_name, cal, protein, carb, fat FROM Makanan")
            self.db_makanan_dict = {row[1]: row for row in cursor.fetchall()}
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Error DB", f"Gagal memuat database: {e}")

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.btn_scrape = QPushButton("🔄 Perbarui & Muat Resep dari Cookpad")
        self.btn_scrape.setStyleSheet(
            "padding: 12px; font-weight: bold; background-color: #2E7D32; color: white;"
        )
        self.btn_scrape.clicked.connect(self._proses_muat_data)
        layout.addWidget(self.btn_scrape)

        self.tabel = QTableWidget()
        self.tabel.setColumnCount(2)
        self.tabel.setHorizontalHeaderLabels(["Judul Resep", "Status"])
        self.tabel.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabel.cellDoubleClicked.connect(self._buka_detail)
        layout.addWidget(self.tabel)

        layout.addWidget(QLabel("<i>*Klik ganda pada resep untuk melihat kalkulasi nutrisi otomatis.</i>"))

    def _proses_muat_data(self):
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.btn_scrape.setText("⏳ Sedang Mengambil Resep Baru... Mohon Tunggu")
            self.btn_scrape.setEnabled(False)
            QApplication.processEvents()

            scrape_cookpad()

            # Resep.json disimpan oleh scrape_resep.py di dalam bima_scrapper/
            base_dir  = os.path.join(os.path.dirname(__file__), '..', 'bima_scrapper')
            json_path = os.path.normpath(os.path.join(base_dir, 'Resep.json'))

            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    self.resep_data = json.load(f)

                self.tabel.setRowCount(len(self.resep_data))
                for row, resep in enumerate(self.resep_data):
                    self.tabel.setItem(row, 0, QTableWidgetItem(resep.get('judul', '')))
                    self.tabel.setItem(row, 1, QTableWidgetItem("Tersedia"))

                QMessageBox.information(
                    self, "Selesai", f"Berhasil men-scrape {len(self.resep_data)} resep terbaru!"
                )
            else:
                QMessageBox.warning(self, "File Hilang", f"Resep.json tidak ditemukan di:\n{json_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Terjadi kesalahan: {e}")
        finally:
            QApplication.restoreOverrideCursor()
            self.btn_scrape.setText("🔄 Perbarui & Muat Resep dari Cookpad")
            self.btn_scrape.setEnabled(True)

    def _buka_detail(self, row, _col):
        resep = self.resep_data[row]
        dialog = DetailResepDialog(resep, self.db_makanan_dict)
        dialog.exec_()