import sys
import os
import json

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_GUI_DIR = os.path.join(_THIS_DIR, 'fatih_GUI')
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


# ─────────────────────────────────────────────
#  PATH JSON — sesuaikan jika perlu
# ─────────────────────────────────────────────
JSON_PATH = os.path.join(_THIS_DIR, 'Resep.json')


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


def load_recipes_from_json(path: str) -> list:
    """
    Baca file JSON dan kembalikan list dict dengan key:
      name, desc, img_url, link
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
    except FileNotFoundError:
        print(f'[WARN] File JSON tidak ditemukan: {path}')
        return []
    except json.JSONDecodeError as e:
        print(f'[WARN] Gagal parse JSON: {e}')
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

    ASPECT_W = 3
    ASPECT_H = 4
    RADIUS   = 14
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

        # area gambar — 55% tinggi kartu
        outer.addStretch(55)

        # area teks — 45% tinggi kartu
        text_area = QWidget()
        text_area.setStyleSheet('background: transparent;')
        tlay = QVBoxLayout(text_area)
        tlay.setContentsMargins(14, 8, 38, 10)
        tlay.setSpacing(4)

        # judul (maksimal 2 baris, truncate jika lebih)
        self._name_lbl = QLabel(self._name)
        self._name_lbl.setFont(font_title(11))
        self._name_lbl.setStyleSheet('color: #FFFFFF; background: transparent;')
        self._name_lbl.setWordWrap(True)
        self._name_lbl.setMaximumHeight(50)

        # bahan singkat
        self._desc_lbl = QLabel(self._desc)
        self._desc_lbl.setFont(font_body(8))
        self._desc_lbl.setStyleSheet(
            'color: rgba(255,255,255,0.85); background: transparent;')
        self._desc_lbl.setWordWrap(True)

        tlay.addWidget(self._name_lbl)
        tlay.addWidget(self._desc_lbl)
        outer.addWidget(text_area, 45)

        # tombol buka link — pojok kanan bawah (posisi diatur di resizeEvent)
        self._link_btn = QPushButton('\u29c2', self)   # ⧂ → pakai karakter lain jika kosong
        self._link_btn.setText('\u2197')               # ↗
        self._link_btn.setFixedSize(28, 28)
        self._link_btn.setFont(QFont('Segoe UI Symbol', 12))
        self._link_btn.setStyleSheet("""
            QPushButton {
                color: rgba(255,255,255,0.90);
                background: rgba(255,255,255,0.18);
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.38);
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

        rect  = self.rect()
        img_h = int(rect.height() * 0.55)

        # rounded clip
        clip = QPainterPath()
        clip.addRoundedRect(0, 0, rect.width(), rect.height(),
                            self.RADIUS, self.RADIUS)
        painter.setClipPath(clip)

        # gradient background
        c_top = QColor(self._grad_top)
        c_bot = QColor(self._grad_bot)
        if self._hovered:
            c_top = c_top.lighter(115)
            c_bot = c_bot.lighter(115)
        grad = QLinearGradient(0, 0, 0, rect.height())
        grad.setColorAt(0.0, c_top)
        grad.setColorAt(1.0, c_bot)
        painter.fillRect(rect, grad)

        # gambar atau ilustrasi placeholder
        if self._img_pix and not self._img_pix.isNull():
            self._draw_cover(painter, rect.width(), img_h)
        else:
            self._draw_placeholder(painter, rect.width(), img_h)

        # overlay gradient di batas gambar–teks
        fade = QLinearGradient(0, img_h - 40, 0, rect.height())
        fade.setColorAt(0.0, QColor(0, 0, 0, 0))
        fade.setColorAt(1.0, QColor(0, 0, 0, 90))
        painter.fillRect(0, img_h - 40, rect.width(),
                         rect.height() - img_h + 40, fade)

        painter.end()

    def _draw_cover(self, painter, w, img_h):
        """
        Gambar sebagai cover — skala memenuhi area, crop tengah,
        ditambah vignette ringan agar blend dengan gradien.
        """
        pix = self._img_pix
        # skala agar cover penuh (bisa crop)
        scaled = pix.scaled(w, img_h,
                            Qt.KeepAspectRatioByExpanding,
                            Qt.SmoothTransformation)
        src_x = max((scaled.width()  - w)    // 2, 0)
        src_y = max((scaled.height() - img_h) // 2, 0)
        crop  = scaled.copy(src_x, src_y,
                            min(w,    scaled.width()),
                            min(img_h, scaled.height()))
        painter.drawPixmap(0, 0, crop)

        # vignette ringan agar gambar blend dengan warna kartu
        vig = QLinearGradient(0, 0, 0, img_h)
        vig.setColorAt(0.0, QColor(0, 0, 0, 50))
        vig.setColorAt(0.5, QColor(0, 0, 0, 10))
        vig.setColorAt(1.0, QColor(0, 0, 0, 80))
        painter.fillRect(0, 0, w, img_h, vig)

    def _draw_placeholder(self, painter, w, h):
        """Ilustrasi piring + sayuran sebagai placeholder."""
        cx, cy    = w // 2, h // 2
        plate_r   = min(w, h) // 2 - 16

        painter.setPen(Qt.NoPen)
        for alpha in (40, 25):
            painter.setBrush(QBrush(QColor(255, 255, 255, alpha)))
            off = 0 if alpha == 40 else 6
            r   = plate_r - off
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        leaf_colors = [
            QColor(120, 220, 100, 180), QColor(80,  200, 80,  160),
            QColor(160, 230, 60,  170), QColor(60,  190, 90,  150),
            QColor(200, 230, 80,  160),
        ]
        leaves = [
            (cx - 12, cy - 10, 28, 14, -30),
            (cx + 2,  cy - 14, 24, 12,  20),
            (cx - 8,  cy + 4,  22, 11,  10),
            (cx + 8,  cy + 2,  20, 10, -15),
            (cx - 4,  cy - 2,  18,  9,  45),
        ]
        for i, (lx, ly, lw, lh, angle) in enumerate(leaves):
            painter.save()
            painter.translate(lx + lw // 2, ly + lh // 2)
            painter.rotate(angle)
            painter.setBrush(QBrush(leaf_colors[i % len(leaf_colors)]))
            painter.drawEllipse(-lw // 2, -lh // 2, lw, lh)
            painter.restore()

        painter.setPen(QPen(QColor(255, 255, 255, 120), 2))
        fx, fy = cx + plate_r - 14, cy - 14
        painter.drawLine(fx, fy, fx, fy + 28)
        painter.drawLine(fx - 4, fy, fx - 4, fy + 14)
        painter.drawLine(fx + 4, fy, fx + 4, fy + 14)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(230, 60,  60,  200)))
        painter.drawEllipse(cx - 6, cy - 6, 10, 10)
        painter.setBrush(QBrush(QColor(230, 80,  80,  160)))
        painter.drawEllipse(cx + 8, cy + 4,  8,  8)


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
        recipes = load_recipes_from_json(JSON_PATH)

        if not recipes:
            lbl = QLabel(
                f'\u26a0  Data resep tidak ditemukan.\n'
                f'   Pastikan file Resep.json ada di folder yang sama:\n'
                f'   {JSON_PATH}'
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