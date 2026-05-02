import sys
import os

#tempat main.py berada = root proyek
BASE = os.path.dirname(__file__)   

sys.path.insert(0, os.path.join(BASE, "faqih_integrator"))  # main_window, search_page
sys.path.insert(0, os.path.join(BASE, "bima_scrapper"))     # models.py (DBHelper, JsonHelper)
sys.path.insert(0, os.path.join(BASE, "irfan_calculator"))  # log_page 
sys.path.insert(0, os.path.join(BASE, "anindya_profil"))    # profil_page 
sys.path.insert(0, os.path.join(BASE, "fatih_GUI"))         # dashboard, chart 

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase

from main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NutriKost")

    QFontDatabase.addApplicationFont("assets/fonts/MontserratAlternates-Regular.ttf")
    QFontDatabase.addApplicationFont("assets/fonts/MontserratAlternates-Bold.ttf")
    QFontDatabase.addApplicationFont("assets/fonts/Poppins-Regular.ttf")
    QFontDatabase.addApplicationFont("assets/fonts/Poppins-Medium.ttf")
    QFontDatabase.addApplicationFont("assets/fonts/Poppins-SemiBold.ttf")
    QFontDatabase.addApplicationFont("assets/fonts/Poppins-Bold.ttf")

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
    """)

    window = MainWindow()
    window.show()

    # app.exec_() memulai event loop — aplikasi "hidup" di sini sampai window ditutup.
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()