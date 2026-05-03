"""
Widget Komposisi Gizi — Pie chart makronutrien 7 hari terakhir.

Menggunakan matplotlib yang di-embed ke dalam QWidget (PyQt5)
agar dapat dipanggil / di-import dari file lain.

Desain mengikuti prototipe Pie Chart Komposisi gizi.png:
  • Pie chart dengan 3 slice (Protein, Karbohidrat, Lemak)
  • Label persentase di dalam slice (font bold, warna putih)
  • Legend PyQt5 di sisi kanan chart
  • Container border rounded hijau (#1A7A34)
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy, QApplication, QSpacerItem,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase

import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.font_manager as fm

# ─────────────────────────────────────────────
#  DESIGN TOKENS  (sinkron dengan template_halaman.py)
# ─────────────────────────────────────────────
C_GREEN     = '#1A7A34'
C_BLUE      = '#2196F3'
C_AMBER     = '#FFC107'
C_TEXT_DARK  = '#1C1C1C'
C_TEXT_SUB   = '#555555'
C_WHITE      = '#FFFFFF'

# Urutan: Protein, Karbohidrat, Lemak
MAKRO_COLORS = [C_GREEN, C_BLUE, C_AMBER]
MAKRO_LABELS = ['Protein', 'Karbohidrat', 'Lemak']

# ─────────────────────────────────────────────
#  PATH — default database & fonts
# ─────────────────────────────────────────────
_BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_DB = os.path.join(_BASE_DIR, '..', '..', 'bima_scrapper', 'nutrikost.db')
_FONTS_DIR  = os.path.join(_BASE_DIR, '..', '..', 'assets', 'fonts')

# ─────────────────────────────────────────────
#  REGISTER CUSTOM FONTS KE MATPLOTLIB
# ─────────────────────────────────────────────
_fonts_registered = False

def _register_matplotlib_fonts():
    """Daftarkan font Montserrat Alternates & Poppins ke matplotlib."""
    global _fonts_registered
    if _fonts_registered:
        return
    if os.path.isdir(_FONTS_DIR):
        for fname in os.listdir(_FONTS_DIR):
            if fname.lower().endswith(('.ttf', '.otf')):
                fpath = os.path.join(_FONTS_DIR, fname)
                fm.fontManager.addfont(fpath)
    _fonts_registered = True

_register_matplotlib_fonts()

# FontProperties untuk dipakai di chart
_FP_MONTSERRAT_BOLD = fm.FontProperties(
    family='Montserrat Alternates', weight='bold'
)
_FP_POPPINS = fm.FontProperties(
    family='Poppins', weight='normal'
)
_FP_POPPINS_BOLD = fm.FontProperties(
    family='Poppins', weight='bold'
)


# ─────────────────────────────────────────────
#  DATA HELPER
# ─────────────────────────────────────────────
def _ambil_makronutrien(db_path: str, id_user: int = 1) -> dict:
    """
    Query LogHarian → total protein, carb, fat untuk 7 hari terakhir.
    Mengembalikan dict: {'protein': float, 'karbo': float, 'lemak': float}
    Jika semua 0 (belum ada data), return nilai dummy supaya chart tetap tampil.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                COALESCE(SUM(protein), 0) as total_protein,
                COALESCE(SUM(carb), 0)    as total_carb,
                COALESCE(SUM(fat), 0)     as total_fat
            FROM LogHarian
            WHERE id_user = ?
              AND date(meal_time) BETWEEN date('now', '-6 days') AND date('now')
            """,
            (id_user,),
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            protein, karbo, lemak = float(row[0]), float(row[1]), float(row[2])
        else:
            protein, karbo, lemak = 0.0, 0.0, 0.0

    except Exception:
        protein, karbo, lemak = 0.0, 0.0, 0.0

    # Jika semua 0, return 0
    return {'protein': protein, 'karbo': karbo, 'lemak': lemak}


# ═════════════════════════════════════════════
#  WIDGET UTAMA
# ═════════════════════════════════════════════
class KomposisiGiziWidget(QWidget):
    """
    Widget reusable yang menampilkan pie chart komposisi makronutrien
    (Protein, Karbohidrat, Lemak) dari data 7 hari terakhir.

    Cara pakai:
    -----------
        from fatih_GUI.widgets.komposisi_gizi_widget import KomposisiGiziWidget

        # Di halaman visualisasi
        widget = KomposisiGiziWidget(id_user=1)
        layout.addWidget(widget)

        # Di dashboard (ukuran lebih kecil — cukup atur height parent)
        widget_mini = KomposisiGiziWidget(id_user=1)
        widget_mini.setMaximumHeight(300)
        layout.addWidget(widget_mini)

    Parameter opsional:
        db_path : path ke file nutrikost.db  (default: auto-detect)
        id_user : ID user yang datanya ditampilkan  (default: 1)
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

    # ── Build UI ──────────────────────────────
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
        container_layout.setSpacing(16)
        container_layout.setAlignment(Qt.AlignTop)

        # ── Judul ──
        title = QLabel('Makronutrien Minggu Ini')
        title.setFont(self._font_title(18))
        title.setStyleSheet(f'color: {C_TEXT_DARK}; border: none; background: transparent;')
        container_layout.addWidget(title)

        # ── Konten: Pie Chart (kiri) + Legend (kanan) ──
        content_row = QWidget()
        content_row.setStyleSheet('background: transparent; border: none;')
        content_layout = QHBoxLayout(content_row)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        # Ambil data makronutrien
        self._data = _ambil_makronutrien(self._db_path, self._id_user)

        # Pie Chart (~65%)
        self._canvas = self._create_pie_chart()
        content_layout.addWidget(self._canvas, 65)

        # Legend (~35%)
        legend_widget = self._create_legend()
        content_layout.addWidget(legend_widget, 35)

        container_layout.addWidget(content_row)
        root.addWidget(container)

    # ── Pie Chart (matplotlib) ────────────────
    def _create_pie_chart(self) -> FigureCanvas:
        data = self._data
        values = [data['protein'], data['karbo'], data['lemak']]

        # ── Figure ──
        fig = Figure(figsize=(4, 3.5), dpi=100)
        fig.patch.set_alpha(0.0)

        ax = fig.add_subplot(111)
        ax.set_facecolor('white')
        ax.patch.set_alpha(0.0)

        if sum(values) == 0:
            # ── Pie Kosong ──
            wedges, _, autotexts = ax.pie(
                [100],
                colors=['#E0E0E0'],
                autopct='',
                startangle=90,
                counterclock=False,
                labels=None,
                wedgeprops={'linewidth': 0},
            )
            ax.text(0, 0, 'Belum ada\\ndata', ha='center', va='center', fontproperties=_FP_POPPINS_BOLD, fontsize=14, color=C_TEXT_SUB)
        else:
            # ── Pie ──
            wedges, _, autotexts = ax.pie(
                values,
                colors=MAKRO_COLORS,
                autopct='%1.0f%%',
                startangle=90,
                counterclock=False,
                labels=None,
                pctdistance=0.55,
                wedgeprops={'linewidth': 0},
            )

            # Style label persentase di dalam slice
            for autotext in autotexts:
                autotext.set_fontproperties(_FP_POPPINS_BOLD)
                autotext.set_fontsize(13)
                autotext.set_color(C_WHITE)
                autotext.set_fontweight('bold')

        ax.set_aspect('equal')
        fig.subplots_adjust(left=0.02, right=0.98, top=0.95, bottom=0.05)

        canvas = FigureCanvas(fig)
        canvas.setStyleSheet('background: transparent; border: none;')
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        canvas.setMinimumHeight(280)
        return canvas

    # ── Legend (PyQt5) ────────────────────────
    def _create_legend(self) -> QWidget:
        data = self._data
        values = [data['protein'], data['karbo'], data['lemak']]
        total = sum(values)

        # Hitung persentase
        if total > 0:
            persentase = [v / total * 100 for v in values]
        else:
            persentase = [0.0, 0.0, 0.0]

        legend = QWidget()
        legend.setStyleSheet('background: transparent; border: none;')
        legend_layout = QVBoxLayout(legend)
        legend_layout.setContentsMargins(8, 0, 8, 0)
        legend_layout.setSpacing(16)
        legend_layout.setAlignment(Qt.AlignVCenter)

        for i, (label, color, pct) in enumerate(
            zip(MAKRO_LABELS, MAKRO_COLORS, persentase)
        ):
            item = self._create_legend_item(label, color, pct)
            legend_layout.addWidget(item)

        return legend

    def _create_legend_item(self, label: str, color: str, pct: float) -> QWidget:
        """Buat satu baris legend: ● Nama  persentase"""
        item = QWidget()
        item.setStyleSheet('background: transparent; border: none;')
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(10)
        item_layout.setAlignment(Qt.AlignVCenter)

        # ── Circle bullet ──
        bullet = QLabel()
        bullet.setFixedSize(14, 14)
        bullet.setStyleSheet(f"""
            background: {color};
            border: none;
            border-radius: 7px;
        """)
        item_layout.addWidget(bullet)

        # ── Label nama makronutrien ──
        name_lbl = QLabel(label)
        name_lbl.setFont(self._font_body(11))
        name_lbl.setStyleSheet(
            f'color: {C_TEXT_DARK}; border: none; background: transparent;'
        )
        item_layout.addWidget(name_lbl)

        item_layout.addStretch()

        # ── Persentase ──
        pct_lbl = QLabel(f'{pct:.0f}%')
        pct_lbl.setFont(self._font_body_bold(13))
        pct_lbl.setStyleSheet(
            f'color: {color}; border: none; background: transparent;'
        )
        item_layout.addWidget(pct_lbl)

        return item

    # ── Refresh data ──────────────────────────
    def refresh(self):
        """Reload data dari database dan repaint chart."""
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
    window.setWindowTitle('Preview — Komposisi Gizi Widget')
    window.resize(900, 500)
    window.setStyleSheet('background: #F2F4F0;')

    lay = QVBoxLayout(window)
    lay.setContentsMargins(32, 32, 32, 32)

    widget = KomposisiGiziWidget(id_user=1)
    lay.addWidget(widget)
    lay.addStretch()

    window.show()
    sys.exit(app.exec_())
