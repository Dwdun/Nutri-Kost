import sys
import os
import json
import sqlite3
import re
import threading
import urllib.request
import ssl

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QSizePolicy,
    QTableWidgetItem, QDialog, QLabel, QHeaderView, QMessageBox, QApplication,
    QScrollArea, QGridLayout, QFrame
)
from PyQt5.QtCore import Qt, QUrl, QObject, pyqtSignal
from PyQt5.QtGui import (
    QFont, QColor, QPainter, QLinearGradient, QPixmap, QCursor, QBrush, QPainterPath, QDesktopServices
)
from thefuzz import process

# Import scraper 
try:
    from scrape_resep import scrape_cookpad
except ImportError:
    def scrape_cookpad():
        print("Error: scrape_resep.py tidak ditemukan.")

# ── Kamus konversi satuan → gram ──────────────────────────────────────────────
KONVERSI_GRAM = {
    'sdm': 15, 'sdt': 5, 'siung': 5, 'ekor': 80, 'genggam': 40,
    'pcs': 50, 'buah': 100, 'gram': 1, 'gr': 1, 'liter': 1000, 'ml': 1,
    'lembar': 3, 'ikat': 50, 'batang': 15
}

def hitung_nutrisi_bahan(teks_bahan, db_makanan_dict):
    match = re.search(r'([\d\./]+)\s*([a-zA-Z]+)\s*(.*)', teks_bahan)
    if not match:
        return None
    try:
        kuantitas_str = match.group(1).replace('/', '.0/') if '/' in match.group(1) else match.group(1)
        kuantitas = float(eval(kuantitas_str))
    except Exception:
        return None

    satuan    = match.group(2).lower()
    nama_bahan = match.group(3).strip()

    list_nama_db = list(db_makanan_dict.keys())
    kecocokan = process.extractOne(nama_bahan, list_nama_db)

    if kecocokan and kecocokan[1] >= 70:
        nama_db      = kecocokan[0]
        data_nutrisi = db_makanan_dict[nama_db]
        berat_total  = kuantitas * KONVERSI_GRAM.get(satuan, 50)
        return {
            'nama_asli': teks_bahan,
            'nama_db':   nama_db,
            'berat_g':   round(berat_total, 1),
            'kalori':    round((berat_total / 100) * float(data_nutrisi[2]), 1),
            'protein':   round((berat_total / 100) * float(data_nutrisi[3]), 1),
            'karbo':     round((berat_total / 100) * float(data_nutrisi[4]), 1),
            'lemak':     round((berat_total / 100) * float(data_nutrisi[5]), 1),
        }
    return None

class DetailResepDialog(QDialog):
    def __init__(self, resep, db_makanan_dict):
        super().__init__()
        self.setWindowTitle(f"Nutrisi: {resep.get('judul', 'Resep')}")
        self.resize(700, 500)
        self.resep = resep
        self.db_makanan_dict = db_makanan_dict
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        judul = QLabel(f"<b>{self.resep.get('judul', 'Tanpa Judul')}</b>")
        judul.setStyleSheet("font-size: 18px; margin-bottom: 5px; color: #1C1C1C; font-family: 'Montserrat';")
        layout.addWidget(judul)

        tabel = QTableWidget()
        tabel.setStyleSheet("font-family: 'Poppins'; font-size: 13px;")
        tabel.setColumnCount(6)
        tabel.setHorizontalHeaderLabels(
            ["Bahan Mentah", "Dikenali Sbg (DB)", "Berat (g)", "Kalori", "Protein", "Karbo"]
        )
        tabel.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(tabel)

        bahan_list = self.resep.get('bahan_detail', [])
        tabel.setRowCount(len(bahan_list))

        total_kal = total_pro = total_kar = total_lem = 0
        for row, teks in enumerate(bahan_list):
            tabel.setItem(row, 0, QTableWidgetItem(teks))
            hasil = hitung_nutrisi_bahan(teks, self.db_makanan_dict)
            if hasil:
                tabel.setItem(row, 1, QTableWidgetItem(hasil['nama_db']))
                tabel.setItem(row, 2, QTableWidgetItem(str(hasil['berat_g'])))
                tabel.setItem(row, 3, QTableWidgetItem(f"{hasil['kalori']} kcal"))
                tabel.setItem(row, 4, QTableWidgetItem(f"{hasil['protein']} g"))
                tabel.setItem(row, 5, QTableWidgetItem(f"{hasil['karbo']} g"))
                total_kal += hasil['kalori']
                total_pro += hasil['protein']
                total_kar += hasil['karbo']
                total_lem += hasil['lemak']
            else:
                tabel.setItem(row, 1, QTableWidgetItem("Tidak Dikenali"))
                for col in range(2, 6):
                    tabel.setItem(row, col, QTableWidgetItem("-"))

        ringkasan = QLabel(
            f"<div style='line-height: 1.5;'>"
            f"<b>Estimasi Total Nutrisi Resep:</b><br>"
            f"Kalori: {round(total_kal, 1)} kcal &nbsp;|&nbsp; "
            f"Protein: {round(total_pro, 1)} g &nbsp;|&nbsp; "
            f"Karbohidrat: {round(total_kar, 1)} g &nbsp;|&nbsp; "
            f"Lemak: {round(total_lem, 1)} g"
            f"</div>"
        )
        ringkasan.setStyleSheet("background-color: #E8F5E9; padding: 12px; border-radius: 8px; font-family: 'Poppins'; font-size: 14px; color: #1A7A34;")
        layout.addWidget(ringkasan)
        self.setLayout(layout)

