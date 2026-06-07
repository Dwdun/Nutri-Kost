"""
Widget Nav Card — 3 kartu navigasi cepat di dashboard.

Menampilkan 3 kartu hijau yang bisa diklik:
  • Log Makanan      → navigasi ke halaman log
  • Lihat Grafik     → navigasi ke halaman visualisasi
  • Riwayat          → navigasi ke halaman riwayat

Desain mengikuti prototipe NavCard Content.png:
  • Background hijau (#1A7A34) dengan rounded corners
  • Icon putih di atas, judul (Montserrat Alternates Bold),
    deskripsi (Poppins) di bawahnya
  • Hover effect untuk interaktivitas
"""

import os
import sys
import sqlite3
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy, QApplication, QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPixmap, QFontDatabase, QColor, QCursor

# ─────────────────────────────────────────────
#  DESIGN TOKENS
# ─────────────────────────────────────────────
C_GREEN       = '#1A7A34'
C_GREEN_HOVER = '#1E8C3D'
C_GREEN_PRESS = '#156B2C'
C_WHITE       = '#FFFFFF'
C_TEXT_SUB    = 'rgba(255, 255, 255, 0.75)'

# ─────────────────────────────────────────────
#  PATH
# ─────────────────────────────────────────────
_BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
_ICONS_DIR  = os.path.join(_BASE_DIR, '..', '..', 'assets', 'icons')
_FONTS_DIR  = os.path.join(_BASE_DIR, '..', '..', 'assets', 'fonts')
_DEFAULT_DB = os.path.join(_BASE_DIR, '..', '..', 'bima_scrapper', 'nutrikost.db')

# ─────────────────────────────────────────────
#  DATA HELPER
# ─────────────────────────────────────────────
def _hitung_entri_hari_ini(db_path: str, id_user: int = 1) -> int:
    """Hitung jumlah entri log makanan hari ini."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        hari_ini = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM LogHarian
            WHERE id_user = ? AND date(meal_time) = ?
            """,
            (id_user, hari_ini),
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


