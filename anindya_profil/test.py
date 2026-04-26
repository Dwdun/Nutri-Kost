import sys
import os

# Path ke folder scrapper 
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bima_scrapper'))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QDialog, QLabel,
    QLineEdit, QComboBox, QHeaderView, QMessageBox, QFormLayout
)
from PyQt5.QtCore import Qt

from profil_system import ProfilSystem

# ==========================================
# DIALOG: Form Buat / Edit Profil
# ==========================================
class FormProfilDialog(QDialog):
    def __init__(self, parent=None, profil=None):
        super().__init__(parent)
        self.profil = profil  # None = mode create, ada isi = mode edit
        self.setWindowTitle("Edit Profil" if profil else "Buat Profil Baru")
        self.resize(400, 380)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Judul
        judul = QLabel("<b>Edit Profil</b>" if self.profil else "<b>Buat Profil Baru</b>")
        judul.setStyleSheet("font-size: 15px; margin-bottom: 8px;")
        layout.addWidget(judul)

        # Form input
        form = QFormLayout()
        form.setSpacing(10)

        self.input_nama   = QLineEdit()
        self.input_usia   = QLineEdit()
        self.input_bb     = QLineEdit()
        self.input_tb     = QLineEdit()
        self.input_email  = QLineEdit()
        self.input_pass   = QLineEdit()
        self.input_pass.setEchoMode(QLineEdit.Password)

        self.combo_gender = QComboBox()
        self.combo_gender.addItems(["Male", "Female"])

        # Kalau mode edit, isi form dengan data yang ada
        if self.profil:
            self.input_nama.setText(str(self.profil.get('full_name', '')))
            self.input_usia.setText(str(self.profil.get('age', '')))
            self.input_bb.setText(str(self.profil.get('weight', '')))
            self.input_tb.setText(str(self.profil.get('height', '')))
            self.input_email.setText(str(self.profil.get('email', '')))
            self.combo_gender.setCurrentText(self.profil.get('gender', 'Male'))

        form.addRow("Nama Lengkap :", self.input_nama)
        form.addRow("Usia         :", self.input_usia)
        form.addRow("Jenis Kelamin:", self.combo_gender)
        form.addRow("Berat Badan  :", self.input_bb)
        form.addRow("Tinggi Badan :", self.input_tb)
        form.addRow("Email        :", self.input_email)

        # Password hanya muncul saat create
        if not self.profil:
            form.addRow("Password     :", self.input_pass)

        layout.addLayout(form)

        # Tombol simpan + batal
        btn_row = QHBoxLayout()
        btn_batal  = QPushButton("Batal")
        btn_simpan = QPushButton("Simpan")
        btn_simpan.setStyleSheet("padding: 8px 20px; font-weight: bold; background-color: #1A7A34; color: white;")
        btn_batal.clicked.connect(self.reject)
        btn_simpan.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(btn_batal)
        btn_row.addWidget(btn_simpan)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def get_data(self):
        # Ambil semua data dari form dan return sebagai dict
        data = {
            'full_name' : self.input_nama.text(),
            'age'       : int(self.input_usia.text()) if self.input_usia.text().strip() else 0,
            'gender'    : self.combo_gender.currentText(),
            'weight'    : float(self.input_bb.text()) if self.input_bb.text().strip() else 0,
            'height'    : float(self.input_tb.text()) if self.input_tb.text().strip() else 0,
            'email'     : self.input_email.text(),
        }
        # Password hanya ada saat create
        if not self.profil:
            data['password'] = self.input_pass.text()
        return data

