from __future__ import annotations
from typing import Callable, List

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QScrollArea, QFrame, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFonta

# models.py sudah di-inject ke sys.path oleh main.py, jadi import langsung
try:
    from models import DBHelper
    _DB_AVAILABLE = True
except ImportError:
    # Halaman tetap jalan dengan data dummy — berguna saat develop tanpa DB Bima
    _DB_AVAILABLE = False
    print("[SearchPage] WARNING: models.py tidak ditemukan, pakai dummy data.")

# ── Palet warna ───────────────────────────────────────────────────────────────
GREEN_PRIMARY = "#1A7A34"
GREEN_LIGHT   = "#EAF5EE"
GRAY_BG       = "#f5f7f5"
GRAY_CARD     = "#ffffff"
GRAY_BORDER   = "#e0e0e0"
GRAY_TEXT     = "#6c757d"
RED_SOFT      = "#dc3545"


# ── Konfigurasi Filter Chip ───────────────────────────────────────────────────
# Format: label yang tampil → keyword pencarian (string kosong = tampilkan semua)
# Untuk satu kategori yang punya banyak sinonim, pisahkan dengan spasi.
# Contoh: "Protein" → cari makanan yang namanya mengandung salah satu dari kata-kata ini.
FILTER_CHIPS = {
    "Semua":          {"type": "semua"},
    "Protein Tinggi": {"type": "nutrisi", "key": "protein", "min": 15.0},
    "Karbo Tinggi":   {"type": "nutrisi", "key": "carb",    "min": 38.0},
    "Lemak Rendah":   {"type": "nutrisi", "key": "fat",     "max": 2.0},
    "Rendah Kalori":  {"type": "nutrisi", "key": "cal",     "max": 100.0},
    "Sayur & Buah":   {"type": "nama",    "keywords": ["sayur", "buah", "wortel", "bayam",
                                                        "kangkung", "tomat", "jagung",
                                                        "pisang", "jeruk", "mangga", "apel"]},
    "Minuman":        {"type": "nama",    "keywords": ["teh", "kopi", "susu", "jus",
                                                        "air", "minuman", "sirup", "soda"]},
}

# ── Konfigurasi Sorting ───────────────────────────────────────────────────────
# (label tampilan, key dict makanan, apakah descending?)
# Key harus sesuai dengan nama kolom yang dikembalikan DBHelper: cal, protein, carb, fat
SORT_OPTIONS = [
    ("Kalori ↑",  "cal",     False),   # terendah dulu
    ("Kalori ↓",  "cal",     True),    # tertinggi dulu
    ("Protein ↑", "protein", False),
    ("Protein ↓", "protein", True),
    ("Karbo ↑",   "carb",    False),
    ("Karbo ↓",   "carb",    True),
    ("Lemak ↑",   "fat",     False),
    ("Lemak ↓",   "fat",     True),
]

# ── Komponen: Chip Filter ─────────────────────────────────────────────────────

class ChipButton(QPushButton):
    """
    Tombol kecil berbentuk pil untuk filter kategori makanan.

    Mirip tag/badge yang bisa diklik — satu chip aktif pada satu waktu.
    Tampilan berubah (hijau/putih) mengikuti state aktif/tidak.
    """

    def __init__(self, label: str, parent=None):
        super().__init__(label, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(30)
        self._apply_style(active=False)

    def set_active(self, active: bool):
        self._apply_style(active)

    def _apply_style(self, active: bool):
        if active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {GREEN_PRIMARY};
                    color: white;
                    border: 1.5px solid {GREEN_PRIMARY};
                    border-radius: 15px;
                    padding: 0 14px;
                    font-weight: bold;
                    font-size: 12px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: white;
                    color: #444;
                    border: 1.5px solid {GRAY_BORDER};
                    border-radius: 15px;
                    padding: 0 14px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    border-color: {GREEN_PRIMARY};
                    color: {GREEN_PRIMARY};
                }}
            """)


# ── Komponen: Card Makanan ────────────────────────────────────────────────────

class FoodCard(QFrame):
    """
    Card yang merepresentasikan satu item makanan di hasil pencarian.

    Menampilkan: ikon · nama · ringkasan nutrisi (kal, protein, karbo, lemak)
    User bisa klik card atau tombol '+ Pilih' — keduanya emit signal clicked(dict).

    Signal clicked membawa dict makanan lengkap ke SearchPage,
    lalu diteruskan ke MainWindow dan akhirnya ke LogPage (Irfan).
    """

    # Signal ini membawa data makanan (dict) saat card diklik
    clicked = pyqtSignal(dict)

    def __init__(self, makanan: dict, parent=None):
        super().__init__(parent)
        self._data = makanan
        self._build()

    def _build(self):
        self.setFixedHeight(80)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            FoodCard {{
                background-color: {GRAY_CARD};
                border: 1px solid {GRAY_BORDER};
                border-radius: 10px;
            }}
            FoodCard:hover {{
                border: 1.5px solid {GREEN_PRIMARY};
                background-color: {GREEN_LIGHT};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(14)

        # Ikon makanan — sementara pakai emoji, bisa diganti gambar asli nanti
        icon = QLabel("🍽️")
        icon.setFixedSize(46, 46)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"background-color: {GREEN_LIGHT}; border-radius: 8px; font-size: 22px;")
        layout.addWidget(icon)

        # Blok teks: nama + ringkasan nutrisi
        info = QVBoxLayout()
        info.setSpacing(2)

        name = QLabel(self._data.get("food_name", "-"))
        name.setFont(QFont("Segoe UI", 11, QFont.Bold))
        name.setStyleSheet("color: #1a1a1a;")
        info.addWidget(name)

        # Nilai nutrisi semua per 100g — sesuai standar DBHelper Bima
        nutrisi = QLabel(
            f"{self._data.get('cal', 0):.0f} kal  ·  "
            f"P {self._data.get('protein', 0):.1f}g  ·  "
            f"K {self._data.get('carb', 0):.1f}g  ·  "
            f"L {self._data.get('fat', 0):.1f}g"
        )
        nutrisi.setStyleSheet(f"color: {GRAY_TEXT}; font-size: 11px;")
        info.addWidget(nutrisi)
        layout.addLayout(info, stretch=1)

        # Tombol pilih — klik ini yang memicu alur ke Log Harian
        btn = QPushButton("+ Pilih")
        btn.setFixedSize(72, 32)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {GREEN_PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #155f28; }}
        """)
        # emit signal dengan data makanan lengkap
        btn.clicked.connect(lambda: self.clicked.emit(self._data))
        layout.addWidget(btn)

    def mousePressEvent(self, _event):
        # Klik di mana saja pada card juga trigger signal yang sama
        self.clicked.emit(self._data)


