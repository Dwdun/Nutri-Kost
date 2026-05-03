import sys
import os

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

from PyQt5.QtWidgets import (
    QWidget, QLabel, QGridLayout, QVBoxLayout,
    QPushButton, QSizePolicy, QHBoxLayout, QScrollArea,
    QApplication, QFrame,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import (
    QPainter, QColor, QLinearGradient, QFont,
    QPixmap, QCursor, QBrush, QPen, QPainterPath,
)


# ─────────────────────────────────────────────
#  DATA RESEP
# ─────────────────────────────────────────────
RECIPES = [
    {
        'name': 'Salad',
        'desc': 'Campuran sayuran segar yang menyehatkan',
        'icon': 'fluent_bowl-salad-24-filled.png',
    },
    {
        'name': 'Sup Krim Jamur',
        'desc': 'Sup lembut dengan rasa jamur yang kaya dan krim segar',
        'icon': None,
    },
    {
        'name': 'Nasi Goreng',
        'desc': 'Nasi goreng dengan bumbu khas dan tambahan telur serta sayuran',
        'icon': None,
    },
    {
        'name': 'Sate Ayam',
        'desc': 'Tusuk daging ayam yang dipanggang dengan bumbu kacang pedas',
        'icon': None,
    },
    {
        'name': 'Bakso Sapi',
        'desc': 'Bakso kenyal dari daging sapi yang disajikan dengan kuah kaldu',
        'icon': None,
    },
    {
        'name': 'Mie Rebus',
        'desc': 'Mie kuning rebus dengan sayuran dan pilihan daging atau seafood',
        'icon': None,
    },
    {
        'name': 'Rendang Daging',
        'desc': 'Daging sapi dimasak dengan rempah khas hingga empuk dan beraroma',
        'icon': None,
    },
    {
        'name': 'Gado-Gado',
        'desc': 'Sayuran rebus dengan saus kacang yang gurih dan manis',
        'icon': None,
    },
    {
        'name': 'Pecel Lele',
        'desc': 'Ikan lele goreng disajikan dengan sambal terasi pedas',
        'icon': None,
    },
]

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

class RecipeCard(QWidget):
    """
    Kartu resep fleksibel — mengikuti lebar kolom grid (3:4 aspect ratio).
    - Gambar / ilustrasi placeholder di area atas
    - Nama resep (putih, bold)
    - Deskripsi singkat (putih, kecil)
    - Tombol external-link di pojok kanan bawah
    """

    ASPECT_W = 3
    ASPECT_H = 4
    RADIUS   = 14
    MIN_W    = 140

    def __init__(self, name: str, desc: str, icon_path: str = None,
                 grad_top: str = '#1A7A34', grad_bot: str = '#2E9E50',
                 parent=None):
        super().__init__(parent)
        self._name = name
        self._desc = desc
        self._grad_top = QColor(grad_top)
        self._grad_bot = QColor(grad_bot)
        self._hovered = False

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(self.MIN_W, int(self.MIN_W * self.ASPECT_H / self.ASPECT_W))
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setMouseTracking(True)

        self._icon_path = icon_path
        self._icon_pix_raw: QPixmap | None = None
        if icon_path and os.path.exists(icon_path):
            raw = QPixmap(icon_path)
            if not raw.isNull():
                self._icon_pix_raw = raw

        self._build_layout()

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, w: int) -> int:
        return int(w * self.ASPECT_H / self.ASPECT_W)

    def _build_layout(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addStretch(55)

        text_area = QWidget()
        text_area.setStyleSheet('background: transparent;')
        text_lay = QVBoxLayout(text_area)
        text_lay.setContentsMargins(14, 8, 38, 10)
        text_lay.setSpacing(3)

        self._name_lbl = QLabel(self._name)
        self._name_lbl.setFont(font_title(12))
        self._name_lbl.setStyleSheet('color: #FFFFFF; background: transparent;')
        self._name_lbl.setWordWrap(True)

        self._desc_lbl = QLabel(self._desc)
        self._desc_lbl.setFont(font_body(8))
        self._desc_lbl.setStyleSheet('color: rgba(255,255,255,0.85); background: transparent;')
        self._desc_lbl.setWordWrap(True)

        text_lay.addWidget(self._name_lbl)
        text_lay.addWidget(self._desc_lbl)

        outer.addWidget(text_area, 45)

        # tombol external-link pojok kanan bawah (overlay, diposisikan di resizeEvent)
        self._link_btn = QPushButton('⤢', self)
        self._link_btn.setFixedSize(28, 28)
        self._link_btn.setFont(QFont('Segoe UI Symbol', 11))
        self._link_btn.setStyleSheet("""
            QPushButton {
                color: rgba(255,255,255,0.85);
                background: rgba(255,255,255,0.15);
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.30);
            }
        """)
        self._link_btn.setCursor(QCursor(Qt.PointingHandCursor))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        btn = self._link_btn
        btn.move(
            self.width()  - btn.width()  - 8,
            self.height() - btn.height() - 8,
        )

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        rect = self.rect()

        path = QPainterPath()
        path.addRoundedRect(0, 0, rect.width(), rect.height(), self.RADIUS, self.RADIUS)
        painter.setClipPath(path)

        grad = QLinearGradient(0, 0, 0, rect.height())
        top = QColor(self._grad_top)
        bot = QColor(self._grad_bot)
        if self._hovered:
            top = top.lighter(115)
            bot = bot.lighter(115)
        grad.setColorAt(0.0, top)
        grad.setColorAt(1.0, bot)
        painter.fillRect(rect, grad)

        # area gambar = 55% tinggi kartu
        img_h = int(rect.height() * 0.55)

        if self._icon_pix_raw:
            # scale ikon proporsional terhadap ukuran kartu
            icon_size = int(min(rect.width(), img_h) * 0.55)
            icon_size = max(icon_size, 32)
            scaled = self._icon_pix_raw.scaled(
                icon_size, icon_size,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            x = (rect.width() - scaled.width()) // 2
            y = (img_h - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            self._draw_food_illustration(painter, rect.width(), img_h)

        # ── subtle overlay gradient di area teks ──
        overlay = QLinearGradient(0, img_h - 30, 0, rect.height())
        overlay.setColorAt(0.0, QColor(0, 0, 0, 0))
        overlay.setColorAt(1.0, QColor(0, 0, 0, 60))
        painter.fillRect(0, img_h - 30, rect.width(), rect.height() - img_h + 30, overlay)

        painter.end()

    def _draw_food_illustration(self, painter: QPainter, w: int, h: int):
        """Gambar placeholder piring + sayuran sederhana."""
        cx, cy = w // 2, h // 2

        # piring (lingkaran putih semi-transparan)
        plate_r = min(w, h) // 2 - 16
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 40)))
        painter.drawEllipse(cx - plate_r, cy - plate_r, plate_r * 2, plate_r * 2)

        painter.setBrush(QBrush(QColor(255, 255, 255, 25)))
        painter.drawEllipse(cx - plate_r + 6, cy - plate_r + 6,
                            (plate_r - 6) * 2, (plate_r - 6) * 2)

        # daun / sayuran (beberapa elips hijau muda)
        colors = [
            QColor(120, 220, 100, 180),
            QColor(80, 200, 80, 160),
            QColor(160, 230, 60, 170),
            QColor(60, 190, 90, 150),
            QColor(200, 230, 80, 160),
        ]
        leaf_data = [
            (cx - 12, cy - 10, 28, 14, -30),
            (cx + 2,  cy - 14, 24, 12,  20),
            (cx - 8,  cy + 4,  22, 11,  10),
            (cx + 8,  cy + 2,  20, 10, -15),
            (cx - 4,  cy - 2,  18,  9,  45),
        ]
        for i, (lx, ly, lw, lh, angle) in enumerate(leaf_data):
            painter.save()
            painter.translate(lx + lw // 2, ly + lh // 2)
            painter.rotate(angle)
            painter.setBrush(QBrush(colors[i % len(colors)]))
            painter.drawEllipse(-lw // 2, -lh // 2, lw, lh)
            painter.restore()

        # garpu kecil (garis putih)
        pen = QPen(QColor(255, 255, 255, 120), 2)
        painter.setPen(pen)
        fx = cx + plate_r - 14
        fy = cy - 14
        painter.drawLine(fx, fy, fx, fy + 28)
        painter.drawLine(fx - 4, fy, fx - 4, fy + 14)
        painter.drawLine(fx + 4, fy, fx + 4, fy + 14)

        # tomat merah kecil
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(230, 60, 60, 200)))
        painter.drawEllipse(cx - 6, cy - 6, 10, 10)
        painter.setBrush(QBrush(QColor(230, 80, 80, 160)))
        painter.drawEllipse(cx + 8, cy + 4, 8, 8)


