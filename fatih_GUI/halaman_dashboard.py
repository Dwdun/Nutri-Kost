"""
Halaman Dashboard — Konten utama Home Dashboard.

Layout mengikuti prototipe Home Dashboard.png:
  Baris 1: Header → "Halo, {nama}" + deskripsi | tanggal hari ini | + Tambah Makanan
  Baris 2: KaloriHariIni | DetailMakro (Makronutrien hari ini) | FunFact
  Baris 3: NavCardWidget (3 kartu navigasi cepat)
  Baris 4: KaloriMingguan | KomposisiGizi | TopMakanan
"""

import sys
import os
import sqlite3
import locale
from datetime import datetime

# Tambahkan root proyek ke sys.path agar import fatih_GUI dikenali saat run mandiri
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QApplication, QScrollArea, QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap, QCursor

from fatih_GUI.widgets import (
    KaloriHariIniWidget,
    KaloriMingguanWidget,
    KomposisiGiziWidget,
    DetailMakroWidget,
    TopMakananWidget,
    NavCardWidget,
    FunFactWidget,
)

# ─────────────────────────────────────────────
#  DESIGN TOKENS
# ─────────────────────────────────────────────
C_GREEN       = '#1A7A34'
C_GREEN_HOVER = '#1E8C3D'
C_TEXT_DARK   = '#1C1C1C'
C_TEXT_SUB    = '#555555'
C_WHITE       = '#FFFFFF'

# ─────────────────────────────────────────────
#  PATH
# ─────────────────────────────────────────────
_BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
_ICONS_DIR  = os.path.join(_BASE_DIR, '..', 'assets', 'icons')
_FONTS_DIR  = os.path.join(_BASE_DIR, '..', 'assets', 'fonts')
_DEFAULT_DB = os.path.join(_BASE_DIR, '..', 'bima_scrapper', 'nutrikost.db')


