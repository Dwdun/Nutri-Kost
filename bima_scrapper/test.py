import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QTableWidget, QTableWidgetItem, 
                            QDialog, QLabel, QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt

# Menggunakan DBHelper dan JsonHelper dari models.py
from models import DBHelper, JsonHelper, kalkulasi_nutrisi_bahan

# Impor fungsi scraper dari file scrape_resep.py
try:
    from scrape_resep import scrape_cookpad
except ImportError:
    # Fungsi fallback jika file tidak ditemukan
    def scrape_cookpad():
        print("Error: scrape_resep.py tidak ditemukan di folder yang sama.")


# ==========================================
# 2. POP-UP DETAIL RESEP (DIALOG)
# ==========================================
class DetailResepDialog(QDialog):
    def __init__(self, resep, db_makanan_dict):
        super().__init__()
        self.setWindowTitle(f"Nutrisi: {resep.get('judul', 'Resep')}")
        self.resize(700, 500)
        self.resep = resep
        self.db_makanan_dict = db_makanan_dict
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        judul_label = QLabel(f"<b>{self.resep.get('judul', 'Tanpa Judul')}</b>")
        judul_label.setStyleSheet("font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(judul_label)

        self.tabel_bahan = QTableWidget()
        self.tabel_bahan.setColumnCount(6)
        self.tabel_bahan.setHorizontalHeaderLabels(
            ["Bahan Mentah", "Dikenali Sbg (DB)", "Berat (g)", "Kalori", "Protein", "Karbo"]
        )
        self.tabel_bahan.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.tabel_bahan)

        # Gunakan 'bahan_detail' sesuai kunci di Resep.json
        bahan_list = self.resep.get('bahan_detail', [])
        self.tabel_bahan.setRowCount(len(bahan_list))
        
        total_kal = total_pro = total_kar = total_lem = 0

        for row, teks_bahan in enumerate(bahan_list):
            self.tabel_bahan.setItem(row, 0, QTableWidgetItem(teks_bahan))
            
            # Kalkulasi menggunakan fungsi dari models.py
            hasil = kalkulasi_nutrisi_bahan(teks_bahan, self.db_makanan_dict)
            
            if hasil:
                self.tabel_bahan.setItem(row, 1, QTableWidgetItem(hasil['nama_db']))
                self.tabel_bahan.setItem(row, 2, QTableWidgetItem(str(hasil['berat_g'])))
                self.tabel_bahan.setItem(row, 3, QTableWidgetItem(f"{hasil['kalori']} kcal"))
                self.tabel_bahan.setItem(row, 4, QTableWidgetItem(f"{hasil['protein']} g"))
                self.tabel_bahan.setItem(row, 5, QTableWidgetItem(f"{hasil['karbo']} g"))
                
                total_kal += hasil['kalori']
                total_pro += hasil['protein']
                total_kar += hasil['karbo']
                total_lem += hasil['lemak']
            else:
                self.tabel_bahan.setItem(row, 1, QTableWidgetItem("Tidak Dikenali"))
                for col in range(2, 6):
                    self.tabel_bahan.setItem(row, col, QTableWidgetItem("-"))

        ringkasan_teks = (
            f"<b>Estimasi Total Nutrisi Resep:</b><br>"
            f"Kalori: {round(total_kal, 1)} kcal | "
            f"Protein: {round(total_pro, 1)} g | "
            f"Karbohidrat: {round(total_kar, 1)} g | "
            f"Lemak: {round(total_lem, 1)} g"
        )
        ringkasan_label = QLabel(ringkasan_teks)
        ringkasan_label.setStyleSheet("background-color: #e0f7fa; padding: 10px; border-radius: 5px;")
        layout.addWidget(ringkasan_label)

        self.setLayout(layout)


# ==========================================
# 3. JENDELA UTAMA APLIKASI
# ==========================================
class NutrikostApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nutrikost - Dashboard Resep Harian")
        self.resize(800, 600)
        self.resep_data = []
        self.db_makanan_dict = {}
        
        self.muat_database()
        self.initUI()

    def muat_database(self):
        """Memuat data dari nutrikost.db ke memori"""
        try:
            # Menggunakan method DBHelper dari models.py
            db = DBHelper()
            semua_makanan = db.get_all_makanan()
            
            # Konversi menjadi format dictionary dengan key food_name
            self.db_makanan_dict = {row['food_name']: row for row in semua_makanan}
        except Exception as e:
            QMessageBox.warning(self, "Error DB", f"Gagal memuat database: {e}")

    def initUI(self):
        main_widget = QWidget()
        layout = QVBoxLayout()

        self.btn_scrape = QPushButton("Perbarui & Muat Resep dari Cookpad")
        self.btn_scrape.setStyleSheet("padding: 12px; font-weight: bold; background-color: #2E7D32; color: white;")
        self.btn_scrape.clicked.connect(self.proses_muat_data)
        layout.addWidget(self.btn_scrape)

        self.tabel_resep = QTableWidget()
        self.tabel_resep.setColumnCount(2)
        self.tabel_resep.setHorizontalHeaderLabels(["Judul Resep", "Status"])
        self.tabel_resep.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabel_resep.cellDoubleClicked.connect(self.buka_detail_resep)
        layout.addWidget(self.tabel_resep)

        layout.addWidget(QLabel("<i>*Klik ganda pada resep untuk melihat kalkulasi nutrisi otomatis.</i>"))

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

    def proses_muat_data(self):
        """Menjalankan scraper lalu memperbarui tabel GUI"""
        try:
            # Feedback visual: Ubah kursor dan teks tombol
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.btn_scrape.setText("Sedang Mengambil Resep Baru... Mohon Tunggu")
            self.btn_scrape.setEnabled(False)
            QApplication.processEvents() 

            # Panggil fungsi dari scrape_resep.py
            scrape_cookpad() 

            # Muat ulang JSON menggunakan method dari models.py
            json_helper = JsonHelper()
            self.resep_data = json_helper.get_resep_harian()
            
            if self.resep_data:
                self.tabel_resep.setRowCount(len(self.resep_data))
                for row, resep in enumerate(self.resep_data):
                    self.tabel_resep.setItem(row, 0, QTableWidgetItem(resep.get('judul', '')))
                    self.tabel_resep.setItem(row, 1, QTableWidgetItem("Tersedia"))

                QMessageBox.information(self, "Selesai", f"Berhasil memuat {len(self.resep_data)} resep terbaru!")
            else:
                QMessageBox.warning(self, "Data Kosong", "Data Resep.json tidak ditemukan atau kosong.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Terjadi kesalahan saat pemrosesan: {e}")
        finally:
            # Kembalikan keadaan tombol dan kursor
            QApplication.restoreOverrideCursor()
            self.btn_scrape.setText(" Perbarui & Muat Resep dari Cookpad")
            self.btn_scrape.setEnabled(True)

    def buka_detail_resep(self, row, column):
        resep_terpilih = self.resep_data[row]
        dialog = DetailResepDialog(resep_terpilih, self.db_makanan_dict)
        dialog.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NutrikostApp()
    window.show()
    sys.exit(app.exec_())