# ── Halaman Utama ─────────────────────────────────────────────────────────────

class SearchPage(QWidget):
    """
    Halaman pencarian makanan utama.

    Alur data:
        User ketik → debounce 400ms → _do_search() → DB / dummy
            → _all_results disimpan
            → _filter_sort() terapkan chip + sort
            → _render() tampilkan FoodCard

    Parameter:
        on_pilih_makanan: Callable[[dict], None]
            Fungsi yang dipanggil saat user memilih makanan.
            Diisi oleh MainWindow saat SearchPage dibuat.
    """

    def __init__(self, on_pilih_makanan: Callable[[dict], None] = None, parent=None):
        super().__init__(parent)
        self._callback    = on_pilih_makanan
        self._all_results: List[dict] = []   # cache hasil pencarian terakhir dari DB
        self._active_chip = "Semua"
        self._sort_key    = "cal"
        self._sort_desc   = False

        self._db = DBHelper() if _DB_AVAILABLE else None

        # QTimer sebagai debounce: cegah query ke DB setiap kali user mengetik satu huruf.
        # Timer di-reset tiap ada perubahan teks; query baru dijalankan setelah 400ms diam.
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(400)
        self._timer.timeout.connect(self._do_search)

        self._build_ui()
        self._do_search()   # load awal: tampilkan semua makanan tanpa filter

    # ── Membangun Tampilan ────────────────────────────────────────────────────

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {GRAY_BG};")
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # Baris 1: search bar + dropdown sort
        top = QHBoxLayout()
        top.setSpacing(10)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍  Cari nama makanan...")
        self._search_input.setFixedHeight(40)
        self._search_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid {GRAY_BORDER};
                border-radius: 8px;
                padding: 0 14px;
                background: white;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {GREEN_PRIMARY}; }}
        """)
        # Setiap perubahan teks me-restart timer debounce
        self._search_input.textChanged.connect(lambda _: self._timer.start())
        top.addWidget(self._search_input, stretch=1)

        sort_lbl = QLabel("Urutkan:")
        sort_lbl.setStyleSheet(f"color: {GRAY_TEXT}; font-size: 12px;")
        top.addWidget(sort_lbl)

        self._sort_combo = QComboBox()
        self._sort_combo.setFixedHeight(40)
        self._sort_combo.setMinimumWidth(130)
        self._sort_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1.5px solid {GRAY_BORDER};
                border-radius: 8px;
                padding: 0 10px;
                background: white;
                font-size: 12px;
            }}
            QComboBox:focus {{ border-color: {GREEN_PRIMARY}; }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
        """)
        # Simpan (key, desc) sebagai data item — diambil kembali saat sort berubah
        for label, key, desc in SORT_OPTIONS:
            self._sort_combo.addItem(label, (key, desc))
        self._sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        top.addWidget(self._sort_combo)
        root.addLayout(top)

        # Baris 2: filter chip
        chip_row = QHBoxLayout()
        chip_row.setSpacing(8)
        self._chips: dict[str, ChipButton] = {}
        for label in FILTER_CHIPS:
            chip = ChipButton(label)
            # default arg l=label penting agar setiap lambda capture nilai yang benar
            chip.clicked.connect(lambda _, l=label: self._on_chip_click(l))
            self._chips[label] = chip
            chip_row.addWidget(chip)
        chip_row.addStretch()
        self._chips["Semua"].set_active(True)
        root.addLayout(chip_row)

        # Baris 3: label status (jumlah hasil / pesan error)
        self._status = QLabel("Memuat data...")
        self._status.setStyleSheet(f"color: {GRAY_TEXT}; font-size: 12px;")
        root.addWidget(self._status)

        # Area scroll untuk daftar FoodCard
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._result_container = QWidget()
        self._result_container.setStyleSheet("background: transparent;")
        self._result_layout = QVBoxLayout(self._result_container)
        self._result_layout.setContentsMargins(0, 4, 0, 4)
        self._result_layout.setSpacing(8)
        # Stretch di akhir mendorong card ke atas, bukan terpusat di tengah
        self._result_layout.addStretch()

        scroll.setWidget(self._result_container)
        root.addWidget(scroll, stretch=1)

    # ── Event Handler ─────────────────────────────────────────────────────────

    def _on_chip_click(self, label: str):
        """Ganti chip aktif lalu re-filter data yang sudah ada di cache."""
        self._active_chip = label
        for k, c in self._chips.items():
            c.set_active(k == label)
        # Tidak perlu query DB ulang — cukup filter dari _all_results
        self._render(self._filter_sort(self._all_results))

    def _on_sort_changed(self, _index: int):
        """Ambil (key, desc) dari item combo yang dipilih lalu re-sort."""
        self._sort_key, self._sort_desc = self._sort_combo.currentData()
        self._render(self._filter_sort(self._all_results))