import sys
import os

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_GUI_DIR = os.path.join(_THIS_DIR, '..', 'fatih_GUI')
sys.path.insert(0, _GUI_DIR)

try:
    from template_halaman import (
        PageTemplate, font_title, font_body, font_label,
        C_WHITE, C_TEXT_DARK, C_TEXT_SUB, C_NAVBAR, C_NAVBAR_HVR, C_NAVBAR_ACT,
        ICONS_DIR, ASSETS_DIR,
    )
except ModuleNotFoundError:
    _parent = os.path.join(_THIS_DIR, '..', 'pages')
    sys.path.insert(0, _parent)
    from template_halaman import (
        PageTemplate, font_title, font_body, font_label,
        C_WHITE, C_TEXT_DARK, C_TEXT_SUB, C_NAVBAR, C_NAVBAR_HVR, C_NAVBAR_ACT,
        ICONS_DIR, ASSETS_DIR,
    )

import threading
import urllib.request
import ssl

from PyQt5.QtWidgets import (
    QWidget, QLabel, QGridLayout, QVBoxLayout,
    QPushButton, QSizePolicy, QApplication,
)
from PyQt5.QtCore import Qt, QUrl, QObject, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QColor, QLinearGradient, QFont,
    QPixmap, QCursor, QBrush, QPen, QPainterPath,
    QDesktopServices,
)

# Impor JsonHelper dari models.py
from models import JsonHelper

# ─────────────────────────────────────────────
#  WARNA GRADIEN (dirotasi per kartu)
# ─────────────────────────────────────────────
CARD_GRADIENTS = [
    ('#1A7A34', '#2E9E50'),
    ('#1E6E40', '#3AAA5E'),
    ('#176030', '#2B8B48'),
    ('#1B7530', '#36A050'),
    ('#1A6E38', '#329C54'),
    ('#156832', '#2C9848'),
    ('#197228', '#30A044'),
    ('#1C7A3A', '#34A858'),
    ('#157030', '#2A9C4C'),
]


# ─────────────────────────────────────────────
#  HELPER — parsing data JSON
# ─────────────────────────────────────────────
def _bahan_singkat(komposisi: str, maks: int = 4) -> str:
    """
    Ambil maksimal `maks` bahan dari komposisi_singkat (dipisah tanda bullet),
    gabungkan kembali dengan ' • '.
    Contoh: 'ayam•garam•jahe•bawang putih•daun bawang'
            -> 'ayam • garam • jahe • bawang putih  (+1 lainnya)'
    """
    if not komposisi:
        return ''
    items = [b.strip() for b in komposisi.split('\u2022') if b.strip()]
    preview = items[:maks]
    result  = ' \u2022 '.join(preview)
    if len(items) > maks:
        result += f'  (+{len(items) - maks} lainnya)'
    return result


def _fix_url(url: str) -> str:
    """Lengkapi URL protokol-relatif (//) menjadi https://."""
    if url.startswith('//'):
        return 'https:' + url
    return url


def get_formatted_recipes() -> list:
    """
    Ambil data resep via JsonHelper dan kembalikan list dict dengan key:
      name, desc, img_url, link
    """
    json_helper = JsonHelper()
    raw = json_helper.get_resep_harian()
    
    if not raw:
        return []

    result = []
    for item in raw:
        result.append({
            'name'   : item.get('judul', '(Tanpa Judul)'),
            'desc'   : _bahan_singkat(item.get('komposisi_singkat', '')),
            'img_url': _fix_url(item.get('gambar', '')),
            'link'   : item.get('link', ''),
        })
    return result