class RecipeGrid(QWidget):
    """
    Grid 3 kolom yang selalu mengisi lebar penuh.
    Kartu mengikuti rasio 3:4 secara otomatis lewat heightForWidth().
    """

    COLS    = 3
    GAP     = 16

    def __init__(self, recipes: list, gradients: list, icons_dir: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet('background: transparent;')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(self.GAP)
        self._grid.setVerticalSpacing(self.GAP)

        for c in range(self.COLS):
            self._grid.setColumnStretch(c, 1)

        for idx, recipe in enumerate(recipes):
            row, col = divmod(idx, self.COLS)
            grad_top, grad_bot = gradients[idx % len(gradients)]

            icon_path = None
            if recipe.get('icon'):
                p = os.path.join(icons_dir, recipe['icon'])
                if os.path.exists(p):
                    icon_path = p

            card = RecipeCard(
                name=recipe['name'],
                desc=recipe['desc'],
                icon_path=icon_path,
                grad_top=grad_top,
                grad_bot=grad_bot,
            )
            self._grid.addWidget(card, row, col)

        # Baris stretch rata
        total_rows = (len(recipes) + self.COLS - 1) // self.COLS
        for r in range(total_rows):
            self._grid.setRowStretch(r, 1)


class HalamanResepMakanan(PageTemplate):
    PAGE_NAME = 'Resep Makanan'
    PAGE_DESC = 'Temukan resep lezat untuk menemani harimu'
    NAV_INDEX = 4   # "Resep Makanan" = indeks ke-4 di sidebar

    def build_content(self, container: QWidget):
        grid = RecipeGrid(
            recipes=RECIPES,
            gradients=CARD_GRADIENTS,
            icons_dir=ICONS_DIR,
        )
        # Isi seluruh lebar & tinggi container tersedia
        container.layout().addWidget(grid, 1)


if __name__ == '__main__':
    # Untuk bisa dijalankan langsung, template_halaman.py harus ada
    # di folder yang sama, atau sesuaikan sys.path di atas.
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = HalamanResepMakanan()
    window.show()
    sys.exit(app.exec_())