# ─────────────────────────────────────────────
#  SINGLE NAV CARD
# ─────────────────────────────────────────────
class _NavCard(QPushButton if False else QFrame):
    """
    Satu kartu navigasi hijau yang bisa diklik.
    """
    clicked = pyqtSignal()

    def __init__(self, icon_path: str, title: str, description: str, parent=None):
        super().__init__(parent)
        self._title_text = title
        self._desc_text = description

        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(140)

        self._apply_style(C_GREEN)
        self._build_ui(icon_path)

        # Subtle shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

    def _apply_style(self, bg_color: str):
        self.setStyleSheet(f"""
            _NavCard {{
                background-color: {bg_color};
                border-radius: 16px;
                border: none;
            }}
        """)

    def _build_ui(self, icon_path: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        # ── Icon ──
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet('background: transparent; border: none;')

        if os.path.exists(icon_path):
            pix = QPixmap(icon_path)
            if not pix.isNull():
                scaled = pix.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_lbl.setPixmap(scaled)
        layout.addWidget(icon_lbl)

        layout.addSpacing(4)

        # ── Title (Montserrat Alternates Bold) ──
        title_lbl = QLabel(self._title_text)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setFont(self._font_title(15))
        title_lbl.setStyleSheet(f'color: {C_WHITE}; background: transparent; border: none;')
        layout.addWidget(title_lbl)

        # ── Description (Poppins) ──
        desc_lbl = QLabel(self._desc_text)
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setFont(self._font_body(10))
        desc_lbl.setStyleSheet(f'color: {C_TEXT_SUB}; background: transparent; border: none;')
        layout.addWidget(desc_lbl)

    # ── Mouse events untuk klik & hover ──
    def enterEvent(self, event):
        self._apply_style(C_GREEN_HOVER)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(C_GREEN)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._apply_style(C_GREEN_PRESS)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._apply_style(C_GREEN_HOVER)
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    # ── Font helpers ──
    @staticmethod
    def _font_title(size: int = 15) -> QFont:
        f = QFont('Montserrat Alternates', size, QFont.Bold)
        f.setStyleHint(QFont.SansSerif)
        return f

    @staticmethod
    def _font_body(size: int = 10) -> QFont:
        f = QFont('Poppins', size)
        f.setStyleHint(QFont.SansSerif)
        return f


# ═════════════════════════════════════════════
#  WIDGET UTAMA — NavCardWidget
# ═════════════════════════════════════════════
class NavCardWidget(QWidget):
    """
    Widget berisi 3 kartu navigasi cepat untuk dashboard.

    Signal:
        card_clicked(str)  — dipancarkan saat kartu diklik,
                             berisi page_key target navigasi:
                             'log', 'kalori_mingguan', atau 'riwayat'

    Cara pakai:
    -----------
        from fatih_GUI.widgets import NavCardWidget

        nav = NavCardWidget(id_user=1)
        nav.card_clicked.connect(lambda key: main_window.navigate(key))
        layout.addWidget(nav)
    """

    card_clicked = pyqtSignal(str)

    # Konfigurasi 3 kartu: (icon_file, title, description, page_key)
    CARDS = [
        (
            'material-symbols_list-alt-rounded.png',
            'Log Makanan',
            '{n} entri hari ini',
            'log',
        ),
        (
            'material-symbols_bar-chart-rounded.png',
            'Lihat Grafik',
            'Tren Mingguan',
            'kalori_mingguan',
        ),
        (
            'iconamoon_history-bold.png',
            'Riwayat',
            'hingga 30 hari sebelum',
            'riwayat',
        ),
    ]

    def __init__(self, id_user: int = 1, db_path: str = None, parent=None):
        super().__init__(parent)
        self._id_user = id_user
        self._db_path = db_path or os.path.normpath(_DEFAULT_DB)

        self.setStyleSheet('background: transparent;')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Hitung entri hari ini untuk kartu pertama
        entri_hari_ini = _hitung_entri_hari_ini(self._db_path, self._id_user)

        for icon_file, title, desc_template, page_key in self.CARDS:
            icon_path = os.path.join(_ICONS_DIR, icon_file)

            # Format deskripsi dinamis
            if '{n}' in desc_template:
                description = desc_template.format(n=entri_hari_ini)
            else:
                description = desc_template

            card = _NavCard(icon_path, title, description)
            card.clicked.connect(lambda key=page_key: self._on_card_clicked(key))
            layout.addWidget(card)

    def _on_card_clicked(self, page_key: str):
        self.card_clicked.emit(page_key)

    def refresh(self, id_user: int = None):
        """Reload data dan rebuild kartu."""
        if id_user is not None:
            self._id_user = id_user
        layout = self.layout()
        if layout:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        # Hapus layout lama dan buat ulang
        entri_hari_ini = _hitung_entri_hari_ini(self._db_path, self._id_user)

        for icon_file, title, desc_template, page_key in self.CARDS:
            icon_path = os.path.join(_ICONS_DIR, icon_file)

            if '{n}' in desc_template:
                description = desc_template.format(n=entri_hari_ini)
            else:
                description = desc_template

            card = _NavCard(icon_path, title, description)
            card.clicked.connect(lambda key=page_key: self._on_card_clicked(key))
            layout.addWidget(card)


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
    window.setWindowTitle('Preview — Nav Card Widget')
    window.resize(900, 220)
    window.setStyleSheet('background: #F2F4F0;')

    lay = QVBoxLayout(window)
    lay.setContentsMargins(32, 32, 32, 32)

    widget = NavCardWidget(id_user=1)
    widget.card_clicked.connect(lambda key: print(f'Navigasi ke: {key}'))
    lay.addWidget(widget)
    lay.addStretch()

    window.show()
    sys.exit(app.exec_())
