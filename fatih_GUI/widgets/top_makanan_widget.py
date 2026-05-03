"""
Widget Top 10 Makanan — Menampilkan 10 makanan yang paling sering dikonsumsi
oleh user dalam 30 hari terakhir.

Mengikuti referensi "Top 10 table.png".
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy, QApplication,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase

# ─────────────────────────────────────────────
#  DESIGN TOKENS
# ─────────────────────────────────────────────
C_GREEN      = '#1A7A34'
C_TEXT_DARK  = '#1C1C1C'
C_WHITE      = '#FFFFFF'

# Warna untuk Rank 1
C_RANK1_TEXT = '#FFC107'
C_RANK1_BG   = '#FFF8E1'

# Warna untuk Rank 2-10
C_RANKN_TEXT = '#2ECC71'
C_RANKN_BG   = '#E8F8F5'

# ─────────────────────────────────────────────
#  PATH — default database & fonts
# ─────────────────────────────────────────────
_BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_DB = os.path.join(_BASE_DIR, '..', '..', 'bima_scrapper', 'nutrikost.db')
_FONTS_DIR  = os.path.join(_BASE_DIR, '..', '..', 'assets', 'fonts')


# ─────────────────────────────────────────────
#  DATA HELPER
# ─────────────────────────────────────────────
def _ambil_top_10_makanan(db_path: str, id_user: int = 1) -> list:
    """
    Query Top 10 makanan yang sering dimakan dalam 30 hari terakhir.
    Mengembalikan list of dict:
    [{'name': str, 'cal': float, 'freq': int}, ...]
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                M.food_name,
                M.cal,
                COUNT(L.id_log) as freq
            FROM LogHarian L
            JOIN Makanan M ON L.kode_makanan = M.code
            WHERE L.id_user = ? 
              AND date(L.meal_time) BETWEEN date('now', '-30 days') AND date('now')
            GROUP BY L.kode_makanan
            ORDER BY freq DESC, M.food_name ASC
            LIMIT 10
        """
        cursor.execute(query, (id_user,))
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            return [{'name': r[0], 'cal': float(r[1]), 'freq': int(r[2])} for r in rows]
        else:
            return _get_dummy_data()
            
    except Exception:
        return _get_dummy_data()


def _get_dummy_data():
    """Nilai dummy sesuai prototipe jika database kosong."""
    return [
        {'name': 'Nasi Putih',      'cal': 260, 'freq': 7},
        {'name': 'Nasi Goreng',     'cal': 350, 'freq': 5},
        {'name': 'Ayam Penyet',     'cal': 500, 'freq': 4},
        {'name': 'Sate Ayam',       'cal': 400, 'freq': 6},
        {'name': 'Rendang',         'cal': 600, 'freq': 3},
        {'name': 'Gado-Gado',       'cal': 300, 'freq': 2},
        {'name': 'Bakso',           'cal': 450, 'freq': 5},
        {'name': 'Mie Goreng',      'cal': 550, 'freq': 3},
        {'name': 'Sup Buntut',      'cal': 700, 'freq': 2},
        {'name': 'Kwetiau Goreng',  'cal': 480, 'freq': 4},
    ]


# ═════════════════════════════════════════════
#  WIDGET UTAMA
# ═════════════════════════════════════════════
class TopMakananWidget(QWidget):
    """
    Widget reusable yang menampilkan Top 10 makanan yang dikonsumsi
    dalam 30 hari terakhir.
    """

    def __init__(self, id_user: int = 1, db_path: str = None, parent=None):
        super().__init__(parent)
        self._id_user = id_user
        self._db_path = db_path or os.path.normpath(_DEFAULT_DB)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setStyleSheet(f"""
            QWidget {{
                background: {C_WHITE};
            }}
        """)

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 16, 0, 0)
        root.setSpacing(0)

        # ── Container utama dengan border rounded ──
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: {C_WHITE};
                border: 1.5px solid {C_GREEN};
                border-radius: 16px;
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(24, 20, 24, 24)
        container_layout.setSpacing(16)
        container_layout.setAlignment(Qt.AlignTop)

        # ── Judul ──
        title = QLabel('Top 10 Makanan yang dikonsumsi')
        title.setFont(self._font_title(18))
        title.setStyleSheet(f'color: {C_TEXT_DARK}; border: none; background: transparent;')
        container_layout.addWidget(title)

        # ── List Makanan ──
        data = _ambil_top_10_makanan(self._db_path, self._id_user)
        
        # Urutkan berdasarkan freq descending (karena dummy mungkin belum terurut)
        data = sorted(data, key=lambda x: x['freq'], reverse=True)
        
        for i, item in enumerate(data):
            rank = i + 1
            row_widget = self._create_row(rank, item['name'], item['cal'], item['freq'])
            container_layout.addWidget(row_widget)

        root.addWidget(container)

    def _create_row(self, rank: int, name: str, cal: float, freq: int) -> QWidget:
        row = QWidget()
        row.setStyleSheet('background: transparent; border: none;')
        
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 4, 0, 4)
        row_layout.setSpacing(16)
        
        # Tentukan warna berdasarkan rank
        if rank == 1:
            color_text = C_RANK1_TEXT
            color_bg   = C_RANK1_BG
        else:
            color_text = C_RANKN_TEXT
            color_bg   = C_RANKN_BG
            
        # ── Badge Rank ──
        badge = QLabel(str(rank))
        badge.setFixedSize(36, 36)
        badge.setAlignment(Qt.AlignCenter)
        badge.setFont(self._font_body_bold(12))
        badge.setStyleSheet(f"""
            background-color: {color_bg};
            color: {color_text};
            border-radius: 8px;
        """)
        row_layout.addWidget(badge)
        
        # ── Nama Makanan ──
        name_lbl = QLabel(name)
        name_lbl.setFont(self._font_body_bold(12))
        name_lbl.setStyleSheet(f"color: {color_text};")
        row_layout.addWidget(name_lbl)
        
        row_layout.addStretch()
        
        # ── Kalori ──
        cal_lbl = QLabel(f"{int(cal)} kcal")
        cal_lbl.setFont(self._font_body(12))
        cal_lbl.setStyleSheet(f"color: {color_text};")
        row_layout.addWidget(cal_lbl)
        
        # Spasi ekstra antara kalori dan frekuensi
        row_layout.addSpacing(16)
        
        # ── Frekuensi ──
        freq_lbl = QLabel(f"{freq}x bulan ini")
        freq_lbl.setFont(self._font_body(12))
        freq_lbl.setStyleSheet(f"color: {color_text};")
        row_layout.addWidget(freq_lbl)
        
        return row

    def refresh(self):
        """Reload data dari database dan rebuild UI."""
        layout = self.layout()
        if layout:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        self._build_ui()

    # ── Font helper ───────────────────────────
    @staticmethod
    def _font_title(size: int = 18) -> QFont:
        f = QFont('Montserrat Alternates', size, QFont.Bold)
        f.setStyleHint(QFont.SansSerif)
        return f

    @staticmethod
    def _font_body(size: int = 10) -> QFont:
        f = QFont('Poppins', size)
        f.setStyleHint(QFont.SansSerif)
        return f

    @staticmethod
    def _font_body_bold(size: int = 10) -> QFont:
        f = QFont('Poppins', size, QFont.Bold)
        f.setStyleHint(QFont.SansSerif)
        return f


# ═════════════════════════════════════════════
#  STANDALONE PREVIEW
# ═════════════════════════════════════════════
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Load custom fonts untuk standalone preview
    if os.path.isdir(_FONTS_DIR):
        for fname in os.listdir(_FONTS_DIR):
            if fname.lower().endswith(('.ttf', '.otf')):
                QFontDatabase.addApplicationFont(os.path.join(_FONTS_DIR, fname))

    app.setStyle('Fusion')

    # Preview window sederhana
    window = QWidget()
    window.setWindowTitle('Preview — Top 10 Makanan Widget')
    window.resize(900, 700)
    window.setStyleSheet('background: #F2F4F0;')

    lay = QVBoxLayout(window)
    lay.setContentsMargins(32, 32, 32, 32)

    widget = TopMakananWidget(id_user=1)
    lay.addWidget(widget)
    lay.addStretch()

    window.show()
    sys.exit(app.exec_())
