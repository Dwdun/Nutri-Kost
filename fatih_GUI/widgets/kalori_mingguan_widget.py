"""
Widget Kalori Mingguan — Bar chart asupan kalori 7 hari terakhir.

Menggunakan matplotlib yang di-embed ke dalam QWidget (PyQt5)
agar dapat dipanggil / di-import dari file lain.

Desain mengikuti prototipe Bar Chart Konten.png:
  • Bar hijau (#1A7A34) untuk hari yang mencapai target kalori
  • Bar merah (#C0392B) untuk hari di bawah target
  • 3 kartu ringkasan di bawah chart:
      ‣ Rata-rata kcal/hari (border hijau)
      ‣ Hari target tercapai  (border hijau)
      ‣ Hari dibawah target   (border merah)
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
from PyQt5.QtGui import QFont, QColor, QFontDatabase

import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
import matplotlib.font_manager as fm

# ─────────────────────────────────────────────
#  DESIGN TOKENS  (sinkron dengan template_halaman.py)
# ─────────────────────────────────────────────
C_GREEN       = '#1A7A34'
C_RED         = '#C0392B'
C_TEXT_DARK   = '#1C1C1C'
C_TEXT_SUB    = '#555555'
C_WHITE       = '#FFFFFF'
C_BG          = '#FFFFFF'

# Nama hari dalam bahasa Indonesia (index 0 = Senin)
HARI_ID = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

# ─────────────────────────────────────────────
#  PATH — default database & fonts
# ─────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
def _ambil_kalori_7_hari(db_path: str, id_user: int = 1):
    """
    Query LogHarian → total kalori per hari untuk 7 hari terakhir.
    Mengembalikan list of tuples: [(nama_hari, total_cal), ...] urut dari 7 hari lalu → hari ini.
    Jika belum ada data, kembalikan list dengan 0.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    hari_ini = datetime.now().date()
    hasil = []

    for i in range(6, -1, -1):  # 6 hari lalu … hari ini
        tanggal = hari_ini - timedelta(days=i)
        tgl_str = tanggal.strftime('%Y-%m-%d')

        cursor.execute(
            """
            SELECT COALESCE(SUM(cal), 0)
            FROM LogHarian
            WHERE id_user = ? AND date(meal_time) = ?
            """,
            (id_user, tgl_str),
        )
        total_cal = cursor.fetchone()[0]
        nama_hari = HARI_ID[tanggal.weekday()]
        hasil.append((nama_hari, round(total_cal)))

    conn.close()
    return hasil


def _ambil_target_kalori(db_path: str, id_user: int = 1):
    """
    Ambil target kalori harian dari ProfilUser.calory.
    Default 1500 jika belum di-set.
    """
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
    return 1500  # default target


