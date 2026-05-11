"""
Widget Detail Makro — Progress bar detail nutrisi rata-rata/hari minggu ini.

Mengikuti prototipe "Detail Makro.png".
Menampilkan 5 komponen: Protein, Karbohidrat, Lemak, Serat, Air.
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy, QApplication, QProgressBar,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase

# ─────────────────────────────────────────────
#  DESIGN TOKENS
# ─────────────────────────────────────────────
C_GREEN      = '#1A7A34'
C_TEXT_DARK  = '#1C1C1C'
C_TEXT_SUB   = '#555555'
C_WHITE      = '#FFFFFF'

# Warna Spesifik Nutrisi
COLOR_MAP = {
    'protein': {'color': '#2ECC71', 'bg': '#E8F8F5'},
    'karbo':   {'color': '#2196F3', 'bg': '#E3F2FD'},
    'lemak':   {'color': '#FFC107', 'bg': '#FFF8E1'},
    'serat':   {'color': '#AEEA00', 'bg': '#F9FBE7'},
    'air':     {'color': '#26C6DA', 'bg': '#E0F7FA'},
}

# ─────────────────────────────────────────────
#  PATH — default database & fonts
# ─────────────────────────────────────────────
_BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_DB = os.path.join(_BASE_DIR, '..', '..', 'bima_scrapper', 'nutrikost.db')
_FONTS_DIR  = os.path.join(_BASE_DIR, '..', '..', 'assets', 'fonts')


# ─────────────────────────────────────────────
#  DATA HELPER
# ─────────────────────────────────────────────
def _ambil_detail_makro(db_path: str, id_user: int = 1) -> dict:
    """
    Query rata-rata asupan gizi 7 hari terakhir dan target per hari.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Ambil target dari ProfilUser
        cursor.execute("SELECT protein, carb, fat FROM ProfilUser WHERE id_user = ?", (id_user,))
        row_user = cursor.fetchone()
        
        target_protein = 75.0
        target_carb = 300.0
        target_fat = 70.0
        
        if row_user:
            if row_user[0]: target_protein = float(row_user[0])
            if row_user[1]: target_carb = float(row_user[1])
            if row_user[2]: target_fat = float(row_user[2])
            
        target_serat = 30.0
        target_air = 2.0
        
        # 2. Ambil total dari LogHarian (7 hari terakhir)
        query = """
            SELECT
                COALESCE(SUM(L.protein), 0) as total_protein,
                COALESCE(SUM(L.carb), 0)    as total_carb,
                COALESCE(SUM(L.fat), 0)     as total_fat,
                COALESCE(SUM((L.portion / 100.0) * COALESCE(M.fiber, 0)), 0) as total_fiber,
                COALESCE(SUM((L.portion / 100.0) * COALESCE(M.water, 0)), 0) as total_water,
                COUNT(DISTINCT date(L.meal_time)) as active_days
            FROM LogHarian L
            LEFT JOIN Makanan M ON L.kode_makanan = M.code
            WHERE L.id_user = ?
              AND date(L.meal_time) BETWEEN date('now', '-6 days') AND date('now')
        """
        cursor.execute(query, (id_user,))
        row_log = cursor.fetchone()
        conn.close()
        
        if row_log and row_log[5] > 0:
            # Dibagi 7 untuk mendapatkan rata-rata per hari
            protein = float(row_log[0]) / 7.0
            carb = float(row_log[1]) / 7.0
            fat = float(row_log[2]) / 7.0
            serat = float(row_log[3]) / 7.0
            air_l = (float(row_log[4]) / 1000.0) / 7.0
        else:
            protein = 0.0
            carb = 0.0
            fat = 0.0
            serat = 0.0
            air_l = 0.0

        # Pastikan tidak dibagi dengan 0 di persentase nantinya, namun UI akan handle
        return {
            'protein': {'avg': protein, 'target': target_protein, 'unit': 'g'},
            'karbo':   {'avg': carb,    'target': target_carb,    'unit': 'g'},
            'lemak':   {'avg': fat,     'target': target_fat,     'unit': 'g'},
            'serat':   {'avg': serat,   'target': target_serat,   'unit': 'g'},
            'air':     {'avg': air_l,   'target': target_air,     'unit': 'L'}
        }
        
    except Exception:
        return {
            'protein': {'avg': 0.0, 'target': 75.0, 'unit': 'g'},
            'karbo':   {'avg': 0.0, 'target': 300.0, 'unit': 'g'},
            'lemak':   {'avg': 0.0, 'target': 70.0, 'unit': 'g'},
            'serat':   {'avg': 0.0, 'target': 30.0, 'unit': 'g'},
            'air':     {'avg': 0.0, 'target': 2.0,  'unit': 'L'}
        }


