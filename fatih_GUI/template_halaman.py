import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QScrollArea, QPushButton,
    QFrame, QSizePolicy, QSpacerItem,
)
from PyQt5.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QSize,
    pyqtProperty, QPoint,
)
from PyQt5.QtGui import (
    QFont, QFontDatabase, QPixmap, QPainter,
    QColor, QIcon, QPalette, QBrush, QCursor,
)

# ─────────────────────────────────────────────
#  PATH SETUP
# ─────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, '..', 'assets')
ICONS_DIR  = os.path.join(ASSETS_DIR, 'icons')
FONTS_DIR  = os.path.join(ASSETS_DIR, 'fonts')
PATTERN_PATH = os.path.join(ASSETS_DIR, 'pattern.png')

# ─────────────────────────────────────────────
#  DESIGN TOKENS
# ─────────────────────────────────────────────
C_NAVBAR      = '#1A7A34'   # sidebar & header
C_NAVBAR_HVR  = '#3C8E52'   # hover item
C_NAVBAR_ACT  = '#5EA271'   # active/selected
C_CONTENT_BG  = '#F2F4F0'   # halaman konten
C_WHITE       = '#FFFFFF'
C_TEXT_DARK   = '#1C1C1C'
C_TEXT_SUB    = '#555555'
C_DIVIDER     = 'rgba(255,255,255,0.25)'
C_SECTION_LBL = 'rgba(255,255,255,0.55)'

SIDEBAR_EXP   = 320   # lebar sidebar saat expand (px)
SIDEBAR_COL   = 76    # lebar sidebar saat collapse (px)
HEADER_H      = 76    # tinggi header bar (px)
ANIM_MS       = 280   # durasi animasi (ms)
PATTERN_TILE  = 150   # ukuran tile pattern (px)
PATTERN_ALPHA = 0.07  # transparansi pattern

NAV_ITEM_H    = 48    # tinggi tiap nav item (px)
NAV_ICON_W    = 76    # lebar kolom icon (sama dgn SIDEBAR_COL)
NAV_SECTION_H = 32    # tinggi section label
NAV_SECTION_GAP = 16  # spasi sebelum section label


# ─────────────────────────────────────────────
#  FONT LOADER
# ─────────────────────────────────────────────
_fonts_loaded = False

def load_fonts():
    global _fonts_loaded
    if _fonts_loaded:
        return
    if os.path.exists(FONTS_DIR):
        for fname in os.listdir(FONTS_DIR):
            if fname.lower().endswith(('.ttf', '.otf')):
                QFontDatabase.addApplicationFont(os.path.join(FONTS_DIR, fname))
    _fonts_loaded = True


def font_title(size: int = 18) -> QFont:
    """Montserrat Alternates Bold — untuk judul halaman."""
    f = QFont('Montserrat Alternates', size, QFont.Bold)
    f.setStyleHint(QFont.SansSerif)
    return f


def font_body(size: int = 10) -> QFont:
    """Poppins Regular — untuk deskripsi & konten."""
    f = QFont('Poppins', size)
    f.setStyleHint(QFont.SansSerif)
    return f


def font_label(size: int = 9, bold: bool = False) -> QFont:
    """Poppins Medium — untuk label kecil."""
    f = QFont('Poppins', size, QFont.Medium if bold else QFont.Normal)
    f.setStyleHint(QFont.SansSerif)
    return f


