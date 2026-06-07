from __future__ import annotations
from typing import Callable, List

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QScrollArea, QFrame, QComboBox, QSizePolicy, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, QDate, pyqtSignal, QPoint, QRect, QSize, QThread
from PyQt5.QtGui import QFont, QCursor, QPainter, QColor, QPen

import sys
import os

try:
    from bima_scrapper.models import DBHelper
except ModuleNotFoundError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from bima_scrapper.models import DBHelper

# collor pallate matching template_halaman.py
GREEN_PRIMARY = "#1A7A34"
GREEN_LIGHT   = "#E8F5E9"
GRAY_BG       = "transparent"
GRAY_CARD     = "#ffffff"
GRAY_BORDER   = "#e2e8e4"
GRAY_TEXT     = "#6c757d"
RED_SOFT      = "#E03030"
C_TEXT_DARK   = "#1C1C1C"

#konfigurasi parameter chip filter makanan
FILTER_CHIPS = {
    "Semua":         ("",        0,    ""),
    "Protein Tinggi":("protein", 15.0, "gte"), #greater than or equal 
    "Karbo Tinggi":  ("carb",    40.0, "gte"), 
    "Lemak Rendah":  ("fat",     5.0,  "lte"), #less than or equal
    "Rendah Kalori": ("cal",     100.0,"lte"),
    "Sayur dan Buah":("",        0,    ""),
    "Minuman":       ("",        0,    ""),
}

