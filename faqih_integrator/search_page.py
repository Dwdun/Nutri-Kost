from __future__ import annotations
from typing import Callable, List

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QScrollArea, QFrame, QComboBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QDate, pyqtSignal
from PyQt5.QtGui import QFont

from models import DBHelper

# collor pallate
GREEN_PRIMARY = "#1A7A34"
GREEN_LIGHT   = "#CAEED4"
GRAY_BG       = "#f5f7f5"
GRAY_CARD     = "#ffffff"
GRAY_BORDER   = "#e0e0e0"
GRAY_TEXT     = "#6c757d"
RED_SOFT      = "#E03030"


#konfigurasi parameter chip filter makanan
FILTER_CHIPS = {
    "Semua":         ("",        0,    ""),
    "Protein Tinggi":("protein", 15.0, "gte"), #greater than or equal 
    "Karbo Tinggi":  ("carb",    40.0, "gte"), 
    "Lemak Rendah":  ("fat",     5.0,  "lte"), #less than or equal
    "Rendah Kalori": ("cal",     100.0,"lte"),
    "Sayur & Buah":  ("",        0,    ""),
    "Minuman":       ("",        0,    ""),
}

CHIP_NAME_KEYWORDS = {
    "Sayur & Buah": "sayur buah",
    "Minuman":      "minuman teh kopi susu jus air",
}

#konfigurasi fitur sorting berdasarkan makronutrien
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

#komponen filter button
class ChipButton(QPushButton):
    #tombol filter bentuknya kapsul (chip)
    def __init__(self, label: str, parent=None):
        super().__init__(label, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(30)
        self._apply_style(active=False)

    def set_active(self, active: bool):
        self._apply_style(active)

    #style UI
    def _apply_style(self, active: bool):
        #aktif = hijau
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
        #nonaktif = abu
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

#komponen foodcard di searching page
class FoodCard(QFrame):
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

        icon = QLabel("🍽️")
        icon.setFixedSize(46, 46)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"background-color: {GREEN_LIGHT}; border-radius: 8px; font-size: 22px;")
        layout.addWidget(icon)

        # Blok teks nama + ringkasan nutrisi
        info = QVBoxLayout()
        info.setSpacing(2)

        name = QLabel(self._data.get("food_name", "-"))
        name.setFont(QFont("Montserrat Alternates", 11, QFont.Bold))
        name.setStyleSheet("color: #1a1a1a;")
        info.addWidget(name)

        # status kalori dan nutrisi makronutrien per 100g
        nutrisi = QLabel(
            f"{self._data.get('cal', 0):.0f} kal  ·  "
            f"P {self._data.get('protein', 0):.1f}g  ·  "
            f"K {self._data.get('carb', 0):.1f}g  ·  "
            f"L {self._data.get('fat', 0):.1f}g"
        )
        nutrisi.setStyleSheet(f"color: {GRAY_TEXT}; font-size: 11px;")
        info.addWidget(nutrisi)
        layout.addLayout(info, 1)

        # Tombol pilih memicu log harian
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

