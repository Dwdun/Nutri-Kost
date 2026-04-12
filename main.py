import sys
import os

BASE = os.path.dirname(__file__)   # direktori tempat main.py berada = root proyek

sys.path.insert(0, os.path.join(BASE, "faqih_integrator"))  # main_window, search_page
sys.path.insert(0, os.path.join(BASE, "bima_scrapper"))     # models.py (DBHelper, JsonHelper)
sys.path.insert(0, os.path.join(BASE, "irfan_calculator"))  # log_page (nanti)
sys.path.insert(0, os.path.join(BASE, "anindya_profil"))    # profil_page (nanti)
sys.path.insert(0, os.path.join(BASE, "fatih_GUI"))         # dashboard, chart (nanti)

from PyQt5.QtWidgets import QApplication
from main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NutriKost")

    # Fusion: tampilan lintas OS yang konsisten (Windows, Linux, Mac sama ratanya)
    app.setStyle("Fusion")

    # Stylesheet global — berlaku untuk SEMUA widget di seluruh aplikasi.
    # Tiap anggota tidak perlu set font/scrollbar sendiri-sendiri.
    app.setStyleSheet("""
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }
        QScrollBar:vertical {
            border: none;
            background: #f0f0f0;
            width: 8px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background: #c0c0c0;
            border-radius: 4px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: #a0a0a0;
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