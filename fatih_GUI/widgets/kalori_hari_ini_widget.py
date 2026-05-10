"""
Widget Kalori Hari Ini — Donut chart asupan kalori harian.

Menampilkan donut chart yang menunjukkan berapa kalori yang
sudah dikonsumsi hari ini vs target kalori harian user.

Desain mengikuti prototipe pie chart dashboard.png:
  • Border hijau (#1A7A34) dengan rounded corners
  • Judul "Kalori hari ini" (Montserrat Alternates Bold, merah/hijau)
  • Donut chart: hijau tua (dikonsumsi), hijau muda (sisa)
  • Angka kalori di tengah donut: dikonsumsi / target
  • Bawah: dua kolom — Dikonsumsi & Sisa
"""

import os
import sys
import sqlite3
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy, QApplication,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase, QColor

import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.font_manager as fm

# ─────────────────────────────────────────────
#  DESIGN TOKENS
# ─────────────────────────────────────────────
C_GREEN       = '#1A7A34'
C_GREEN_LIGHT = '#C8E6C9'   # sisa kalori (hijau muda/transparan)
C_RED         = '#C0392B'
C_TEXT_DARK   = '#1C1C1C'
C_TEXT_SUB    = '#555555'
C_WHITE       = '#FFFFFF'

# ─────────────────────────────────────────────
#  PATH
# ─────────────────────────────────────────────
_BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_DB = os.path.join(_BASE_DIR, '..', '..', 'bima_scrapper', 'nutrikost.db')
_FONTS_DIR  = os.path.join(_BASE_DIR, '..', '..', 'assets', 'fonts')

# ─────────────────────────────────────────────
#  REGISTER FONTS KE MATPLOTLIB
# ─────────────────────────────────────────────
_fonts_registered = False

def _register_matplotlib_fonts():
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

_FP_MONTSERRAT_BOLD = fm.FontProperties(
    family='Montserrat Alternates', weight='bold'
)
_FP_POPPINS = fm.FontProperties(
    family='Poppins', weight='normal'
)


# ─────────────────────────────────────────────
#  DATA HELPER
# ─────────────────────────────────────────────
def _ambil_kalori_hari_ini(db_path: str, id_user: int = 1) -> int:
    """Total kalori yang sudah dikonsumsi hari ini."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        hari_ini = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            """
            SELECT COALESCE(SUM(cal), 0)
            FROM LogHarian
            WHERE id_user = ? AND date(meal_time) = ?
            """,
            (id_user, hari_ini),
        )
        total = cursor.fetchone()[0]
        conn.close()
        return round(total)
    except Exception:
        return 0


def _ambil_target_kalori(db_path: str, id_user: int = 1) -> int:
    """Ambil target kalori harian dari ProfilUser.calory."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT calory FROM ProfilUser WHERE id_user = ?", (id_user,)
        )
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            return int(row[0])
    except Exception:
        pass
    return 2100  # default target