#Page Utama Searching filtering dan sorting
class SearchPage(QWidget):
    PAGE_SIZE = 20
    def __init__(self, on_pilih_makanan: Callable[[dict], None] = None, parent=None):
        super().__init__(parent)
        self._callback    = on_pilih_makanan
        self._all_results = []   # cache hasil pencarian terakhir dari DB
        self._active_chip = "Semua"
        self._sort_key    = "cal"
        self._sort_desc   = False
        self._current_page   = 1      # lagi di halaman berapa sekarang
        self._total_pages    = 1      # total halaman yang ada di DB
        self._total_items    = 0      # total semua item di DB (misal 9800)
        self._is_search_mode = False  # True kalau user lagi ngetik keyword

        self._db = DBHelper()

        # QTimer sebagai debounce mencegah query ke DB setiap kali user mengetik satu huruf.
        # Timer di-reset tiap ada perubahan teks, query baru dijalankan setelah 400ms diam.
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(400)
        self._timer.timeout.connect(self._do_search)

        self._build_ui()
        self._do_search()   # load awal menampilkan semua makanan tanpa filter

    #UI page
    def _build_ui(self):
        self.setStyleSheet(f"background-color: {GRAY_BG};")
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # Baris 1: search bar + dropdown sort
        top = QHBoxLayout()
        top.setSpacing(10)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(" Cari nama makanan...")
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

        #dropdown sorting
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
            chip.clicked.connect(lambda _, l=label: self._on_chip_click(l))
            self._chips[label] = chip
            chip_row.addWidget(chip)
        chip_row.addStretch()
        self._chips["Semua"].set_active(True)
        root.addLayout(chip_row)

        # Baris 4: label status (jumlah hasil / pesan error)
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
        self._result_layout.setContentsMargins(0, 4, 14, 4)
        self._result_layout.setSpacing(8)

        # Stretch di akhir mendorong card ke atas, bukan terpusat di tengah
        self._result_layout.addStretch()

        scroll.setWidget(self._result_container)
        # Row baru di bawah scroll area
        pagination_row = QHBoxLayout()

        root.addWidget(scroll, stretch=1)

        self._pagination_label = QLabel("")   # "Menampilkan 20 dari 9800 makanan"
        pagination_row.addWidget(self._pagination_label)

        pagination_row.addStretch()

        self._load_more_btn = QPushButton("Muat 20 Lagi ↓")
        self._load_more_btn.clicked.connect(self._load_next_page)
        self._load_more_btn.hide()  # disembunyikan dulu sampai data dimuat
        pagination_row.addWidget(self._load_more_btn)

        root.addLayout(pagination_row)

    #kalo chip di klik , re filter data
    def _on_chip_click(self, label: str):
        self._active_chip = label
        for k, c in self._chips.items():
            c.set_active(k == label)
        # Tidak perlu query DB ulang — cukup filter dari _all_results
        self._render(self._filter_sort(self._all_results))

    #kalo opsi dropdown berubah , sorting ulang
    def _on_sort_changed(self, _index: int):
        self._sort_key, self._sort_desc = self._sort_combo.currentData()
        self._render(self._filter_sort(self._all_results))

    #searching makanan sesuai yang diinput berdasarkan dengan nama db
    def _do_search(self):
        query = self._search_input.text().strip()

        if query:
            # Mode search: ambil semua hasil keyword (jumlahnya kecil, aman)
            self._is_search_mode = True
            raw = self._db.search_makanan(query)
            self._all_results = raw
            self._total_items = len(raw)
            self._total_pages = 1
            self._current_page = 1
            self._update_pagination_ui(hide_btn=True)  # sembunyikan tombol Load More
            self._render(self._filter_sort(raw), append=False)
        else:
            # Mode browse: pakai pagination, ambil 20 dulu
            self._is_search_mode = False
            self._current_page = 1
            self._fetch_page(page=1, append=False)
    
    #sorting makanan sesuai kandungan makronutrien dan kalori
    def _filter_sort(self, data: List[dict]) -> List[dict]:
        field, threshold, operator = FILTER_CHIPS.get(self._active_chip, ("", 0, ""))

        #proses sesuai chip yang aktif
        if operator == "gte":
            data = [m for m in data if (m.get(field) or 0) >= threshold]
        elif operator == "lte":
            data = [m for m in data if (m.get(field) or 0) <= threshold]
        elif self._active_chip in CHIP_NAME_KEYWORDS:
            kws = CHIP_NAME_KEYWORDS[self._active_chip].lower().split()
            data = [m for m in data if any(k in m.get("food_name", "").lower() for k in kws)]

        #sorted sesuai pilihan 
        return sorted(data, key=lambda m: m.get(self._sort_key, 0) or 0, reverse=self._sort_desc)

    def _render(self, results: List[dict], append: bool = False):
        if not append:
            # reset foodcard
            while self._result_layout.count() > 1:
                item = self._result_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            #validasi nama makanan jika tidak ada
        if not results and not append:
            self._show_empty_state()
            self._status.setText(" Makanan tidak ditemukan.")
            self._status.setStyleSheet(f"color: {RED_SOFT}; font-size: 12px;")
            return

        # Update label status
        q     = self._search_input.text().strip()
        chip  = self._active_chip
        info  = f"{len(results)} makanan ditemukan"
        if q:              info += f" untuk \"{q}\""
        if chip != "Semua": info += f" · filter: {chip}"
        self._status.setText(info)
        self._status.setStyleSheet(f"color: {GRAY_TEXT}; font-size: 12px;")

        #render list ke foodcard per baris makanan
        for mkn in results:
            card = FoodCard(mkn)
            card.clicked.connect(self._on_card_click)
            # insertWidget(count-1) = sisipkan sebelum stretch agar card tetap di atas
            self._result_layout.insertWidget(self._result_layout.count() - 1, card)

    #searching gagal
    def _show_empty_state(self):
        empty = QLabel("\n\nMakanan tidak ditemukan.\nCoba kata kunci lain atau ubah filter.")
        empty.setAlignment(Qt.AlignCenter)
        empty.setStyleSheet(f"color: {GRAY_TEXT}; font-size: 13px; padding: 40px;")
        self._result_layout.insertWidget(0, empty)

    #kalo foodcard di klik akan trigger tambah makanan 
    def _on_card_click(self, makanan: dict):
        print(f"[SearchPage] Dipilih: {makanan.get('food_name')}")
        if self._callback:
            self._callback(makanan)

    def _fetch_page(self, page: int, append: bool):
        hasil = self._db.get_all_makanan_paginated(page=page, per_page=self.PAGE_SIZE)

        new_data   = hasil["data"]
        pagination = hasil["pagination"]

        self._total_items = pagination["total_items"]
        self._total_pages = pagination["total_pages"]

        if append:
            self._all_results.extend(new_data)   # tambahkan ke cache
            self._render(self._filter_sort(new_data), append=True)
        else:
            self._all_results = new_data          # reset cache
            self._render(self._filter_sort(new_data), append=False)

        self._update_pagination_ui(hide_btn=False)

    def _load_next_page(self):
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._fetch_page(page=self._current_page, append=True)

    def _update_pagination_ui(self, hide_btn: bool = False):
        if hide_btn or self._is_search_mode:
            self._load_more_btn.hide()
            self._pagination_label.setText("")
            return

        shown = len(self._all_results)
        total = self._total_items
        self._pagination_label.setText(f"Menampilkan {shown} dari {total} makanan")

        if self._current_page >= self._total_pages:
            self._load_more_btn.setEnabled(False)
            self._load_more_btn.setText("Semua data sudah dimuat ✓")
            self._load_more_btn.show()
        else:
            self._load_more_btn.setEnabled(True)
            remaining = self._total_items - len(self._all_results)
            self._load_more_btn.setText(f"Muat 20 Lagi ↓  (sisa ±{remaining})")
            self._load_more_btn.show()