# ==========================================
# WINDOW UTAMA
# ==========================================
class ProfilTestApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self._sistem = ProfilSystem()
        self.setWindowTitle("NutriKost — Test Driver Profil")
        self.resize(800, 500)
        self.initUI()

    def initUI(self):
        main_widget = QWidget()
        layout = QVBoxLayout()

        # ===== BARIS TOMBOL AKSI =====
        btn_row = QHBoxLayout()

        self.btn_create = QPushButton("+ Buat Profil")
        self.btn_edit   = QPushButton("✏️ Edit Profil")
        self.btn_delete = QPushButton("🗑️ Hapus Profil")
        self.btn_refresh= QPushButton("🔄 Refresh")

        # Style tombol
        for btn in [self.btn_create, self.btn_edit, self.btn_delete, self.btn_refresh]:
            btn.setStyleSheet("padding: 10px 16px; font-size: 13px; font-weight: bold;")

        self.btn_create.setStyleSheet("padding: 10px 16px; font-size: 13px; font-weight: bold; background-color: #1A7A34; color: white;")
        self.btn_delete.setStyleSheet("padding: 10px 16px; font-size: 13px; font-weight: bold; background-color: #C62828; color: white;")

        self.btn_create.clicked.connect(self.aksi_create)
        self.btn_edit.clicked.connect(self.aksi_edit)
        self.btn_delete.clicked.connect(self.aksi_delete)
        self.btn_refresh.clicked.connect(self.refresh_tabel)

        btn_row.addWidget(self.btn_create)
        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_delete)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_refresh)
        layout.addLayout(btn_row)

        # ===== TABEL DATA PROFIL =====
        self.tabel = QTableWidget()
        self.tabel.setColumnCount(8)  # ← dari 7 jadi 8
        self.tabel.setHorizontalHeaderLabels([
            "ID", "Nama Lengkap", "Usia", "Gender", 
            "Berat (kg)", "Tinggi (cm)", "BMI", "Target Kalori"  # ← tambah 2 kolom
        ])
        self.tabel.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabel.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.tabel.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabel.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabel.cellClicked.connect(self._on_row_klik)
        layout.addWidget(self.tabel)

        # ===== LABEL STATUS =====
        self.label_status = QLabel("Klik baris untuk memilih profil.")
        self.label_status.setStyleSheet("color: #6c757d; font-size: 12px; padding: 4px;")
        layout.addWidget(self.label_status)

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # Load data awal
        self.refresh_tabel()

    def refresh_tabel(self):
        semua_user = self._sistem.data_helper.get_all_users()
        self.tabel.setRowCount(len(semua_user))

        for row, user in enumerate(semua_user):
            # Hitung BMI dan kalori otomatis untuk setiap user
            bmi    = self._sistem.calculatorBMI(user['weight'], user['height'])
            kalori = self._sistem.calculatorHarrisBenedict(
                user['gender'], user['weight'], user['height'], user['age']
            )

            self.tabel.setItem(row, 0, QTableWidgetItem(str(user.get('id_user', ''))))
            self.tabel.setItem(row, 1, QTableWidgetItem(str(user.get('full_name', ''))))
            self.tabel.setItem(row, 2, QTableWidgetItem(str(user.get('age', ''))))
            self.tabel.setItem(row, 3, QTableWidgetItem(str(user.get('gender', ''))))
            self.tabel.setItem(row, 4, QTableWidgetItem(str(user.get('weight', ''))))
            self.tabel.setItem(row, 5, QTableWidgetItem(str(user.get('height', ''))))
            self.tabel.setItem(row, 6, QTableWidgetItem(str(bmi)))     
            self.tabel.setItem(row, 7, QTableWidgetItem(f"{kalori} kkal")) 

        total = len(semua_user)
        self.label_status.setText(f"Total {total} profil tersimpan di database.")

    def _on_row_klik(self, row, _col):
        # Saat baris diklik, set current_profil ke user yang dipilih
        id_user = int(self.tabel.item(row, 0).text())
        self._sistem.current_profil = self._sistem.data_helper.get_user_by_id(id_user)
        nama = self.tabel.item(row, 1).text()
        self.label_status.setText(f"✅ Profil aktif: {nama}")

    def aksi_create(self):
        dialog = FormProfilDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                data  = dialog.get_data()
                hasil = self._sistem.createProfil(data)
                if hasil:
                    # Setelah berhasil simpan, langsung hitung BMI & kalori
                    # dari data yang sama — tidak perlu input lagi!
                    bmi    = self._sistem.calculatorBMI(data['weight'], data['height'])
                    kalori = self._sistem.calculatorHarrisBenedict(
                        data['gender'],
                        data['weight'],
                        data['height'],
                        data['age']
                    )

                    # Tampilkan hasil sekaligus di popup
                    QMessageBox.information(
                        self, "Profil Berhasil Dibuat!",
                        f"✅ Profil berhasil dibuat!\n\n"
                        f"⚖️  BMI kamu        : {bmi}\n"
                        f"🔥  Target kalori   : {kalori} kkal/hari"
                    )
                    self.refresh_tabel()
                else:
                    QMessageBox.warning(self, "Gagal", "❌ Validasi gagal! Cek kembali inputan kamu.")
            except ValueError:
                QMessageBox.warning(self, "Error", "Usia, berat, dan tinggi harus berupa angka!")

    def aksi_edit(self):
        if self._sistem.current_profil is None:
            QMessageBox.warning(self, "Peringatan", "Pilih profil dulu dengan klik baris di tabel!")
            return

        dialog = FormProfilDialog(parent=self, profil=self._sistem.current_profil)
        if dialog.exec_() == QDialog.Accepted:
            try:
                data  = dialog.get_data()
                hasil = self._sistem.updateProfil(data)
                if hasil:
                    QMessageBox.information(self, "Berhasil", "✅ Profil berhasil diupdate!")
                    self.refresh_tabel()
                else:
                    QMessageBox.warning(self, "Gagal", "❌ Update gagal! Cek kembali inputan kamu.")
            except ValueError:
                QMessageBox.warning(self, "Error", "Usia, berat, dan tinggi harus berupa angka!")

    def aksi_delete(self):
        if self._sistem.current_profil is None:
            QMessageBox.warning(self, "Peringatan", "Pilih profil dulu dengan klik baris di tabel!")
            return

        nama = self._sistem.current_profil.get('full_name', '')
        konfirmasi = QMessageBox.question(
            self, "Konfirmasi Hapus",
            f"Yakin ingin menghapus profil '{nama}'?\nSemua log harian akan ikut terhapus.",
            QMessageBox.Yes | QMessageBox.No
        )
        if konfirmasi == QMessageBox.Yes:
            self._sistem.deleteProfil()
            QMessageBox.information(self, "Berhasil", "✅ Profil berhasil dihapus!")
            self.refresh_tabel()


# ==========================================
# JALANKAN
# ==========================================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ProfilTestApp()
    window.show()
    sys.exit(app.exec_())