# ─────────────────────────────────────────────
#  KOMPONEN KARTU RESEP & GRID
# ─────────────────────────────────────────────

def _bahan_singkat(komposisi: str, maks: int = 4) -> str:
    if not komposisi:
        return ''
    items = [b.strip() for b in komposisi.split('\u2022') if b.strip()]
    preview = items[:maks]
    result  = ' \u2022 '.join(preview)
    if len(items) > maks:
        result += f'  (+{len(items) - maks} lainnya)'
    return result

def _fix_url(url: str) -> str:
    if url.startswith('//'):
        return 'https:' + url
    return url

CARD_GRADIENTS = [
    ('#1A7A34', '#2E9E50'), ('#1E6E40', '#3AAA5E'), ('#176030', '#2B8B48'),
    ('#1B7530', '#36A050'), ('#1A6E38', '#329C54'), ('#156832', '#2C9848'),
    ('#197228', '#30A044'), ('#1C7A3A', '#34A858'), ('#157030', '#2A9C4C'),
]

class _ImageSignal(QObject):
    done = pyqtSignal(QPixmap)

def _download_image(url: str, signal: '_ImageSignal'):
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = resp.read()
        pix = QPixmap()
        pix.loadFromData(data)
        signal.done.emit(pix)
    except Exception as e:
        print(f'[WARN] Gagal unduh gambar ({url[:60]}): {e}')

