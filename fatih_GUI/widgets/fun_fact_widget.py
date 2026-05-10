"""
Widget Fun Fact — Kartu fakta menarik tentang makanan & nutrisi.

Menampilkan satu fakta acak dari file FoodFact.json pada kartu
dengan background hijau terang.

Desain mengikuti prototipe Fun fact card.png:
  • Background hijau terang (#3BAF4E)
  • Judul "Fun Fact" (Montserrat Alternates Bold, warna hijau gelap)
  • Isi fakta (Poppins, putih, justified)
  • Rounded corners 16px
"""

import os
import sys
import json
import random

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QFrame, QSizePolicy, QApplication,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase, QColor

# ─────────────────────────────────────────────
#  DESIGN TOKENS
# ─────────────────────────────────────────────
C_CARD_BG     = '#3BAF4E'   # background hijau terang
C_TITLE       = '#1A5C28'   # judul hijau gelap
C_WHITE       = '#FFFFFF'

# ─────────────────────────────────────────────
#  PATH
# ─────────────────────────────────────────────
_BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
_FONTS_DIR     = os.path.join(_BASE_DIR, '..', '..', 'assets', 'fonts')
_FOOD_FACT_JSON = os.path.join(_BASE_DIR, '..', '..', 'bima_scrapper', 'FoodFact.json')


# ─────────────────────────────────────────────
#  DATA HELPER
# ─────────────────────────────────────────────
def _load_random_fact(json_path: str) -> dict:
    """
    Muat satu fakta acak dari FoodFact.json.
    Mengembalikan dict {'judul': ..., 'isi': ...}.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            facts = json.load(f)
        if facts:
            return random.choice(facts)
    except Exception:
        pass
    # Fallback jika file tidak ditemukan / kosong
    return {
        'judul': 'Fun Fact',
        'isi': 'Makanan sehat menyediakan energi yang dibutuhkan tubuh untuk beraktivitas sepanjang hari.',
    }


# ═════════════════════════════════════════════
#  WIDGET UTAMA — FunFactWidget
# ═════════════════════════════════════════════
class FunFactWidget(QWidget):
    """
    Widget kartu Fun Fact untuk dashboard.

    Menampilkan fakta makanan/nutrisi acak dari FoodFact.json
    dengan desain kartu hijau terang.

    Cara pakai:
    -----------
        from fatih_GUI.widgets import FunFactWidget

        widget = FunFactWidget()
        layout.addWidget(widget)

    Method:
        refresh()  — tampilkan fakta baru secara acak.
    """

    def __init__(self, json_path: str = None, parent=None):
        super().__init__(parent)
        self._json_path = json_path or os.path.normpath(_FOOD_FACT_JSON)

        self.setStyleSheet('background: transparent;')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._build_ui()

    def _build_ui(self):
        root = self.layout()
        if root is None:
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

        # ── Ambil fakta acak ──
        fact = _load_random_fact(self._json_path)

        # ── Card container ──
        card = QFrame()
        card.setObjectName('funFactCard')
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        card.setStyleSheet(f"""
            QFrame#funFactCard {{
                background-color: {C_CARD_BG};
                border-radius: 16px;
                border: none;
            }}
        """)

        # Subtle shadow
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(12)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 22)
        card_layout.setSpacing(10)

        # ── Title (judul dari JSON) ──
        title_lbl = QLabel(fact.get('judul', 'Fun Fact'))
        title_lbl.setFont(self._font_title(16))
        title_lbl.setStyleSheet(
            f'color: {C_TITLE}; background: transparent; border: none;'
        )
        title_lbl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        card_layout.addWidget(title_lbl)

        # ── Isi fakta (Poppins, justified) ──
        body_lbl = QLabel(fact.get('isi', ''))
        body_lbl.setFont(self._font_body(10))
        body_lbl.setWordWrap(True)
        body_lbl.setAlignment(Qt.AlignJustify | Qt.AlignTop)
        body_lbl.setStyleSheet(
            f'color: {C_WHITE}; background: transparent; border: none;'
            'line-height: 1.5;'
        )
        body_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        card_layout.addWidget(body_lbl, 1)

        root.addWidget(card)

    # ── Refresh — tampilkan fakta baru ──
    def refresh(self):
        """Tampilkan fakta baru secara acak."""
        layout = self.layout()
        if layout:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        self._build_ui()

    # ── Font helpers ──
    @staticmethod
    def _font_title(size: int = 16) -> QFont:
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
    window.setWindowTitle('Preview — Fun Fact Widget')
    window.resize(320, 400)
    window.setStyleSheet('background: #F2F4F0;')

    lay = QVBoxLayout(window)
    lay.setContentsMargins(32, 32, 32, 32)

    widget = FunFactWidget()
    lay.addWidget(widget)
    lay.addStretch()

    window.show()
    sys.exit(app.exec_())