# ─────────────────────────────────────────────
#  RECIPE CARD WIDGET
# ─────────────────────────────────────────────
class RecipeCard(QWidget):
    """
    Kartu resep fleksibel — rasio 3:4, mengikuti lebar kolom grid.
    Gambar dimuat dari URL secara async; selama loading tampil ilustrasi placeholder.
    Klik tombol ⤢ membuka link resep di browser.
    """

    ASPECT_W = 4
    ASPECT_H = 3
    RADIUS   = 12
    MIN_W    = 140

    def __init__(self, name: str, desc: str, link: str = '',
                 grad_top: str = '#1A7A34', grad_bot: str = '#2E9E50',
                 parent=None):
        super().__init__(parent)
        self._name     = name
        self._desc     = desc
        self._link     = link
        self._grad_top = QColor(grad_top)
        self._grad_bot = QColor(grad_bot)
        self._hovered  = False
        self._img_pix  = None   # QPixmap | None — diisi setelah download selesai

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(self.MIN_W, int(self.MIN_W * self.ASPECT_H / self.ASPECT_W))
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setMouseTracking(True)

        self._build_layout()

    # ── rasio aspek tetap 3:4 ──────────────────
    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        return int(w * self.ASPECT_H / self.ASPECT_W)

    # ── dipanggil oleh RecipeGrid setelah gambar tiba ──
    def set_image(self, pixmap):
        if pixmap and not pixmap.isNull():
            self._img_pix = pixmap
            self.update()

    def _build_layout(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Dorong teks ke bawah — gambar + overlay mengisi penuh via paintEvent
        outer.addStretch(1)

        # area teks di bagian bawah
        text_area = QWidget()
        text_area.setStyleSheet('background: transparent;')
        tlay = QVBoxLayout(text_area)
        tlay.setContentsMargins(14, 6, 42, 12)
        tlay.setSpacing(4)

        self._name_lbl = QLabel(self._name)
        self._name_lbl.setFont(font_title(11))
        self._name_lbl.setStyleSheet('color: #FFFFFF; background: transparent;')
        self._name_lbl.setWordWrap(True)

        self._desc_lbl = QLabel(self._desc)
        self._desc_lbl.setFont(font_body(8))
        self._desc_lbl.setStyleSheet(
            'color: rgba(255,255,255,0.88); background: transparent;')
        self._desc_lbl.setWordWrap(True)

        tlay.addWidget(self._name_lbl)
        tlay.addWidget(self._desc_lbl)
        outer.addWidget(text_area)

        # tombol link pojok kanan bawah
        self._link_btn = QPushButton('\u2197', self)
        self._link_btn.setFixedSize(28, 28)
        self._link_btn.setFont(QFont('Segoe UI Symbol', 12))
        self._link_btn.setStyleSheet("""
            QPushButton {
                color: rgba(255,255,255,0.90);
                background: rgba(255,255,255,0.20);
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.40);
            }
        """)
        self._link_btn.setCursor(QCursor(Qt.PointingHandCursor))
        if self._link:
            self._link_btn.clicked.connect(
                lambda _=False, url=self._link: QDesktopServices.openUrl(QUrl(url))
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        btn = self._link_btn
        btn.move(self.width() - btn.width() - 8,
                 self.height() - btn.height() - 8)

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    # ─────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        rect = self.rect()
        w, h = rect.width(), rect.height()

        # ── rounded clip — seluruh kartu ──
        clip = QPainterPath()
        clip.addRoundedRect(0, 0, w, h, self.RADIUS, self.RADIUS)
        painter.setClipPath(clip)

        # ── 1. Gambar mengisi penuh kartu ──
        if self._img_pix and not self._img_pix.isNull():
            self._draw_full_cover(painter, w, h)
        else:
            # fallback: solid gradient hijau
            c_top = QColor(self._grad_top)
            c_bot = QColor(self._grad_bot)
            if self._hovered:
                c_top = c_top.lighter(115)
                c_bot = c_bot.lighter(115)
            bg = QLinearGradient(0, 0, 0, h)
            bg.setColorAt(0.0, c_top)
            bg.setColorAt(1.0, c_bot)
            painter.fillRect(rect, bg)

        # ── 2. Overlay hijau gradient: transparan di atas → solid di bawah ──
        #    Mulai transparan dari y=0 hingga ~35% kartu,
        #    lalu solid (warna hijau kartu) dari ~60% ke bawah.
        c_solid = QColor(self._grad_bot)
        if self._hovered:
            c_solid = c_solid.lighter(115)

        overlay = QLinearGradient(0, 0, 0, h)
        overlay.setColorAt(0.00, QColor(c_solid.red(), c_solid.green(), c_solid.blue(), 0))
        overlay.setColorAt(0.35, QColor(c_solid.red(), c_solid.green(), c_solid.blue(), 0))
        overlay.setColorAt(0.62, QColor(c_solid.red(), c_solid.green(), c_solid.blue(), 160))
        overlay.setColorAt(1.00, QColor(c_solid.red(), c_solid.green(), c_solid.blue(), 245))
        painter.fillRect(rect, overlay)

        painter.end()

    def _draw_full_cover(self, painter, w, h):
        """Gambar cover mengisi penuh seluruh area kartu (crop tengah)."""
        pix    = self._img_pix
        scaled = pix.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        src_x  = max((scaled.width()  - w) // 2, 0)
        src_y  = max((scaled.height() - h) // 2, 0)
        crop   = scaled.copy(src_x, src_y,
                             min(w, scaled.width()),
                             min(h, scaled.height()))
        painter.drawPixmap(0, 0, crop)

    def _draw_placeholder(self, painter, w, h):
        """Ilustrasi piring di tengah atas kartu sebagai placeholder."""
        # lingkaran piring di area atas
        cx  = w // 2
        cy  = int(h * 0.35)          # tengah ilustrasi berada di 35% atas
        r   = min(w, int(h * 0.55)) // 2 - 12

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 35)))
        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        painter.setBrush(QBrush(QColor(255, 255, 255, 20)))
        painter.drawEllipse(cx - r + 5, cy - r + 5, (r - 5) * 2, (r - 5) * 2)

        leaf_colors = [
            QColor(120, 220, 100, 180), QColor(80, 200, 80, 160),
            QColor(160, 230, 60, 170),  QColor(60, 190, 90, 150),
            QColor(200, 230, 80, 160),
        ]
        leaves = [
            (cx - 10, cy - 8,  22, 11, -30),
            (cx + 2,  cy - 11, 20, 10,  20),
            (cx - 6,  cy + 3,  18,  9,  10),
            (cx + 7,  cy + 2,  16,  8, -15),
            (cx - 3,  cy - 2,  14,  7,  45),
        ]
        for i, (lx, ly, lw, lh, angle) in enumerate(leaves):
            painter.save()
            painter.translate(lx + lw // 2, ly + lh // 2)
            painter.rotate(angle)
            painter.setBrush(QBrush(leaf_colors[i % len(leaf_colors)]))
            painter.drawEllipse(-lw // 2, -lh // 2, lw, lh)
            painter.restore()

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(230, 60, 60, 200)))
        painter.drawEllipse(cx - 5, cy - 5, 9, 9)
        painter.setBrush(QBrush(QColor(230, 80, 80, 160)))
        painter.drawEllipse(cx + 7, cy + 3, 7, 7)


# ─────────────────────────────────────────────
#  IMAGE DOWNLOADER — urllib + thread (SSL 3.x safe)
# ─────────────────────────────────────────────
class _ImageSignal(QObject):
    """Bridge: kirim pixmap dari thread ke main thread via signal."""
    done = pyqtSignal(QPixmap)


def _download_image(url: str, signal: '_ImageSignal'):
    """
    Jalankan di thread terpisah.
    Unduh gambar dari URL lalu emit signal ke main thread.
    """
    try:
        ctx = ssl.create_default_context()   # pakai SSL Python (OpenSSL 3.x OK)
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (NutriKos/1.0)'}
        )
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = resp.read()
        pix = QPixmap()
        pix.loadFromData(data)
        signal.done.emit(pix)
    except Exception as e:
        print(f'[WARN] Gagal unduh gambar ({url[:60]}): {e}')