class RecipeCard(QWidget):
    ASPECT_W = 4
    ASPECT_H = 3
    RADIUS   = 12
    MIN_W    = 140

    clicked = pyqtSignal(dict)

    def __init__(self, recipe: dict, grad_top: str, grad_bot: str, parent=None):
        super().__init__(parent)
        self._recipe = recipe
        self._name   = recipe.get('judul', '(Tanpa Judul)')
        self._desc   = _bahan_singkat(recipe.get('komposisi_singkat', ''))
        self._link   = _fix_url(recipe.get('link', ''))
        
        self._grad_top = QColor(grad_top)
        self._grad_bot = QColor(grad_bot)
        self._hovered  = False
        self._img_pix  = None

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(self.MIN_W, int(self.MIN_W * self.ASPECT_H / self.ASPECT_W))
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setMouseTracking(True)

        self._build_layout()

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        return int(w * self.ASPECT_H / self.ASPECT_W)

    def set_image(self, pixmap):
        if pixmap and not pixmap.isNull():
            self._img_pix = pixmap
            self.update()

    def _build_layout(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addStretch(1)

        text_area = QWidget()
        text_area.setStyleSheet('background: transparent;')
        tlay = QVBoxLayout(text_area)
        tlay.setContentsMargins(14, 6, 42, 12)
        tlay.setSpacing(4)

        self._name_lbl = QLabel(self._name)
        self._name_lbl.setStyleSheet("color: #FFFFFF; background: transparent; font-family: 'Montserrat'; font-size: 15px; font-weight: bold;")
        self._name_lbl.setWordWrap(True)

        self._desc_lbl = QLabel(self._desc)
        self._desc_lbl.setStyleSheet("color: rgba(255,255,255,0.88); background: transparent; font-family: 'Poppins'; font-size: 11px;")
        self._desc_lbl.setWordWrap(True)

        tlay.addWidget(self._name_lbl)
        tlay.addWidget(self._desc_lbl)
        outer.addWidget(text_area)

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
            QPushButton:hover { background: rgba(255,255,255,0.40); }
        """)
        self._link_btn.setCursor(QCursor(Qt.PointingHandCursor))
        if self._link:
            self._link_btn.clicked.connect(lambda _=False: QDesktopServices.openUrl(QUrl(self._link)))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        btn = self._link_btn
        btn.move(self.width() - btn.width() - 8, self.height() - btn.height() - 8)

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        self.clicked.emit(self._recipe)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        rect = self.rect()
        w, h = rect.width(), rect.height()

        clip = QPainterPath()
        clip.addRoundedRect(0, 0, w, h, self.RADIUS, self.RADIUS)
        painter.setClipPath(clip)

        if self._img_pix and not self._img_pix.isNull():
            self._draw_full_cover(painter, w, h)
        else:
            c_top = QColor(self._grad_top)
            c_bot = QColor(self._grad_bot)
            if self._hovered:
                c_top = c_top.lighter(115)
                c_bot = c_bot.lighter(115)
            bg = QLinearGradient(0, 0, 0, h)
            bg.setColorAt(0.0, c_top)
            bg.setColorAt(1.0, c_bot)
            painter.fillRect(rect, bg)
            self._draw_placeholder(painter, w, h)

        c_solid = QColor(self._grad_bot)
        if self._hovered: c_solid = c_solid.lighter(115)
        overlay = QLinearGradient(0, 0, 0, h)
        overlay.setColorAt(0.00, QColor(c_solid.red(), c_solid.green(), c_solid.blue(), 0))
        overlay.setColorAt(0.35, QColor(c_solid.red(), c_solid.green(), c_solid.blue(), 0))
        overlay.setColorAt(0.62, QColor(c_solid.red(), c_solid.green(), c_solid.blue(), 160))
        overlay.setColorAt(1.00, QColor(c_solid.red(), c_solid.green(), c_solid.blue(), 245))
        painter.fillRect(rect, overlay)
        painter.end()

    def _draw_full_cover(self, painter, w, h):
        pix = self._img_pix
        scaled = pix.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        src_x = max((scaled.width() - w) // 2, 0)
        src_y = max((scaled.height() - h) // 2, 0)
        crop = scaled.copy(src_x, src_y, min(w, scaled.width()), min(h, scaled.height()))
        painter.drawPixmap(0, 0, crop)

    def _draw_placeholder(self, painter, w, h):
        cx, cy = w // 2, int(h * 0.35)
        r = min(w, int(h * 0.55)) // 2 - 12
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 35)))
        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        painter.setBrush(QBrush(QColor(255, 255, 255, 20)))
        painter.drawEllipse(cx - r + 5, cy - r + 5, (r - 5) * 2, (r - 5) * 2)
        leaf_colors = [QColor(120, 220, 100, 180), QColor(80, 200, 80, 160), QColor(160, 230, 60, 170)]
        leaves = [(cx - 10, cy - 8, 22, 11, -30), (cx + 2, cy - 11, 20, 10, 20), (cx - 6, cy + 3, 18, 9, 10)]
        for i, (lx, ly, lw, lh, angle) in enumerate(leaves):
            painter.save()
            painter.translate(lx + lw // 2, ly + lh // 2)
            painter.rotate(angle)
            painter.setBrush(QBrush(leaf_colors[i % len(leaf_colors)]))
            painter.drawEllipse(-lw // 2, -lh // 2, lw, lh)
            painter.restore()

class RecipeGrid(QWidget):
    COLS = 3
    GAP  = 16

    # Signal yang akan diforward ke RekomendasiPage saat kartu di klik
    cardClicked = pyqtSignal(dict)

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
            row, col = divmod(idx, self.COLS)
            grad_top, grad_bot = CARD_GRADIENTS[idx % len(CARD_GRADIENTS)]

            card = RecipeCard(recipe, grad_top, grad_bot)
            card.clicked.connect(self.cardClicked.emit)
            layout.addWidget(card, row, col)

            url = _fix_url(recipe.get('gambar', ''))
            if url:
                self._start_download(url, card)

    @staticmethod
    def _start_download(url: str, card: 'RecipeCard'):
        sig = _ImageSignal()
        sig.done.connect(card.set_image)
        t = threading.Thread(target=_download_image, args=(url, sig), daemon=True)
        t.start()

# ─────────────────────────────────────────────
#  HALAMAN UTAMA REKOMENDASI PAGE
# ─────────────────────────────────────────────

class RekomendasiPage(QWidget):
    """Widget halaman Rekomendasi Resep — drop-in ke MainWindow._stack."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resep_data      = []
        self.db_makanan_dict = {}
        self.setStyleSheet("background-color: transparent;")
        
        self._muat_database()
        self._baca_json_lokal()
        self._init_ui()

    def _muat_database(self):
        try:
            base_dir = os.path.join(os.path.dirname(__file__), '..', 'bima_scrapper')
            db_path  = os.path.normpath(os.path.join(base_dir, 'nutrikost.db'))
            conn     = sqlite3.connect(db_path)
            cursor   = conn.cursor()
            cursor.execute("SELECT code, food_name, cal, protein, carb, fat FROM Makanan")
            self.db_makanan_dict = {row[1]: row for row in cursor.fetchall()}
            conn.close()
        except Exception as e:
            print(f"Gagal memuat database: {e}")

    def _baca_json_lokal(self):
        base_dir  = os.path.join(os.path.dirname(__file__), '..', 'bima_scrapper')
        json_path = os.path.normpath(os.path.join(base_dir, 'Resep.json'))
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                self.resep_data = json.load(f)

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        # Header Title
        title_layout = QHBoxLayout()
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        lbl_title = QLabel("Rekomendasi Resep")
        lbl_title.setStyleSheet("color: #1C1C1C; background: transparent; border: none; font-family: 'Montserrat Alternates'; font-size: 32px; font-weight: bold;")
        
        lbl_sub = QLabel("Temukan ide menu makan harian yang menyehatkan")
        lbl_sub.setStyleSheet("color: #6c757d; background: transparent; border: none; font-family: 'Montserrat'; font-size: 14px;")
        
        text_layout.addWidget(lbl_title)
        text_layout.addWidget(lbl_sub)
        
        title_layout.addLayout(text_layout)
        title_layout.addStretch()

        # Tombol Perbarui
        self.btn_scrape = QPushButton("Perbarui & Muat Resep")
        self.btn_scrape.setCursor(Qt.PointingHandCursor)
        self.btn_scrape.setStyleSheet("""
            QPushButton {
                background-color: #1A7A34;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-family: 'Montserrat';
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #155f28; }
            QPushButton:disabled { background-color: #A5D6A7; }
        """)
        self.btn_scrape.clicked.connect(self._proses_muat_data)
        title_layout.addWidget(self.btn_scrape, alignment=Qt.AlignBottom)

        root.addLayout(title_layout)
        
        # Area Scroll untuk Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._grid_container = QWidget()
        self._grid_container.setStyleSheet("background: transparent;")
        self._grid_layout = QVBoxLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        
        self._render_grid()

        scroll.setWidget(self._grid_container)
        root.addWidget(scroll, stretch=1)

    def _render_grid(self):
        # Clear lama
        for i in reversed(range(self._grid_layout.count())): 
            widget_to_remove = self._grid_layout.itemAt(i).widget()
            if widget_to_remove:
                self._grid_layout.removeWidget(widget_to_remove)
                widget_to_remove.deleteLater()

        if not self.resep_data:
            empty_lbl = QLabel("Resep belum tersedia atau masih memuat.\nSilakan tekan tombol 'Perbarui'.")
            empty_lbl.setAlignment(Qt.AlignCenter)
            empty_lbl.setStyleSheet("color: #888888; font-size: 14px; margin-top: 40px;")
            self._grid_layout.addWidget(empty_lbl)
            self._grid_layout.addStretch()
        else:
            grid = RecipeGrid(self.resep_data)
            grid.cardClicked.connect(self._buka_detail)
            self._grid_layout.addWidget(grid)

    def _proses_muat_data(self):
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.btn_scrape.setText("⏳ Sedang Mengambil Resep...")
            self.btn_scrape.setEnabled(False)
            QApplication.processEvents()

            scrape_cookpad()
            self._baca_json_lokal()
            self._render_grid()

            QMessageBox.information(
                self, "Selesai", f"Berhasil memuat {len(self.resep_data)} resep terbaru!"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Terjadi kesalahan saat memuat resep: {e}")
        finally:
            QApplication.restoreOverrideCursor()
            self.btn_scrape.setText("🔄 Perbarui & Muat Resep")
            self.btn_scrape.setEnabled(True)

    def _buka_detail(self, resep):
        # Saat card di klik, muncul kalkulasi gizi
        dialog = DetailResepDialog(resep, self.db_makanan_dict)
        dialog.exec_()