# ═════════════════════════════════════════════
#  WIDGET UTAMA — KaloriHariIniWidget
# ═════════════════════════════════════════════
class KaloriHariIniWidget(QWidget):
    """
    Widget donut chart kalori hari ini untuk dashboard.

    Menampilkan:
      • Donut chart: dikonsumsi vs sisa
      • Angka di tengah: dikonsumsi / target
      • Keterangan bawah: Dikonsumsi & Sisa

    Cara pakai:
    -----------
        from fatih_GUI.widgets import KaloriHariIniWidget

        widget = KaloriHariIniWidget(id_user=1)
        layout.addWidget(widget)
    """

    def __init__(self, id_user: int = 1, db_path: str = None,
                 target_cal: int = None, parent=None):
        super().__init__(parent)
        self._id_user = id_user
        self._db_path = db_path or os.path.normpath(_DEFAULT_DB)
        self._target_cal = target_cal or _ambil_target_kalori(self._db_path, id_user)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setStyleSheet('background: transparent;')

        self._build_ui()

    def _build_ui(self):
        root = self.layout()
        if root is None:
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

        # ── Container dengan border hijau ──
        container = QFrame()
        container.setObjectName('kaloriHariIniCard')
        container.setStyleSheet(f"""
            QFrame#kaloriHariIniCard {{
                background: {C_WHITE};
                border: 1.5px solid {C_GREEN};
                border-radius: 16px;
            }}
        """)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(16, 16, 16, 16)
        container_layout.setSpacing(8)
        container_layout.setAlignment(Qt.AlignTop)

        # ── Judul "Kalori hari ini" ──
        title = QLabel('Kalori hari ini')
        title.setFont(self._font_title(14))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f'color: {C_GREEN}; background: transparent; border: none;'
        )
        container_layout.addWidget(title)

        # ── Donut Chart ──
        dikonsumsi = _ambil_kalori_hari_ini(self._db_path, self._id_user)
        target = self._target_cal
        self._dikonsumsi = dikonsumsi
        self._sisa = max(target - dikonsumsi, 0)

        canvas = self._create_donut_chart(dikonsumsi, target)
        container_layout.addWidget(canvas)

        # ── Keterangan bawah: Dikonsumsi | Sisa ──
        summary_row = self._create_summary(dikonsumsi, target)
        container_layout.addWidget(summary_row)

        root.addWidget(container)

    def _create_donut_chart(self, dikonsumsi: int, target: int) -> FigureCanvas:
        sisa = max(target - dikonsumsi, 0)

        # Jika melebihi target, donut penuh hijau tua
        if dikonsumsi >= target:
            sizes = [1]
            colors = [C_GREEN]
        elif dikonsumsi == 0:
            sizes = [1]
            colors = [C_GREEN_LIGHT]
        else:
            sizes = [dikonsumsi, sisa]
            colors = [C_GREEN, C_GREEN_LIGHT]

        fig = Figure(figsize=(3.2, 3.2), dpi=100)
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(0.0)

        ax = fig.add_subplot(111)
        ax.set_facecolor('white')
        ax.patch.set_alpha(0.0)

        # Donut chart
        wedges, _ = ax.pie(
            sizes,
            colors=colors,
            startangle=90,
            counterclock=False,
            wedgeprops=dict(width=0.32, edgecolor='white', linewidth=2),
        )

        # Teks tengah — dikonsumsi
        ax.text(
            0, 0.06,
            f'{dikonsumsi}',
            ha='center', va='center',
            fontsize=28,
            fontproperties=_FP_MONTSERRAT_BOLD,
            color=C_GREEN,
        )
        # Teks tengah — /target
        ax.text(
            0, -0.18,
            f'/{target}',
            ha='center', va='center',
            fontsize=13,
            fontproperties=_FP_POPPINS,
            color=C_TEXT_SUB,
        )

        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.set_aspect('equal')

        fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)

        canvas = FigureCanvas(fig)
        canvas.setStyleSheet('background: transparent; border: none;')
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        canvas.setMinimumHeight(200)
        canvas.setMinimumWidth(10)
        return canvas

    def _create_summary(self, dikonsumsi: int, target: int) -> QWidget:
        sisa = max(target - dikonsumsi, 0)

        row = QWidget()
        row.setStyleSheet('background: transparent; border: none;')
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(8, 0, 8, 4)
        row_layout.setSpacing(16)

        # ── Kolom Dikonsumsi ──
        col_left = QWidget()
        col_left.setStyleSheet('background: transparent; border: none;')
        left_layout = QVBoxLayout(col_left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.setAlignment(Qt.AlignCenter)

        val_consumed = QLabel(str(dikonsumsi))
        val_consumed.setFont(self._font_body(18))
        val_consumed.setAlignment(Qt.AlignCenter)
        val_consumed.setStyleSheet(
            f'color: {C_TEXT_DARK}; background: transparent; border: none;'
        )

        lbl_consumed = QLabel('Dikonsumsi')
        lbl_consumed.setFont(self._font_title(10))
        lbl_consumed.setAlignment(Qt.AlignCenter)
        lbl_consumed.setStyleSheet(
            f'color: {C_TEXT_SUB}; background: transparent; border: none;'
        )

        left_layout.addWidget(val_consumed)
        left_layout.addWidget(lbl_consumed)

        # ── Kolom Sisa ──
        col_right = QWidget()
        col_right.setStyleSheet('background: transparent; border: none;')
        right_layout = QVBoxLayout(col_right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignCenter)

        sisa_color = C_RED

        val_sisa = QLabel(str(sisa))
        val_sisa.setFont(self._font_body(18))
        val_sisa.setAlignment(Qt.AlignCenter)
        val_sisa.setStyleSheet(
            f'color: {sisa_color}; background: transparent; border: none;'
        )

        lbl_sisa = QLabel('Sisa')
        lbl_sisa.setFont(self._font_title(10))
        lbl_sisa.setAlignment(Qt.AlignCenter)
        lbl_sisa.setStyleSheet(
            f'color: {C_TEXT_SUB}; background: transparent; border: none;'
        )

        right_layout.addWidget(val_sisa)
        right_layout.addWidget(lbl_sisa)

        row_layout.addWidget(col_left)
        row_layout.addWidget(col_right)
        return row

    # ── Refresh ──
    def refresh(self):
        """Reload data dari database dan rebuild widget."""
        layout = self.layout()
        if layout:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            self._target_cal = _ambil_target_kalori(self._db_path, self._id_user)
        self._build_ui()

    # ── Font helpers ──
    @staticmethod
    def _font_title(size: int = 14) -> QFont:
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
    window.setWindowTitle('Preview — Kalori Hari Ini Widget')
    window.resize(380, 450)
    window.setStyleSheet('background: #F2F4F0;')

    lay = QVBoxLayout(window)
    lay.setContentsMargins(32, 32, 32, 32)

    widget = KaloriHariIniWidget(id_user=1)
    lay.addWidget(widget)
    lay.addStretch()

    window.show()
    sys.exit(app.exec_())