# ═════════════════════════════════════════════
#  WIDGET UTAMA
# ═════════════════════════════════════════════
class KaloriMingguanWidget(QWidget):
    """
    Widget reusable yang menampilkan bar chart kalori 7 hari terakhir
    beserta ringkasan statistik di bawahnya.

    Cara pakai:
    -----------
        from fatih_GUI.widgets import KaloriMingguanWidget

        widget = KaloriMingguanWidget(id_user=1)
        layout.addWidget(widget)

    Parameter opsional:
        db_path   : path ke file nutrikost.db  (default: auto-detect)
        id_user   : ID user yang datanya ditampilkan  (default: 1)
        target_cal: override target kalori  (default: ambil dari DB)
    """

    def __init__(self, id_user: int = 1, db_path: str = None,
                 target_cal: int = None, parent=None):
        super().__init__(parent)
        self._id_user = id_user
        self._db_path = db_path or os.path.normpath(_DEFAULT_DB)
        self._target_cal = target_cal or _ambil_target_kalori(self._db_path, id_user)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setStyleSheet(f"""
            QWidget {{
                background: {C_WHITE};
            }}
        """)

        self._build_ui()

    # ── Build UI ──────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
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

        # ── Judul ──
        title = QLabel('Asupan Kalori minggu ini')
        title.setFont(self._font_title(18))
        title.setStyleSheet(f'color: {C_TEXT_DARK}; border: none; background: transparent;')
        container_layout.addWidget(title)

        # ── Bar Chart (matplotlib) ──
        self._canvas = self._create_chart()
        container_layout.addWidget(self._canvas)

        # ── Kartu ringkasan ──
        cards_row = self._create_summary_cards()
        container_layout.addWidget(cards_row)

        root.addWidget(container)

    # ── Chart ─────────────────────────────────
    def _create_chart(self) -> FigureCanvas:
        data = _ambil_kalori_7_hari(self._db_path, self._id_user)
        self._data = data  # simpan untuk kartu ringkasan

        hari  = [d[0] for d in data]
        kalori = [d[1] for d in data]
        target = self._target_cal

        # Tentukan warna per bar
        warna = [C_GREEN if k >= target else C_RED for k in kalori]

        # ── Figure ──
        fig = Figure(figsize=(10, 3.5), dpi=100)
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(0.0)

        ax = fig.add_subplot(111)
        ax.set_facecolor('white')
        ax.patch.set_alpha(0.0)

        # Hitung max untuk skala
        max_val = max(kalori) if max(kalori) > 0 else target
        y_max = max(max_val, target) * 1.15

        # ── Bars ──
        bars = ax.bar(
            range(len(hari)), kalori,
            color=warna,
            width=0.6,
            edgecolor='none',
            zorder=3,
        )

        # Rounded top corners via bar patches
        for bar_patch in bars:
            bar_patch.set_linewidth(0)

        # ── Label hari di bawah (Poppins) ──
        ax.set_xticks(range(len(hari)))
        ax.set_xticklabels(hari, fontsize=11,
                           fontproperties=_FP_POPPINS,
                           color=C_TEXT_DARK)

        # ── Label kalori di bawah nama hari (Montserrat Alternates Bold) ──
        for i, (h, k) in enumerate(zip(hari, kalori)):
            clr = C_GREEN if k >= target else C_RED
            ax.text(i, -y_max * 0.12, f'{k}',
                    ha='center', va='top',
                    fontsize=11,
                    fontproperties=_FP_MONTSERRAT_BOLD,
                    color=clr)

        # ── Style axes ──
        ax.set_ylim(0, y_max)
        ax.set_xlim(-0.6, len(hari) - 0.4)

        # Hilangkan semua spines & ticks
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(left=False, labelleft=False, bottom=False)

        # Beri ruang bawah untuk label kalori
        fig.subplots_adjust(left=0.02, right=0.98, top=0.95, bottom=0.22)

        canvas = FigureCanvas(fig)
        canvas.setStyleSheet('background: transparent; border: none;')
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        canvas.setMinimumHeight(250)
        return canvas

    # ── Kartu Ringkasan ───────────────────────
    def _create_summary_cards(self) -> QWidget:
        data = self._data
        target = self._target_cal

        kalori = [d[1] for d in data]
        hari_dengan_data = [k for k in kalori if k > 0]

        # Hitung statistik
        if hari_dengan_data:
            rata_rata = round(sum(hari_dengan_data) / len(hari_dengan_data))
        else:
            rata_rata = 0
        hari_tercapai = sum(1 for k in kalori if k >= target)
        hari_dibawah  = sum(1 for k in kalori if 0 < k < target)

        # Container
        row = QWidget()
        row.setStyleSheet('background: transparent; border: none;')
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 8, 0, 0)
        row_layout.setSpacing(16)

        # Kartu 1: Rata-rata
        card1 = self._make_card(
            value=f'{rata_rata:,}'.replace(',', '.'),
            label='Rata-Rata kcal/hari',
            border_color=C_GREEN,
            value_color=C_GREEN,
        )
        # Kartu 2: Hari tercapai
        card2 = self._make_card(
            value=str(hari_tercapai),
            label='hari target tercapai',
            border_color=C_GREEN,
            value_color=C_GREEN,
        )
        # Kartu 3: Hari di bawah target
        card3 = self._make_card(
            value=str(hari_dibawah),
            label='hari dibawah target',
            border_color=C_RED,
            value_color=C_RED,
        )

        row_layout.addWidget(card1)
        row_layout.addWidget(card2)
        row_layout.addWidget(card3)
        return row

    def _make_card(self, value: str, label: str,
                   border_color: str, value_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {C_WHITE};
                border: 1.5px solid {border_color};
                border-radius: 12px;
            }}
        """)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setFixedHeight(120)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)

        val_lbl = QLabel(value)
        val_lbl.setFont(self._font_title(28))
        val_lbl.setAlignment(Qt.AlignCenter)
        val_lbl.setStyleSheet(
            f'color: {value_color}; border: none; background: transparent;'
        )

        desc_lbl = QLabel(label)
        desc_lbl.setFont(self._font_body(10))
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setStyleSheet(
            f'color: {C_TEXT_SUB}; border: none; background: transparent;'
        )

        layout.addWidget(val_lbl)
        layout.addWidget(desc_lbl)
        return card

    # ── Refresh data ──────────────────────────
    def refresh(self):
        """Reload data dari database dan repaint chart."""
        # Hapus layout lama
        layout = self.layout()
        if layout:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            # Re-build
            self._target_cal = _ambil_target_kalori(self._db_path, self._id_user)
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
    window.setWindowTitle('Preview — Kalori Mingguan Widget')
    window.resize(900, 500)
    window.setStyleSheet('background: #F2F4F0;')

    lay = QVBoxLayout(window)
    lay.setContentsMargins(32, 32, 32, 32)

    widget = KaloriMingguanWidget(id_user=1)
    lay.addWidget(widget)
    lay.addStretch()

    window.show()
    sys.exit(app.exec_())