# ─────────────────────────────────────────────
#  RESPONSIVE GRID  +  ASYNC IMAGE LOADER
# ─────────────────────────────────────────────
class RecipeGrid(QWidget):
    """
    Grid 3 kolom yang selalu memenuhi lebar parent.
    Gambar tiap kartu diunduh secara async via thread + urllib (SSL 3.x aman).
    """

    COLS = 3
    GAP  = 16

    def __init__(self, recipes: list, parent=None):
        super().__init__(parent)
        self.setStyleSheet('background: transparent;')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(self.GAP)
        layout.setVerticalSpacing(self.GAP)

        for c in range(self.COLS):
            layout.setColumnStretch(c, 1)

        total_rows = (len(recipes) + self.COLS - 1) // self.COLS
        for r in range(total_rows):
            layout.setRowStretch(r, 1)

        for idx, recipe in enumerate(recipes):
            row, col           = divmod(idx, self.COLS)
            grad_top, grad_bot = CARD_GRADIENTS[idx % len(CARD_GRADIENTS)]

            card = RecipeCard(
                name     = recipe['name'],
                desc     = recipe['desc'],
                link     = recipe.get('link', ''),
                grad_top = grad_top,
                grad_bot = grad_bot,
            )
            layout.addWidget(card, row, col)

            url = recipe.get('img_url', '')
            if url:
                self._start_download(url, card)

    @staticmethod
    def _start_download(url: str, card: 'RecipeCard'):
        """Buat signal bridge + mulai thread unduh gambar."""
        sig = _ImageSignal()
        sig.done.connect(card.set_image)   # dipanggil di main thread
        t = threading.Thread(
            target=_download_image,
            args=(url, sig),
            daemon=True,
        )
        t.start()


# ─────────────────────────────────────────────
#  HALAMAN RESEP MAKANAN
# ─────────────────────────────────────────────
class HalamanResepMakanan(PageTemplate):
    PAGE_NAME = 'Resep Makanan'
    PAGE_DESC = 'Temukan resep lezat untuk menemani harimu'
    NAV_INDEX = 4

    def build_content(self, container: QWidget):
        recipes = get_formatted_recipes()

        if not recipes:
            lbl = QLabel(
                f'\u26a0  Data resep tidak ditemukan atau kosong.\n'
                f'   Pastikan file Resep.json sudah dibuat atau berhasil di-scrape.'
            )
            lbl.setFont(font_body(10))
            lbl.setStyleSheet(
                f'color: {C_TEXT_SUB};'
                'background: rgba(255,255,255,0.7);'
                'border: 1.5px dashed #aaa; border-radius: 8px;'
                'padding: 24px 20px;'
            )
            lbl.setAlignment(Qt.AlignCenter)
            container.layout().addWidget(lbl)
            return

        grid = RecipeGrid(recipes)
        container.layout().addWidget(grid, 1)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = HalamanResepMakanan()
    window.show()
    sys.exit(app.exec_())