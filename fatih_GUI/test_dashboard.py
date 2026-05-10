"""
test.py — Standalone runner untuk modul fatih_GUI (Dashboard & Visualisasi).

Menampilkan HalamanDashboard di dalam window dengan sidebar sederhana
agar bisa dicoba secara mandiri tanpa main_window terintegrasi.

Cara pakai:
    python fatih_GUI/test.py
"""

import sys
import os

# Pastikan root proyek ada di sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap

from fatih_GUI.halaman_dashboard import HalamanDashboard
from fatih_GUI.halaman_visualisasi import HalamanVisualisasi

# ─────────────────────────────────────────────
#  DESIGN TOKENS
# ─────────────────────────────────────────────
SIDEBAR_BG   = '#1A7A34'
SIDEBAR_HOVER = '#3C8E52'
CONTENT_BG   = '#F2F4F0'
FONTS_DIR    = os.path.join(ROOT_DIR, 'assets', 'fonts')
ICONS_DIR    = os.path.join(ROOT_DIR, 'assets', 'icons')


# ═════════════════════════════════════════════
#  MINI SIDEBAR BUTTON
# ═════════════════════════════════════════════
class SidebarButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)
        self.setFont(QFont('Poppins', 10))
        self._set_style(active=False)

    def _set_style(self, active: bool):
        bg = '#5EA271' if active else 'transparent'
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
                text-align: left;
                font-family: 'Poppins';
            }}
            QPushButton:hover {{
                background: {SIDEBAR_HOVER};
            }}
        """)

    def set_active(self, active: bool):
        self._set_style(active)


# ═════════════════════════════════════════════
#  TEST WINDOW
# ═════════════════════════════════════════════
class TestWindow(QMainWindow):
    """
    Window testing sederhana dengan sidebar mini dan halaman dashboard + visualisasi.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Testing — fatih_GUI Dashboard')
        self.setMinimumSize(1100, 700)
        self.resize(1200, 780)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Sidebar ──
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f'background: {SIDEBAR_BG}; border: none;')

        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(12, 20, 12, 20)
        sb_layout.setSpacing(8)

        # Logo
        logo_lbl = QLabel('🍊 NutriKost')
        logo_lbl.setFont(QFont('Montserrat Alternates', 14, QFont.Bold))
        logo_lbl.setStyleSheet('color: white; padding: 8px 0;')
        sb_layout.addWidget(logo_lbl)
        sb_layout.addSpacing(16)

        # Section label
        section = QLabel('Testing Pages')
        section.setFont(QFont('Poppins', 8))
        section.setStyleSheet('color: rgba(255,255,255,0.5); padding-left: 4px;')
        sb_layout.addWidget(section)

        # Navigation buttons
        self._buttons = {}
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f'background: {CONTENT_BG};')

        pages = [
            ('dashboard', '🏠  Dashboard'),
            ('visualisasi', '📊  Visualisasi'),
        ]

        for key, label in pages:
            btn = SidebarButton(label)
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))
            self._buttons[key] = btn
            sb_layout.addWidget(btn)

        sb_layout.addStretch()

        # Info footer
        info = QLabel('fatih_GUI — Test Mode')
        info.setFont(QFont('Poppins', 8))
        info.setStyleSheet('color: rgba(255,255,255,0.4);')
        info.setAlignment(Qt.AlignCenter)
        sb_layout.addWidget(info)

        root_layout.addWidget(sidebar)

        # ── Content Area ──
        content = QWidget()
        content.setStyleSheet(f'background: {CONTENT_BG};')
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Header bar
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet('background: white; border: none;')
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)

        self._page_title = QLabel('NutriKos — Home Dashboard')
        self._page_title.setFont(QFont('Poppins', 12, QFont.Bold))
        self._page_title.setStyleSheet('color: #1C1C1C;')
        header_layout.addWidget(self._page_title)
        header_layout.addStretch()

        test_badge = QLabel('🧪 TEST MODE')
        test_badge.setFont(QFont('Poppins', 9, QFont.Bold))
        test_badge.setStyleSheet("""
            color: #1A7A34;
            background: rgba(26, 122, 52, 0.1);
            border: 1px solid #1A7A34;
            border-radius: 8px;
            padding: 4px 12px;
        """)
        header_layout.addWidget(test_badge)

        content_layout.addWidget(header)

        content_layout.addWidget(self._stack, 1)
        root_layout.addWidget(content, 1)

        # ── Setup Pages ──
        self._setup_pages()
        self._navigate('dashboard')

    def _setup_pages(self):
        # Dashboard
        self.dashboard_page = HalamanDashboard(id_user=1)
        self.dashboard_page.navigate_to.connect(self._on_dashboard_navigate)
        self.dashboard_page.tambah_makanan_clicked.connect(
            lambda: print('[TEST] Tombol Tambah Makanan diklik! → Navigasi ke Log Page')
        )
        self._stack.addWidget(self.dashboard_page)

        # Visualisasi
        self.visualisasi_page = HalamanVisualisasi()
        self._stack.addWidget(self.visualisasi_page)

    def _navigate(self, key: str):
        pages = {
            'dashboard': (0, 'Home Dashboard'),
            'visualisasi': (1, 'Grafik & Visualisasi'),
        }

        if key not in pages:
            print(f'[TEST] Navigasi ke halaman: {key} (belum tersedia di test mode)')
            return

        idx, title = pages[key]
        self._stack.setCurrentIndex(idx)
        self._page_title.setText(f'NutriKos — {title}')

        for k, btn in self._buttons.items():
            btn.set_active(k == key)

    def _on_dashboard_navigate(self, page_key: str):
        """Handle sinyal navigate_to dari dashboard."""
        mapping = {
            'log': 'dashboard',                # tetap di dashboard (log belum ada)
            'kalori_mingguan': 'visualisasi',
            'riwayat': 'dashboard',            # riwayat belum ada
        }

        target = mapping.get(page_key, page_key)

        if target == 'visualisasi':
            self._navigate('visualisasi')
            # Set tab di visualisasi jika relevan
            tab_map = {'kalori_mingguan': 0, 'komposisi_gizi': 1, 'top_10_makanan': 2}
            if page_key in tab_map:
                self.visualisasi_page.set_tab(tab_map[page_key])
        else:
            print(f'[TEST] Dashboard request navigasi ke: {page_key}')


# ═════════════════════════════════════════════
#  MAIN
# ═════════════════════════════════════════════
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Load custom fonts
    if os.path.isdir(FONTS_DIR):
        for fname in os.listdir(FONTS_DIR):
            if fname.lower().endswith(('.ttf', '.otf')):
                QFontDatabase.addApplicationFont(os.path.join(FONTS_DIR, fname))

    app.setStyle('Fusion')

    window = TestWindow()
    window.show()

    print('-' * 50)
    print('  fatih_GUI Test Mode')
    print('  Sidebar: Dashboard | Visualisasi')
    print('  Sinyal navigasi di-print ke terminal')
    print('-' * 50)

    sys.exit(app.exec_())