# ─────────────────────────────────────────────
#  DATA HELPER
# ─────────────────────────────────────────────
def _ambil_nama_user(db_path: str, id_user: int = 1) -> str:
    """Ambil nama user dari ProfilUser."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT full_name FROM ProfilUser WHERE id_user = ?", (id_user,)
        )
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            return str(row[0])
    except Exception:
        pass
    return 'User'


def _tanggal_hari_ini() -> str:
    """Kembalikan tanggal hari ini dalam format 'Selasa, 14 April 2026'."""
    HARI = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    BULAN = [
        '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
    ]
    now = datetime.now()
    hari = HARI[now.weekday()]
    bulan = BULAN[now.month]
    return f'{hari}, {now.day} {bulan} {now.year}'


# ═════════════════════════════════════════════
#  HALAMAN DASHBOARD
# ═════════════════════════════════════════════
class HalamanDashboard(QWidget):
    """
    Konten halaman Home Dashboard.

    Signal:
        navigate_to(str)       — minta main_window pindah halaman.
                                 Misal: 'log', 'kalori_mingguan', 'riwayat'
        tambah_makanan_clicked — saat tombol "+ Tambah Makanan" diklik.
    """

    navigate_to = pyqtSignal(str)
    tambah_makanan_clicked = pyqtSignal()

    _id_user = 1

    def __init__(self, id_user: int = 1, db_path: str = None, parent=None):
        super().__init__(parent)
        self._id_user = id_user
        self._db_path = db_path or os.path.normpath(_DEFAULT_DB)

        self.setStyleSheet('background: transparent;')

        self._build_ui()

    # ─────────────────────────────────────────
    #  BUILD UI
    # ─────────────────────────────────────────
    def _build_ui(self):
        # Scroll area agar konten bisa di-scroll jika panjang
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.15);
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }
        """)

        content = QWidget()
        content.setStyleSheet('background: transparent;')
        content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        content.setMaximumWidth(1600)
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(32, 28, 32, 32)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignTop)

        # ── BARIS 1: Header ──
        header = self._build_header()
        main_layout.addLayout(header)

        # ── BARIS 2: Kalori Hari Ini | Detail Makro | Fun Fact ──
        row2 = self._build_row_widgets()
        main_layout.addLayout(row2)

        # ── BARIS 3: Nav Card (3 kartu navigasi) ──
        self._nav_card = NavCardWidget(id_user=self._id_user, db_path=self._db_path)
        self._nav_card.card_clicked.connect(self._on_navigate)
        self._nav_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._nav_card.setMinimumWidth(0)
        main_layout.addWidget(self._nav_card)

        # ── BARIS 4: Kalori Mingguan | Komposisi Gizi | Top Makanan ──
        row4 = self._build_row_charts()
        main_layout.addLayout(row4)

        main_layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    # ─────────────────────────────────────────
    #  HEADER — Halo, Nama | Tanggal | + Tambah Makanan
    # ─────────────────────────────────────────
    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(12)

        # Kiri: Judul & deskripsi
        left = QVBoxLayout()
        left.setSpacing(4)

        nama = _ambil_nama_user(self._db_path, self._id_user)
        self.title_lbl = QLabel(f'Halo, {nama}')
        self.title_lbl.setStyleSheet(f"color: {C_TEXT_DARK}; background: transparent; font-family: 'Montserrat Alternates'; font-size: 32px; font-weight: bold;")

        desc = QLabel('Pantau asupan nutrisimu hari ini')
        desc.setStyleSheet(f"color: {C_TEXT_SUB}; background: transparent; font-family: 'Montserrat'; font-size: 14px;")

        left.addWidget(self.title_lbl)
        left.addWidget(desc)
        header.addLayout(left)
        header.addStretch()

        # Tengah: Tanggal hari ini
        date_row = QHBoxLayout()
        date_row.setSpacing(6)

        cal_icon = QLabel()
        cal_icon_path = os.path.join(_ICONS_DIR, 'uim_calender.png')
        if os.path.exists(cal_icon_path):
            pix = QPixmap(cal_icon_path).scaled(
                18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            cal_icon.setPixmap(pix)
        cal_icon.setStyleSheet('background: transparent;')

        date_lbl = QLabel(_tanggal_hari_ini())
        date_lbl.setFont(self._font_body(11))
        date_lbl.setStyleSheet(f'color: {C_GREEN}; background: transparent;')

        date_row.addWidget(cal_icon)
        date_row.addWidget(date_lbl)
        header.addLayout(date_row)

        header.addSpacing(16)

        # Kanan: Tombol + Tambah Makanan
        btn_tambah = QPushButton('+  Tambah Makanan')
        btn_tambah.setFont(QFont('Poppins', 11, QFont.Bold))
        btn_tambah.setCursor(QCursor(Qt.PointingHandCursor))
        btn_tambah.setStyleSheet(f"""
            QPushButton {{
                background: {C_GREEN};
                color: {C_WHITE};
                border: none;
                border-radius: 12px;
                padding: 12px 28px;
                font-family: 'Poppins';
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {C_GREEN_HOVER};
            }}
        """)
        btn_tambah.clicked.connect(self._on_tambah_makanan)
        header.addWidget(btn_tambah)

        return header

    # ─────────────────────────────────────────
    #  BARIS 2: KaloriHariIni | DetailMakro | FunFact
    # ─────────────────────────────────────────
    def _build_row_widgets(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(16)

        # Kolom kiri: Kalori Hari Ini (donut chart)
        self._w_kalori_hari_ini = KaloriHariIniWidget(
            id_user=self._id_user, db_path=self._db_path
        )
        self._w_kalori_hari_ini.setMinimumWidth(0)
        self._w_kalori_hari_ini.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        row.addWidget(self._w_kalori_hari_ini, 28)

        # Kolom tengah: Detail Makro (progress bars)
        self._w_detail_makro = DetailMakroWidget(
            id_user=self._id_user, db_path=self._db_path
        )
        self._w_detail_makro.setMinimumWidth(0)
        self._w_detail_makro.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        row.addWidget(self._w_detail_makro, 45)

        # Kolom kanan: Fun Fact
        self._w_fun_fact = FunFactWidget()
        self._w_fun_fact.setMinimumWidth(0)
        self._w_fun_fact.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        row.addWidget(self._w_fun_fact, 27)

        return row

    # ─────────────────────────────────────────
    #  BARIS 4: KaloriMingguan | KomposisiGizi | TopMakanan
    # ─────────────────────────────────────────
    def _build_row_charts(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(16)

        # Kalori Mingguan (bar chart)
        self._w_kalori_mingguan = KaloriMingguanWidget(
            id_user=self._id_user, db_path=self._db_path
        )
        self._w_kalori_mingguan.setMinimumWidth(0)
        self._w_kalori_mingguan.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        row.addWidget(self._w_kalori_mingguan, 35)

        # Komposisi Gizi (pie chart)
        self._w_komposisi = KomposisiGiziWidget(
            id_user=self._id_user, db_path=self._db_path
        )
        self._w_komposisi.setMinimumWidth(0)
        self._w_komposisi.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        row.addWidget(self._w_komposisi, 40)

        # Top Makanan (ranked list)
        self._w_top_makanan = TopMakananWidget(
            id_user=self._id_user, db_path=self._db_path
        )
        self._w_top_makanan.setMinimumWidth(0)
        self._w_top_makanan.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        row.addWidget(self._w_top_makanan, 25)

        return row

    # ─────────────────────────────────────────
    #  ACTIONS
    # ─────────────────────────────────────────
    def _on_navigate(self, page_key: str):
        """Dipanggil saat NavCard diklik."""
        self.navigate_to.emit(page_key)

    def _on_tambah_makanan(self):
        """Dipanggil saat tombol + Tambah Makanan diklik."""
        self.tambah_makanan_clicked.emit()

    # ─────────────────────────────────────────
    #  REFRESH
    # ─────────────────────────────────────────
    def refresh(self, id_user: int = None):
        """Reload semua widget dari database."""
        if id_user is not None:
            self._id_user = id_user
        if hasattr(self, 'title_lbl') and self.title_lbl:
            nama = _ambil_nama_user(self._db_path, self._id_user)
            self.title_lbl.setText(f'Halo, {nama}')
        if hasattr(self, '_w_kalori_hari_ini'):
            self._w_kalori_hari_ini.refresh(id_user=id_user)
        if hasattr(self, '_w_detail_makro'):
            self._w_detail_makro.refresh(id_user=id_user)
        if hasattr(self, '_w_fun_fact'):
            self._w_fun_fact.refresh()
        if hasattr(self, '_nav_card'):
            self._nav_card.refresh(id_user=id_user)
        if hasattr(self, '_w_kalori_mingguan'):
            self._w_kalori_mingguan.refresh(id_user=id_user)
        if hasattr(self, '_w_komposisi'):
            self._w_komposisi.refresh(id_user=id_user)
        if hasattr(self, '_w_top_makanan'):
            self._w_top_makanan.refresh(id_user=id_user)

    # ─────────────────────────────────────────
    #  FONT HELPERS
    # ─────────────────────────────────────────
    @staticmethod
    def _font_title(size: int = 22) -> QFont:
        f = QFont('Montserrat Alternates', size, QFont.Bold)
        f.setStyleHint(QFont.SansSerif)
        return f

    @staticmethod
    def _font_body(size: int = 10) -> QFont:
        f = QFont('Poppins', size)
        f.setStyleHint(QFont.SansSerif)
        return f


# ═════════════════════════════════════════════
#  STANDALONE PREVIEW
# ═════════════════════════════════════════════
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Load custom fonts
    if os.path.isdir(_FONTS_DIR):
        for fname in os.listdir(_FONTS_DIR):
            if fname.lower().endswith(('.ttf', '.otf')):
                QFontDatabase.addApplicationFont(os.path.join(_FONTS_DIR, fname))

    app.setStyle('Fusion')

    window = QWidget()
    window.setWindowTitle('Preview — Home Dashboard')
    window.resize(1100, 800)
    window.setStyleSheet('background: #F2F4F0;')

    lay = QVBoxLayout(window)
    lay.setContentsMargins(0, 0, 0, 0)

    dashboard = HalamanDashboard(id_user=1)
    dashboard.navigate_to.connect(lambda key: print(f'Navigasi ke: {key}'))
    dashboard.tambah_makanan_clicked.connect(lambda: print('Tambah Makanan diklik!'))
    lay.addWidget(dashboard)

    window.show()
    sys.exit(app.exec_())