# ═════════════════════════════════════════════
#  WIDGET UTAMA
# ═════════════════════════════════════════════
class DetailMakroWidget(QWidget):
    """
    Widget reusable yang menampilkan detail nutrisi rata-rata per hari
    selama minggu ini (7 hari terakhir).
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
        root = self.layout()
        if root is None:
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
        container_layout.setSpacing(24)
        container_layout.setAlignment(Qt.AlignTop)

        # ── Judul ──
        title = QLabel('Detail Nutrisi Rata-Rata/Hari')
        title.setFont(self._font_title(20))
        title.setStyleSheet(f'color: {C_TEXT_DARK}; border: none; background: transparent;')
        container_layout.addWidget(title)

        # ── Rows Progress Bar ──
        data = _ambil_detail_makro(self._db_path, self._id_user)
        
        # Urutan sesuai prototipe
        kategori = [
            ('Protein', 'protein'),
            ('Karbohidrat', 'karbo'),
            ('Lemak', 'lemak'),
            ('Serat', 'serat'),
            ('Air', 'air')
        ]
        
        for title_str, key in kategori:
            info = data.get(key, {'avg': 0, 'target': 100, 'unit': 'g'})
            row_widget = self._create_progress_row(
                name=title_str,
                avg=info['avg'],
                target=info['target'],
                unit=info['unit'],
                color=COLOR_MAP[key]['color'],
                bg_color=COLOR_MAP[key]['bg']
            )
            container_layout.addWidget(row_widget)

        root.addWidget(container)

    def _create_progress_row(self, name: str, avg: float, target: float, unit: str, color: str, bg_color: str) -> QWidget:
        row = QWidget()
        row.setStyleSheet('background: transparent; border: none;')
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        
        # ── Teks (Kiri: Nama, Kanan: Value & Persen) ──
        text_row = QWidget()
        text_layout = QHBoxLayout(text_row)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        name_lbl = QLabel(name)
        name_lbl.setFont(self._font_body(12))
        name_lbl.setStyleSheet(f"color: {color};")
        text_layout.addWidget(name_lbl)
        
        text_layout.addStretch()
        
        pct = min(100, int((avg / target) * 100)) if target > 0 else 0
        
        if unit == 'L':
            val_str = f"{avg:.1f}{unit}/{target:.1f}{unit} ({pct}%)"
        else:
            val_str = f"{int(avg)}/{int(target)}{unit} ({pct}%)"
            
        val_lbl = QLabel(val_str)
        val_lbl.setFont(self._font_body(12))
        val_lbl.setStyleSheet(f"color: {C_TEXT_SUB};")
        text_layout.addWidget(val_lbl)
        
        row_layout.addWidget(text_row)
        
        # ── Progress Bar ──
        bar = QProgressBar()
        bar.setFixedHeight(8)
        bar.setTextVisible(False)
        bar.setMinimum(0)
        bar.setMaximum(100)
        bar.setValue(pct)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {bg_color};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        row_layout.addWidget(bar)
        
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
    window.setWindowTitle('Preview — Detail Makro Widget')
    window.resize(900, 600)
    window.setStyleSheet('background: #F2F4F0;')

    lay = QVBoxLayout(window)
    lay.setContentsMargins(32, 32, 32, 32)

    widget = DetailMakroWidget(id_user=1)
    lay.addWidget(widget)
    lay.addStretch()

    window.show()
    sys.exit(app.exec_())