CHIP_NAME_KEYWORDS = {
    "Sayur dan Buah": "sayur buah",
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
        self.setFixedHeight(34)
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
                    border: 1px solid {GREEN_PRIMARY};
                    border-radius: 17px;
                    padding: 0 16px;
                    font-weight: 600;
                    font-size: 12px;
                }}
            """)
        #nonaktif = abu
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: white;
                    color: #555555;
                    border: 1px solid {GRAY_BORDER};
                    border-radius: 17px;
                    padding: 0 16px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    border-color: {GREEN_PRIMARY};
                    color: {GREEN_PRIMARY};
                    background-color: #fcfcfc;
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
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            FoodCard {{
                background-color: {GRAY_CARD};
                border: 1px solid rgba(0,0,0,0.06);
                border-radius: 12px;
            }}
            FoodCard:hover {{
                border: 1.5px solid {GREEN_PRIMARY};
                background-color: {GREEN_LIGHT};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Name
        name = QLabel(self._data.get("food_name", "-"))
        name.setFont(QFont("Poppins", 13))
        name.setStyleSheet(f"color: {C_TEXT_DARK}; border: none; background: transparent; font-family: 'Poppins'; font-size: 15px;")
        name.setWordWrap(True)
        layout.addWidget(name)

        # Kalori per 100g
        cal_label = QLabel(f"{self._data.get('cal', 0):.0f} kal per 100 gram")
        cal_label.setStyleSheet("color: #888888; font-size: 11px; font-family: 'Poppins'; border: none; background: transparent;")
        layout.addWidget(cal_label)

        # Macros container
        macros_layout = QHBoxLayout()
        macros_layout.setSpacing(8)

        def make_macro_lbl(title, val, color):
            lbl = QLabel(f"{title}: {val:.1f}g")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"background-color: {color}; color: white; border-radius: 6px; padding: 4px 8px; font-size: 10px; font-family: 'Poppins'; font-weight: normal; border: none;")
            return lbl

        macros_layout.addWidget(make_macro_lbl("Protein", self._data.get('protein', 0), "#1A7A34")) # Green
        macros_layout.addWidget(make_macro_lbl("Karbohidrat", self._data.get('carb', 0), "#2B73B6")) # Blue
        macros_layout.addWidget(make_macro_lbl("Lemak", self._data.get('fat', 0), "#E29E21")) # Yellow
        macros_layout.addStretch()

        layout.addLayout(macros_layout)

    def mousePressEvent(self, _event):
        # Klik di mana saja pada card memicu signal
        self.clicked.emit(self._data)

#komponen loading spinner
class LoadingSpinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(50)  # rotate setiap 50ms
        self.setFixedSize(50, 50)

    def rotate(self):
        self.angle = (self.angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        painter.translate(width / 2, height / 2)
        painter.rotate(self.angle)
        
        pen = QPen()
        pen.setWidth(4)
        pen.setCapStyle(Qt.RoundCap)
        
        color = QColor(GREEN_PRIMARY)
        for i in range(8):
            color.setAlphaF((i + 1) / 8.0)
            pen.setColor(color)
            painter.setPen(pen)
            painter.drawLine(0, -15, 0, -8)
            painter.rotate(45)

# Worker thread untuk query database di background
class DbWorker(QThread):
    finished = pyqtSignal(dict, bool, str)

    def __init__(self, db_helper, query=None, page=None, per_page=None):
        super().__init__()
        self.db = db_helper
        self.query = query
        self.page = page
        self.per_page = per_page

    def run(self):
        try:
            if self.query is not None:
                raw = self.db.search_makanan(self.query)
                self.finished.emit({"data": raw}, True, "")
            else:
                hasil = self.db.get_all_makanan_paginated(page=self.page, per_page=self.per_page)
                self.finished.emit(hasil, False, "")
        except Exception as e:
            self.finished.emit({}, self.query is not None, str(e))

#Page Utama Searching filtering dan sorting
class SearchPage(QWidget):
    PER_PAGE = 20
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
        self._is_searching = False  # True kalau sedang menampilkan hasil search
        self._worker       = None   # worker thread untuk background search

        self._db = DBHelper()


        self._build_ui()
        self._do_search()   # load awal menampilkan semua makanan tanpa filter

    #UI page
    def _build_ui(self):
        self.setStyleSheet(f"background-color: {GRAY_BG};")
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        # ── Judul halaman ─────────────────────────────────────────────────────
        lbl_title = QLabel("Cari Makanan")
        lbl_title.setFont(QFont("Montserrat Alternates", 32, QFont.Bold))
        lbl_title.setStyleSheet(f"color: {C_TEXT_DARK}; background: transparent; border: none; font-family: 'Montserrat Alternates'; font-size: 32px; font-weight: bold;")

        lbl_sub = QLabel("Temukan informasi nilai gizi dari berbagai makanan")
        lbl_sub.setFont(QFont("Montserrat", 10))
        lbl_sub.setStyleSheet(f"color: {GRAY_TEXT}; background: transparent; border: none; font-family: 'Montserrat'; font-size: 14px;")

        root.addWidget(lbl_title)
        root.addWidget(lbl_sub)

        # Baris 1: search bar + dropdown sort
        top = QHBoxLayout()
        top.setSpacing(12)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("  Cari nama makanan...")
        self._search_input.setFixedHeight(44)
        self._search_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {GRAY_BORDER};
                border-radius: 12px;
                padding: 0 16px;
                background: white;
                font-size: 13px;
                color: {C_TEXT_DARK};
            }}
            QLineEdit:focus {{ border: 1.5px solid {GREEN_PRIMARY}; }}
        """)

        # Jalankan pencarian saat menekan enter
        self._search_input.returnPressed.connect(self._do_search)
        top.addWidget(self._search_input, stretch=1)

        self._search_btn = QPushButton("Cari")
        self._search_btn.setFixedHeight(44)
        self._search_btn.setCursor(Qt.PointingHandCursor)
        self._search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {GREEN_PRIMARY};
                color: white;
                border: none;
                border-radius: 12px;
                padding: 0 20px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: #155f28; }}
        """)
        self._search_btn.clicked.connect(self._do_search)
        top.addWidget(self._search_btn)

        sort_lbl = QLabel("Urutkan:")
        sort_lbl.setStyleSheet(f"color: {GRAY_TEXT}; font-size: 13px;")
        top.addWidget(sort_lbl)

        #dropdown sorting
        self._sort_combo = QComboBox()
        self._sort_combo.setFixedHeight(44)
        self._sort_combo.setMinimumWidth(140)
        self._sort_combo.setCursor(Qt.PointingHandCursor)
        self._sort_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {GRAY_BORDER};
                border-radius: 12px;
                padding: 0 16px;
                background: white;
                font-size: 13px;
                color: {C_TEXT_DARK};
            }}
            QComboBox:focus {{ border: 1.5px solid {GREEN_PRIMARY}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox::down-arrow {{ image: none; }} /* bisa diganti dgn icon panah */
        """)

        for label, key, desc in SORT_OPTIONS:
            self._sort_combo.addItem(label, (key, desc))
        self._sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        top.addWidget(self._sort_combo)
        root.addLayout(top)

        # Baris 2: filter chip di bawah search bar
        chip_row = QHBoxLayout()
        chip_row.setSpacing(10)
        self._chips: dict[str, ChipButton] = {}
        for label in FILTER_CHIPS:
            chip = ChipButton(label)
            chip.clicked.connect(lambda _, l=label: self._on_chip_click(l))
            self._chips[label] = chip
            chip_row.addWidget(chip)
        chip_row.addStretch()
        self._chips["Semua"].set_active(True)
        root.addLayout(chip_row)

        # Baris 3: label status (jumlah hasil / pesan error)
        self._status = QLabel("Memuat data...")
        self._status.setStyleSheet(f"color: {GRAY_TEXT}; font-size: 12px; margin-top: 4px;")
        root.addWidget(self._status)

        # Area scroll untuk daftar FoodCard
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._result_container = QWidget()
        self._result_container.setStyleSheet("background: transparent;")
        self._result_layout = QGridLayout(self._result_container)
        self._result_layout.setContentsMargins(0, 4, 16, 4)
        self._result_layout.setSpacing(16)
        self._result_layout.setAlignment(Qt.AlignTop)
        self._result_layout.setColumnStretch(0, 1)
        self._result_layout.setColumnStretch(1, 1)
        self._result_layout.setColumnStretch(2, 1)

        scroll.setWidget(self._result_container)
        root.addWidget(scroll, stretch=1)

        # Row pagination di paling bawah (tombol prev dan next)
        pagination_row = QHBoxLayout()
        pagination_row.setContentsMargins(0, 12, 0, 0)
        
        pagination_row.addStretch()

        self._pagination_label = QLabel("")
        self._pagination_label.setStyleSheet(f"color: {GRAY_TEXT}; font-size: 12px;")
        pagination_row.addWidget(self._pagination_label)

        pagination_row.addStretch()

        self._prev_btn = QPushButton("← Prev")
        self._prev_btn.setFixedHeight(38)
        self._prev_btn.setCursor(Qt.PointingHandCursor)
        self._prev_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                color: {GREEN_PRIMARY};
                border: 1px solid {GREEN_PRIMARY};
                border-radius: 8px;
                padding: 0 16px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {GREEN_LIGHT}; }}
            QPushButton:disabled {{
                color: {GRAY_TEXT};
                border-color: {GRAY_BORDER};
            }}
        """)
        self._prev_btn.clicked.connect(lambda: self._go_to_page(self._current_page - 1))
        self._prev_btn.hide()
        pagination_row.addWidget(self._prev_btn)

        self._page_label = QLabel("")
        self._page_label.setAlignment(Qt.AlignCenter)
        self._page_label.setFixedWidth(100)
        self._page_label.setStyleSheet(f"color: {C_TEXT_DARK}; font-size: 13px; font-weight: bold;")
        self._page_label.hide()
        pagination_row.addWidget(self._page_label)

        self._next_btn = QPushButton("Next →")
        self._next_btn.setFixedHeight(38)
        self._next_btn.setCursor(Qt.PointingHandCursor)
        self._next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {GREEN_PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 16px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: #155f28; }}
            QPushButton:disabled {{
                background-color: {GRAY_BORDER};
                color: white;
            }}
        """)
        self._next_btn.clicked.connect(lambda: self._go_to_page(self._current_page + 1))
        self._next_btn.hide()   
        pagination_row.addWidget(self._next_btn)

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

    def _cancel_active_worker(self):
        if self._worker is not None:
            try:
                self._worker.finished.disconnect()
            except TypeError:
                pass
            self._worker = None

    def _show_loading(self):
        while self._result_layout.count():
            item = self._result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._status.setText(" Sedang mencari data...")
        self._status.setStyleSheet(f"color: {GRAY_TEXT}; font-size: 13px;")

        self._loading_widget = QWidget()
        layout = QVBoxLayout(self._loading_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 80, 0, 80)
        
        spinner = LoadingSpinner()
        layout.addWidget(spinner, alignment=Qt.AlignCenter)
        
        lbl = QLabel("Sedang mencari data...")
        lbl.setFont(QFont("Poppins", 13))
        lbl.setStyleSheet(f"color: {GREEN_PRIMARY}; font-weight: 500; margin-top: 12px; background: transparent; border: none;")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl, alignment=Qt.AlignCenter)
        
        self._result_layout.addWidget(self._loading_widget, 0, 0, 1, 3)

    #searching makanan sesuai yang diinput berdasarkan dengan nama db
    def _do_search(self):
        self._cancel_active_worker()
        query = self._search_input.text().strip()

        if query:
            self._is_searching = True
            self._show_loading()
            self._worker = DbWorker(self._db, query=query)
            self._worker.finished.connect(self._on_search_finished)
            self._worker.start()
        else:
            self._is_searching = False
            self._current_page = 1
            self._fetch_page(page=1)

    def _on_search_finished(self, result: dict, is_search: bool, error_msg: str):
        self._worker = None
        if error_msg:
            print(f"[SearchPage] DB search error: {error_msg}")
            raw = []
        else:
            raw = result.get("data", [])
            
        self._all_results = raw
        self._update_pagination_ui()
        self._render(self._filter_sort(raw))

    def _filter_sort(self, data: List[dict]) -> List[dict]:
        field, threshold, operator = FILTER_CHIPS.get(self._active_chip, ("", 0, ""))

        if operator == "gte":
            data = [m for m in data if (m.get(field) or 0) >= threshold]
        elif operator == "lte":
            data = [m for m in data if (m.get(field) or 0) <= threshold]
        elif self._active_chip in CHIP_NAME_KEYWORDS:
            kws = CHIP_NAME_KEYWORDS[self._active_chip].lower().split()
            data = [m for m in data if any(k in m.get("food_name", "").lower() for k in kws)]

        return sorted(data, key=lambda m: m.get(self._sort_key, 0) or 0, reverse=self._sort_desc)

    def _render(self, results: List[dict]):
        while self._result_layout.count():
            item = self._result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not results:
            self._show_empty_state()
            self._status.setText(" Makanan tidak ditemukan.")
            self._status.setStyleSheet(f"color: {RED_SOFT}; font-size: 13px;")
            return

        q    = self._search_input.text().strip()
        chip = self._active_chip

        if self._is_searching:
            info = f"{len(results)} makanan ditemukan untuk \"{q}\""
        else:
            info = f"Halaman {self._current_page} dari {self._total_pages}  ·  {self._total_items} makanan"

        if chip != "Semua":
            info += f"  ·  filter: {chip}"

        self._status.setText(info)
        self._status.setStyleSheet(f"color: {GRAY_TEXT}; font-size: 13px;")

        row = 0
        col = 0
        for mkn in results:
            card = FoodCard(mkn)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            card.clicked.connect(self._on_card_click)
            self._result_layout.addWidget(card, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

    def _show_empty_state(self):
        empty = QLabel("\n\nMakanan tidak ditemukan.\nCoba kata kunci lain atau ubah filter.")
        empty.setAlignment(Qt.AlignCenter)
        empty.setStyleSheet(f"color: {GRAY_TEXT}; font-size: 14px; padding: 40px;")
        self._result_layout.addWidget(empty, 0, 0, 1, 3)

    def _on_card_click(self, makanan: dict):
        print(f"[SearchPage] Dipilih: {makanan.get('food_name')}")
        if self._callback:
            self._callback(makanan)

    def _fetch_page(self, page: int):
        self._cancel_active_worker()
        self._show_loading()
        self._worker = DbWorker(self._db, page=page, per_page=self.PER_PAGE)
        self._worker.finished.connect(self._on_fetch_finished)
        self._worker.start()

    def _on_fetch_finished(self, result: dict, is_search: bool, error_msg: str):
        self._worker = None
        if error_msg or not result:
            print(f"[SearchPage] DB pagination error: {error_msg}")
            new_data = []
            pagination = {"total_items": 0, "total_pages": 1}
        else:
            new_data = result.get("data", [])
            pagination = result.get("pagination", {"total_items": 0, "total_pages": 1})

        self._total_items = pagination["total_items"]
        self._total_pages = pagination["total_pages"]

        self._all_results = new_data
        self._render(self._filter_sort(new_data))
        self._update_pagination_ui()

    def _go_to_page(self, page: int):
        if page < 1 or page > self._total_pages:
            return
        self._current_page = page
        self._fetch_page(page)

    def _update_pagination_ui(self):
        if self._is_searching:
            self._prev_btn.hide()
            self._next_btn.hide()
            self._page_label.hide()
            self._pagination_label.setText("")
            return

        self._pagination_label.setText(f"Menampilkan {len(self._all_results)} dari {self._total_items} makanan")

        self._page_label.setText(f"{self._current_page} / {self._total_pages}")
        self._page_label.show()

        self._prev_btn.setEnabled(self._current_page > 1)
        self._prev_btn.show()

        self._next_btn.setEnabled(self._current_page < self._total_pages)
        self._next_btn.show()

