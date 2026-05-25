import sys
import os
import sqlite3
import traceback

# ─── PyInstaller compatibility ───────────────────────────────────────────────
# Saat dikemas sebagai .exe, semua file statis diekstrak ke folder temp _MEIPASS.
# BASE_RESOURCES → folder resource (assets, schema SQL, dll.) — bisa berupa _MEIPASS
# BASE_WRITABLE  → folder di sebelah .exe / script — tempat menyimpan database
def _resource_path(relative_path: str) -> str:
    """Kembalikan path absolut ke resource (bundled atau development)."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)

def _writable_path(relative_path: str) -> str:
    """Kembalikan path di folder yang bisa ditulis (sejajar .exe / main.py)."""
    if getattr(sys, 'frozen', False):
        # Saat jalan sebagai .exe → pakai folder yang sama dengan .exe
        base = os.path.dirname(sys.executable)
    else:
        # Saat development → pakai folder root proyek
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)

# Shortcut yang dipakai di seluruh file
BASE = _resource_path('.')   # untuk assets/fonts/icons (read-only OK)


#add sub folder to py
sys.path.insert(0, os.path.join(BASE, "faqih_integrator"))  # main_window, search_page
sys.path.insert(0, os.path.join(BASE, "bima_scrapper"))     # models.py (DBHelper, JsonHelper)
sys.path.insert(0, os.path.join(BASE, "irfan_calculator"))  # log_page 
sys.path.insert(0, os.path.join(BASE, "anindya_profil"))    # profil_page 
sys.path.insert(0, os.path.join(BASE, "fatih_GUI"))         # dashboard, chart 

from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt5.QtGui import QFontDatabase, QIcon

#import awal
from faqih_integrator.main_window import MainWindow
from anindya_profil.profil_system import ProfilSystem
from anindya_profil.test import HalamanLogin, HalamanRegister, HalamanDataDiri, AuthBaseWidget

# Fungsi untuk inisialisasi database
def init_database():
    # Schema SQL ada di dalam bundle (read-only)
    sql_path = _resource_path(os.path.join("bima_scrapper", "db_schema.sql"))
    # Database disimpan di folder yang bisa ditulis (sejajar .exe)
    db_dir  = _writable_path("bima_scrapper")
    db_path = os.path.join(db_dir, "nutrikost.db")

    # Pastikan folder tujuan ada
    os.makedirs(db_dir, exist_ok=True)

    if not os.path.exists(sql_path):
        print(f"Peringatan: File schema tidak ditemukan di {sql_path}")
        return

    try:
        with open(sql_path, 'r', encoding='utf-8') as sql_file:
            sql_script = sql_file.read()

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # executescript dengan IF NOT EXISTS sudah ada di schema, jadi aman dijalankan ulang
        try:
            cursor.executescript(sql_script)
            conn.commit()
        except Exception:
            # Tabel sudah ada — tidak masalah, skip saja
            pass
        conn.close()
        print(f"Database berhasil diinisialisasi: {db_path}")
    except Exception as e:
        print(f"Terjadi kesalahan saat inisialisasi database: {e}")

#mengatur perpindahan
class AppLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NutriKost")
        self.resize(1200, 720)
        
        # Set high-quality taskbar icon for Windows
        ico_path = _resource_path(os.path.join("assets", "icons", "Logo.ico"))
        png_path = _resource_path(os.path.join("assets", "icons", "Logo.png"))
        icon_path = ico_path if os.path.exists(ico_path) else png_path
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        #sumber data
        self._sistem = ProfilSystem()
        
        #inisiasi admin
        if not self._sistem.cekEmailTerdaftar('admin123@gmail.com'):
            admin_data = {
                'full_name': 'Admin NutriKost',
                'age': 30,
                'gender': 'Laki-laki',
                'weight': 60,
                'height': 170,
                'activity': 'Sedentary (Jarang Olahraga)',
                'email': 'admin123@gmail.com',
                'password': 'admin123'
            }
            self._sistem.createProfil(admin_data)
            self._sistem.current_profil = None  # Reset profil agar tidak langsung login

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.init_auth_flow()
        #halaman pertama dibuka
        self.show_login()

    def init_auth_flow(self):
        #halaman auth
        self.login_p = HalamanLogin(self._sistem)
        self.register_p = HalamanRegister()
        self.datadiri_p = HalamanDataDiri(self._sistem)

        #wrapper
        self.login_wrapper = AuthBaseWidget(self.login_p)
        self.register_wrapper = AuthBaseWidget(self.register_p)
        self.datadiri_wrapper = AuthBaseWidget(self.datadiri_p)

        #koneksi sinyal
        self.login_p.go_register.connect(self.show_register)
        self.login_p.login_success.connect(self.show_dashboard)
        
        self.register_p.go_datadiri.connect(self.show_datadiri)
        self.register_p.go_back.connect(self.show_login)
        
        self.datadiri_p.register_success.connect(self.show_dashboard)
        self.datadiri_p.go_back.connect(self.show_register)

        self.stack.addWidget(self.login_wrapper)
        self.stack.addWidget(self.register_wrapper)
        self.stack.addWidget(self.datadiri_wrapper)

    def show_login(self):
        self.stack.setCurrentWidget(self.login_wrapper)
        
    def show_register(self):
        self.stack.setCurrentWidget(self.register_wrapper)

    def show_datadiri(self, data):
        self.datadiri_p.register_data = data
        self.stack.setCurrentWidget(self.datadiri_wrapper)

    #main window baru dibuat
    def show_dashboard(self):
        # Bersihkan dashboard lama jika masih ada (misal register akun baru tanpa logout)
        if hasattr(self, 'dashboard') and self.dashboard is not None:
            self.stack.removeWidget(self.dashboard)
            self.dashboard.deleteLater()
            self.dashboard = None

        try:
            self.dashboard = MainWindow(self._sistem)
            self.dashboard.logout_signal.connect(self.handle_logout)
            self.stack.addWidget(self.dashboard)
            self.stack.setCurrentWidget(self.dashboard)
        except Exception as e:
            # Tulis error ke file log agar bisa di-debug
            log_path = _writable_path('nutrikost_error.log')
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"\n=== Error saat membuka dashboard ===\n")
                f.write(traceback.format_exc())
            # Tampilkan pesan error ke user
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Gagal Membuka Dashboard",
                f"Terjadi kesalahan:\n{e}\n\nDetail disimpan di: {log_path}"
            )
    
    #handling logout
    def handle_logout(self):
        self.stack.removeWidget(self.dashboard) #keluar dari tampila
        self.dashboard.deleteLater() 
        self.dashboard = None
        self.show_login()

def main():
    import ctypes
    # HARUS dipanggil SEBELUM QApplication agar taskbar icon di Windows berubah
    try:
        myappid = 'nutrikost.app.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
    
    # Memanggil fungsi inisiasi DB sebelum masuk GUI
    init_database()

    app = QApplication(sys.argv)
    
    # Gunakan .ico untuk taskbar Windows (lebih reliable dari .png)
    ico_path = _resource_path(os.path.join("assets", "icons", "Logo.ico"))
    png_path = _resource_path(os.path.join("assets", "icons", "Logo.png"))
    icon_path = ico_path if os.path.exists(ico_path) else png_path
    app_icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
    app.setWindowIcon(app_icon)

    app.setApplicationName("NutriKost")

    #font dan icon
    fonts_dir = _resource_path("assets/fonts")
    QFontDatabase.addApplicationFont(os.path.join(fonts_dir, "MontserratAlternates-Regular.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(fonts_dir, "MontserratAlternates-Bold.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(fonts_dir, "Poppins-Regular.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(fonts_dir, "Poppins-Medium.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(fonts_dir, "Poppins-SemiBold.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(fonts_dir, "Poppins-Bold.ttf"))

    #tampilan lintas OS 
    app.setStyle("Fusion")
    
    # Stylesheet global 
    app.setStyleSheet("""
        QWidget {
            font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }
        QScrollBar:vertical {
            border: none;
            background: transparent;
            width: 8px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 4px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: rgba(0, 0, 0, 0.3);
        }
        /* Sembunyikan tombol panah scrollbar agar terlihat minimalis */
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        /* Set QMessageBox background to white */
        QMessageBox {
            background-color: white;
        }
        QMessageBox QLabel {
            color: #333333;
            background-color: transparent;
        }
        QMessageBox QPushButton {
            background-color: #1A7A34;
            color: white;
            border-radius: 4px;
            padding: 5px 15px;
            min-width: 60px;
        }
        QMessageBox QPushButton:hover {
            background-color: #145925;
        }
    """)

    #menjalankan aplikasi
    window = AppLauncher()
    window.setWindowIcon(app_icon)   # set langsung di window agar taskbar Windows ter-update
    window.showMaximized()

    # app.exec_() memulai event loop — aplikasi "hidup" di sini sampai window ditutup.
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()