# ─────────────────────────────────────────────
#  TILED PATTERN BACKGROUND
# ─────────────────────────────────────────────
class PatternWidget(QWidget):
    """Widget dengan background pattern.png yang di-tile."""

    def __init__(self, parent=None):
        super().__init__(parent)
        raw = QPixmap(PATTERN_PATH)
        if not raw.isNull():
            self._tile = raw.scaled(
                PATTERN_TILE, PATTERN_TILE,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        else:
            self._tile = QPixmap()

    def paintEvent(self, event):
        painter = QPainter(self)
        # solid background
        painter.fillRect(self.rect(), QColor(C_CONTENT_BG))
        # tiled pattern
        if not self._tile.isNull():
            painter.setOpacity(PATTERN_ALPHA)
            tw = self._tile.width()
            th = self._tile.height()
            x = 0
            while x < self.width():
                y = 0
                while y < self.height():
                    painter.drawPixmap(x, y, self._tile)
                    y += th
                x += tw
        painter.end()


# ─────────────────────────────────────────────
#  NAV ITEM BUTTON
# ─────────────────────────────────────────────
class NavItem(QPushButton):
    """
    Tombol navigasi dengan ikon (PNG file / QPixmap) + teks label.
    Saat collapsed, teks disembunyikan.
    """

    def __init__(self, icon_path: str, label: str, parent=None):
        super().__init__(parent)
        self._icon_path = icon_path
        self._label     = label
        self._collapsed = False

        self.setCheckable(True)
        self.setFixedHeight(NAV_ITEM_H)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        self._build_layout()
        self._apply_style()

    def _build_layout(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 12, 0)
        layout.setSpacing(0)

        # kolom ikon — lebar tetap, selalu centered
        self._icon_lbl = QLabel()
        self._icon_lbl.setAlignment(Qt.AlignCenter)
        self._icon_lbl.setFixedWidth(NAV_ICON_W)
        self._icon_lbl.setStyleSheet('background: transparent;')

        # load icon dari file
        if os.path.exists(self._icon_path):
            pix = QPixmap(self._icon_path)
            if not pix.isNull():
                scaled = pix.scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._icon_lbl.setPixmap(scaled)
        else:
            self._icon_lbl.setText('•')
            self._icon_lbl.setFont(QFont('Segoe UI Symbol', 16))
            self._icon_lbl.setStyleSheet(
                f'color: {C_WHITE}; background: transparent;'
            )

        # teks label
        self._text_lbl = QLabel(self._label)
        self._text_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self._text_lbl.setFont(font_label(10))
        self._text_lbl.setStyleSheet(
            f'color: {C_WHITE}; background: transparent;'
        )

        layout.addWidget(self._icon_lbl)
        layout.addWidget(self._text_lbl, 1)

    def _apply_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-left: 3px solid transparent;
            }}
            QPushButton:hover {{
                background: {C_NAVBAR_HVR};
            }}
            QPushButton:checked {{
                background: {C_NAVBAR_ACT};
                border-left: 3px solid {C_WHITE};
            }}
        """)

    def set_collapsed(self, collapsed: bool):
        self._collapsed = collapsed
        self._text_lbl.setVisible(not collapsed)

    def set_icon_pixmap(self, pixmap: 'QPixmap'):
        """Ganti icon dengan QPixmap dari file."""
        scaled = pixmap.scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._icon_lbl.setPixmap(scaled)
        self._icon_lbl.setText('')


# ─────────────────────────────────────────────
#  SECTION LABEL (kecil, muted)
# ─────────────────────────────────────────────
class SectionLabel(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFont(font_label(8))
        self.setFixedHeight(NAV_SECTION_H)
        self.setContentsMargins(NAV_ICON_W, 0, 0, 0)   # indent rata dgn teks nav item
        self.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.setStyleSheet(f'color: {C_SECTION_LBL}; background: transparent;')
        self._full_text = text

    def set_collapsed(self, collapsed: bool):
        if collapsed:
            self.setText('')
        else:
            self.setText(self._full_text)


# ─────────────────────────────────────────────
#  SIDEBAR NAVBAR
# ─────────────────────────────────────────────
class Sidebar(QWidget):
    """
    Sidebar yang bisa expand / collapse dengan animasi.
    Terhubung ke main window melalui signal/callback.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self._nav_items: list[NavItem] = []
        self._section_labels: list[SectionLabel] = []

        self.setFixedWidth(SIDEBAR_EXP)
        self.setMinimumWidth(SIDEBAR_COL)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self._anim = QPropertyAnimation(self, b'minimumWidth')
        self._anim.setDuration(ANIM_MS)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)
        # animasi untuk maximumWidth
        self._anim_max = QPropertyAnimation(self, b'maximumWidth')
        self._anim_max.setDuration(ANIM_MS)
        self._anim_max.setEasingCurve(QEasingCurve.InOutCubic)

        self._build_ui()

    # ── Build UI ──
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Logo area ──
        logo_widget = QWidget()
        logo_widget.setFixedHeight(HEADER_H)
        logo_widget.setStyleSheet('background: transparent;')
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(0)
        logo_layout.setAlignment(Qt.AlignVCenter)  # fix: logo & teks rata tengah vertikal

        # logo icon — dari assets/icons/Logo.png
        logo_icon_lbl = QLabel()
        logo_icon_lbl.setFixedSize(NAV_ICON_W, HEADER_H)
        logo_icon_lbl.setAlignment(Qt.AlignCenter)
        logo_icon_lbl.setStyleSheet('background: transparent;')
        logo_path = os.path.join(ICONS_DIR, 'Logo.png')
        raw_logo = QPixmap(logo_path)
        if not raw_logo.isNull():
            logo_icon_lbl.setPixmap(
                raw_logo.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            logo_icon_lbl.setText('🥗')
            logo_icon_lbl.setFont(QFont('Segoe UI Symbol', 22))
            logo_icon_lbl.setStyleSheet('color: white; background: transparent;')

        # logo text — dari assets/icons/Logo text.png
        self._logo_text = QLabel()
        self._logo_text.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self._logo_text.setStyleSheet('background: transparent;')
        logo_text_path = os.path.join(ICONS_DIR, 'Logo text.png')
        raw_logo_text = QPixmap(logo_text_path)
        if not raw_logo_text.isNull():
            self._logo_text.setPixmap(
                raw_logo_text.scaled(
                    140, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
        else:
            self._logo_text.setText('NUTRIKOST')
            self._logo_text.setFont(font_title(13))
            self._logo_text.setStyleSheet(
                f'color: {C_WHITE}; background: transparent; letter-spacing: 1px;'
            )

        logo_layout.addWidget(logo_icon_lbl)
        logo_layout.addWidget(self._logo_text, 1)
        root.addWidget(logo_widget)

        # ── Divider ──
        root.addWidget(self._divider())

        # gap atas sebelum section label (konsisten expand/collapse)
        self._gap_top = QWidget()
        self._gap_top.setFixedHeight(NAV_SECTION_GAP)
        self._gap_top.setStyleSheet('background: transparent;')
        root.addWidget(self._gap_top)

        # ── Menu Utama ──
        self._lbl_menu = SectionLabel('Menu Utama')
        self._section_labels.append(self._lbl_menu)
        root.addWidget(self._lbl_menu)

        menu_items = [
            ('material-symbols_home-rounded.png',    'Home Dashboard'),
            ('fe_search.png',                        'Cari Makanan'),
            ('material-symbols_list-alt-rounded.png', 'Log Makanan'),
            ('iconamoon_history-bold.png',            'Riwayat'),
            ('fluent_bowl-salad-24-filled.png',       'Resep Makanan'),
        ]
        for icon_file, label in menu_items:
            icon_path = os.path.join(ICONS_DIR, icon_file)
            item = NavItem(icon_path, label, self)
            self._nav_items.append(item)
            root.addWidget(item)

        # gap antar section (konsisten expand/collapse)
        self._gap_mid = QWidget()
        self._gap_mid.setFixedHeight(NAV_SECTION_GAP)
        self._gap_mid.setStyleSheet('background: transparent;')
        root.addWidget(self._gap_mid)

        # ── Visualisasi ──
        self._lbl_vis = SectionLabel('Visualisasi')
        self._section_labels.append(self._lbl_vis)
        root.addWidget(self._lbl_vis)

        vis_items = [
            ('material-symbols_bar-chart-rounded.png', 'Kalori Mingguan'),
            ('fa7-solid_chart-pie.png',                'Komposisi Gizi'),
            ('mingcute_list-ordered-fill.png',          'Top 10 Makanan'),
        ]
        for icon_file, label in vis_items:
            icon_path = os.path.join(ICONS_DIR, icon_file)
            item = NavItem(icon_path, label, self)
            self._nav_items.append(item)
            root.addWidget(item)

        # spacer dorong ke bawah
        root.addStretch(1)

        # ── Pengaturan ──
        settings_icon = os.path.join(ICONS_DIR, 'solar_settings-bold.png')
        settings_item = NavItem(settings_icon, 'Pengaturan', self)
        self._nav_items.append(settings_item)
        root.addWidget(settings_item)

        # ── Divider ──
        root.addWidget(self._divider())

        # ── Profile (clickable) ──
        self._profile_btn = self._build_profile_btn()
        root.addWidget(self._profile_btn)

        # set nav item pertama aktif
        if self._nav_items:
            self._nav_items[0].setChecked(True)

    def _divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(f'background: {C_DIVIDER}; border: none;')
        return line

    def _build_profile_btn(self) -> QPushButton:
        """Profile row yang bisa diklik."""
        btn = QPushButton()
        btn.setFixedHeight(64)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-left: 3px solid transparent;
            }}
            QPushButton:hover {{
                background: {C_NAVBAR_HVR};
            }}
        """)

        lay = QHBoxLayout(btn)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(0)
        lay.setAlignment(Qt.AlignVCenter)

        # avatar icon — dari assets/icons/gg_profile.png
        self._avatar_lbl = QLabel()
        self._avatar_lbl.setFixedSize(NAV_ICON_W, 64)
        self._avatar_lbl.setAlignment(Qt.AlignCenter)
        self._avatar_lbl.setStyleSheet('background: transparent;')
        profile_icon_path = os.path.join(ICONS_DIR, 'gg_profile.png')
        profile_pix = QPixmap(profile_icon_path)
        if not profile_pix.isNull():
            self._avatar_lbl.setPixmap(
                profile_pix.scaled(26, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self._avatar_lbl.setText('◉')
            self._avatar_lbl.setFont(QFont('Segoe UI Symbol', 22))
            self._avatar_lbl.setStyleSheet(f'color: {C_WHITE}; background: transparent;')

        # nama & email
        self._info_col = QWidget()
        self._info_col.setStyleSheet('background: transparent;')
        info_lay = QVBoxLayout(self._info_col)
        info_lay.setContentsMargins(0, 0, 0, 0)
        info_lay.setSpacing(1)

        self._username_lbl = QLabel('Profile')
        self._username_lbl.setFont(font_label(10, bold=True))
        self._username_lbl.setStyleSheet(f'color: {C_WHITE}; background: transparent;')

        self._email_lbl = QLabel('username@gmail.com')
        self._email_lbl.setFont(font_label(8))
        self._email_lbl.setStyleSheet(f'color: {C_SECTION_LBL}; background: transparent;')

        info_lay.addWidget(self._username_lbl)
        info_lay.addWidget(self._email_lbl)

        # logout btn — dari assets/icons/material-symbols_logout-rounded.png
        self._logout_btn = QPushButton()
        self._logout_btn.setFixedSize(36, 36)
        self._logout_btn.setCursor(QCursor(Qt.PointingHandCursor))
        logout_icon_path = os.path.join(ICONS_DIR, 'material-symbols_logout-rounded.png')
        logout_pix = QPixmap(logout_icon_path)
        if not logout_pix.isNull():
            self._logout_btn.setIcon(QIcon(logout_pix))
            self._logout_btn.setIconSize(QSize(20, 20))
        else:
            self._logout_btn.setText('⎋')
            self._logout_btn.setFont(QFont('Segoe UI Symbol', 14))
        self._logout_btn.setStyleSheet(f"""
            QPushButton {{
                color: {C_WHITE};
                background: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {C_NAVBAR_HVR};
            }}
        """)
        self._logout_btn.setVisible(True)

        lay.addWidget(self._avatar_lbl)
        lay.addWidget(self._info_col, 1)
        lay.addWidget(self._logout_btn)
        lay.addSpacing(8)
        return btn

    # ── Animasi toggle ──
    def toggle(self):
        self._collapsed = not self._collapsed
        target_w = SIDEBAR_COL if self._collapsed else SIDEBAR_EXP
        current_w = self.width()

        self._anim.stop()
        self._anim_max.stop()

        self._anim.setStartValue(current_w)
        self._anim.setEndValue(target_w)
        self._anim_max.setStartValue(current_w)
        self._anim_max.setEndValue(target_w)

        self._anim.start()
        self._anim_max.start()

        # tampilkan/sembunyikan teks
        self._logo_text.setVisible(not self._collapsed)
        for lbl in self._section_labels:
            lbl.set_collapsed(self._collapsed)
        self._info_col.setVisible(not self._collapsed)
        self._logout_btn.setVisible(not self._collapsed)

        for item in self._nav_items:
            item.set_collapsed(self._collapsed)

    def paintEvent(self, event):
        """Force-paint hijau agar tidak di-override oleh Qt style."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(C_NAVBAR))
        painter.end()

    def set_active_page(self, index: int):
        for i, item in enumerate(self._nav_items):
            item.setChecked(i == index)


# ─────────────────────────────────────────────
#  HEADER BAR (tidak ikut scroll)
# ─────────────────────────────────────────────
class HeaderBar(QWidget):
    def __init__(self, page_name: str = 'Nama Halaman', parent=None):
        super().__init__(parent)
        self.setFixedHeight(HEADER_H)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # tombol hamburger toggle sidebar
        self._toggle_btn = QPushButton('☰')
        self._toggle_btn.setFixedSize(36, 36)
        self._toggle_btn.setFont(QFont('Segoe UI Symbol', 16))
        self._toggle_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._toggle_btn.setStyleSheet(f"""
            QPushButton {{
                color: {C_WHITE};
                background: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {C_NAVBAR_HVR};
            }}
            QPushButton:pressed {{
                background: {C_NAVBAR_ACT};
            }}
        """)

        # judul halaman di tengah
        self._title_lbl = QLabel(f'NutriKos — {page_name}')
        self._title_lbl.setFont(font_label(11, bold=True))
        self._title_lbl.setStyleSheet(f'color: {C_WHITE}; background: transparent;')
        self._title_lbl.setAlignment(Qt.AlignCenter)

        layout.addWidget(self._toggle_btn)
        layout.addWidget(self._title_lbl, 1)

    @property
    def toggle_btn(self) -> QPushButton:
        return self._toggle_btn

    def set_page_name(self, name: str):
        self._title_lbl.setText(f'NutriKos — {name}')

    def paintEvent(self, event):
        """Force-paint hijau agar tidak di-override oleh Qt style."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(C_NAVBAR))
        painter.end()


# ─────────────────────────────────────────────
#  PAGE TEMPLATE — subclass ini untuk tiap halaman
# ─────────────────────────────────────────────
class PageTemplate(QMainWindow):
    """
    Template utama NutriKost.

    Cara pakai:
    -----------
    class HalamanKu(PageTemplate):
        PAGE_NAME  = 'Home Dashboard'
        PAGE_DESC  = 'Ringkasan data nutrisi harianmu'
        NAV_INDEX  = 0               # indeks aktif di navbar

        def build_content(self, container: QWidget):
            # tambahkan widget ke dalam container
            lbl = QLabel('Halo dunia!')
            lbl.setFont(self.font_body())
            container.layout().addWidget(lbl)
    """

    PAGE_NAME  = 'Nama Halaman'
    PAGE_DESC  = 'Deskripsi singkat halaman ini'
    NAV_INDEX  = 0                  # override sesuai halaman

    def __init__(self):
        super().__init__()
        load_fonts()

        self.setWindowTitle(f'NutriKos — {self.PAGE_NAME}')
        self.setMinimumSize(900, 600)
        self.resize(1200, 720)

        # set window icon ke logo NutriKost
        logo_icon_path = os.path.join(ICONS_DIR, 'Logo.png')
        if os.path.exists(logo_icon_path):
            self.setWindowIcon(QIcon(logo_icon_path))

        self._build_ui()
        self._sidebar.set_active_page(self.NAV_INDEX)
        self.build_content(self._content_container)

    # ── Build ──
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # header tetap di atas
        self._header = HeaderBar(self.PAGE_NAME)
        self._header.toggle_btn.clicked.connect(self._on_toggle)
        root_layout.addWidget(self._header)

        # area di bawah header
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        root_layout.addWidget(body, 1)

        # sidebar
        self._sidebar = Sidebar()
        body_layout.addWidget(self._sidebar)

        # content wrapper dengan tiled background (tidak scroll)
        content_wrapper = PatternWidget()
        content_wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        body_layout.addWidget(content_wrapper, 1)

        wrapper_layout = QVBoxLayout(content_wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(0)

        # scroll area (transparent supaya pattern terlihat)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setStyleSheet('QScrollArea { background: transparent; border: none; }')
        self._scroll.viewport().setStyleSheet('background: transparent;')
        wrapper_layout.addWidget(self._scroll)

        # inner widget (konten halaman)
        inner = QWidget()
        inner.setStyleSheet('background: transparent;')
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(32, 28, 32, 32)
        inner_layout.setSpacing(0)
        inner_layout.setAlignment(Qt.AlignTop)

        # judul halaman
        self._page_title = QLabel(self.PAGE_NAME)
        self._page_title.setFont(font_title(20))
        self._page_title.setStyleSheet(f'color: {C_TEXT_DARK}; background: transparent;')

        # deskripsi
        self._page_desc = QLabel(self.PAGE_DESC)
        self._page_desc.setFont(font_body(10))
        self._page_desc.setStyleSheet(f'color: {C_TEXT_SUB}; background: transparent;')

        inner_layout.addWidget(self._page_title)
        inner_layout.addSpacing(4)
        inner_layout.addWidget(self._page_desc)
        inner_layout.addSpacing(24)

        # ── container untuk konten dari subclass ──
        self._content_container = QWidget()
        self._content_container.setStyleSheet('background: transparent;')
        self._content_layout = QVBoxLayout(self._content_container)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(16)
        self._content_layout.setAlignment(Qt.AlignTop)

        inner_layout.addWidget(self._content_container, 1)
        inner_layout.addStretch()

        self._scroll.setWidget(inner)

    # ── Callback ──
    def _on_toggle(self):
        self._sidebar.toggle()

    # ── Helper font (akses dari subclass) ──
    @staticmethod
    def font_title(size: int = 18) -> QFont:
        return font_title(size)

    @staticmethod
    def font_body(size: int = 10) -> QFont:
        return font_body(size)

    @staticmethod
    def font_label(size: int = 9, bold: bool = False) -> QFont:
        return font_label(size, bold)

    # ── Override di subclass ──
    def build_content(self, container: QWidget):
        """
        Tambahkan widget ke dalam container ini.
        Layout container sudah QVBoxLayout — tinggal addWidget().

        Contoh:
            label = QLabel('Halo!')
            label.setFont(self.font_body())
            container.layout().addWidget(label)
        """
        pass   # override di subclass


# ─────────────────────────────────────────────
#  PREVIEW — jalankan file ini langsung
# ─────────────────────────────────────────────
class _PreviewPage(PageTemplate):
    PAGE_NAME = 'Nama Halaman'
    PAGE_DESC = 'Deskripsi singkat halaman ini'
    NAV_INDEX = 0

    def build_content(self, container: QWidget):
        # placeholder konten
        placeholder = QLabel(
            '📌  Konten halaman ditambahkan di sini.\n'
            '    Override method build_content() di subclass kamu.'
        )
        placeholder.setFont(font_body(10))
        placeholder.setStyleSheet(
            f'color: {C_TEXT_SUB};'
            'background: rgba(255,255,255,0.7);'
            'border: 1.5px dashed #aaa;'
            'border-radius: 8px;'
            'padding: 24px 20px;'
        )
        placeholder.setAlignment(Qt.AlignCenter)
        container.layout().addWidget(placeholder)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = _PreviewPage()
    window.show()
    sys.exit(app.exec_())