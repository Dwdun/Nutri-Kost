import sys
import os

#tempat main.py berada = root proyek
BASE = os.path.dirname(__file__)   

sys.path.insert(0, os.path.join(BASE, "faqih_integrator"))  # main_window, search_page
sys.path.insert(0, os.path.join(BASE, "bima_scrapper"))     # models.py (DBHelper, JsonHelper)
sys.path.insert(0, os.path.join(BASE, "irfan_calculator"))  # log_page 
sys.path.insert(0, os.path.join(BASE, "anindya_profil"))    # profil_page 
sys.path.insert(0, os.path.join(BASE, "fatih_GUI"))         # dashboard, chart 

from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt5.QtGui import QFontDatabase

from main_window import MainWindow
from profil_system import ProfilSystem
from test import HalamanLogin, HalamanRegister, HalamanDataDiri, AuthBaseWidget

class AppLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NutriKost")
        self.resize(1200, 720)
        self._sistem = ProfilSystem()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.init_auth_flow()
        self.show_login()

    def init_auth_flow(self):
        self.login_p = HalamanLogin(self._sistem)
        self.register_p = HalamanRegister()
        self.datadiri_p = HalamanDataDiri(self._sistem)

        self.login_wrapper = AuthBaseWidget(self.login_p)
        self.register_wrapper = AuthBaseWidget(self.register_p)
        self.datadiri_wrapper = AuthBaseWidget(self.datadiri_p)

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

    def show_dashboard(self):
        self.dashboard = MainWindow(self._sistem)
        self.dashboard.logout_signal.connect(self.handle_logout)
        self.stack.addWidget(self.dashboard)
        self.stack.setCurrentWidget(self.dashboard)
        
    def handle_logout(self):
        self.stack.removeWidget(self.dashboard)
        self.dashboard.deleteLater()
        self.dashboard = None
        self.show_login()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NutriKost")

    QFontDatabase.addApplicationFont(os.path.join(BASE, "assets/fonts/MontserratAlternates-Regular.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(BASE, "assets/fonts/MontserratAlternates-Bold.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(BASE, "assets/fonts/Poppins-Regular.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(BASE, "assets/fonts/Poppins-Medium.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(BASE, "assets/fonts/Poppins-SemiBold.ttf"))
    QFontDatabase.addApplicationFont(os.path.join(BASE, "assets/fonts/Poppins-Bold.ttf"))

    #tampilan lintas OS yang konsisten (Windows, Linux, Mac sama ratanya)
    app.setStyle("Fusion")

    # Stylesheet global — berlaku untuk SEMUA widget di seluruh aplikasi.
    # Tiap anggota tidak perlu set font/scrollbar sendiri-sendiri.
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

    window = AppLauncher()
    window.showMaximized()

    # app.exec_() memulai event loop — aplikasi "hidup" di sini sampai window ditutup.
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()