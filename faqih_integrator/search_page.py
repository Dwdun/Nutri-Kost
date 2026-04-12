from __future__ import annotations
from typing import Callable, List

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QScrollArea, QFrame, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, QDate, pyqtSignal
from PyQt5.QtGui import QFont

from models import DBHelper

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

LOG_WAKTU_OPTIONS = [
    ("Semua Waktu",  None),
    ("Sarapan",      "Sarapan"),
    ("Makan Siang",  "Makan Siang"),
    ("Makan Malam",  "Makan Malam"),
    ("Snack",        "Snack"),
    ("Minuman",      "Minuman"),
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
        self._all_logs:    List[dict] = []   # cache log harian untuk filter waktu
        self._active_chip = "Semua"
        self._sort_key    = "cal"
        self._sort_desc   = False
        self._active_waktu: str | None = None  # None = semua waktu, str = category log

        import os
        print("DB path:", os.path.join(os.path.dirname(os.path.abspath(__file__)), "nutrikost.db"))
        self._db = DBHelper()

        # QTimer sebagai debounce: cegah query ke DB setiap kali user mengetik satu huruf.
        # Timer di-reset tiap ada perubahan teks; query baru dijalankan setelah 400ms diam.
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(400)
        self._timer.timeout.connect(self._do_search)

        self._build_ui()
        self._do_search()   # load awal: tampilkan semua makanan tanpa filter
        self._load_logs()   # load awal: ambil semua log harian ke cache
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

        # Baris 3: filter log berdasarkan waktu makan
        log_row = QHBoxLayout()
        log_row.setSpacing(8)

        log_lbl = QLabel("Filter Log:")
        log_lbl.setStyleSheet(f"color: {GRAY_TEXT}; font-size: 12px;")
        log_row.addWidget(log_lbl)

        self._waktu_combo = QComboBox()
        self._waktu_combo.setFixedHeight(32)
        self._waktu_combo.setMinimumWidth(150)
        self._waktu_combo.setStyleSheet(f"""
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
        # Simpan nilai category sebagai data — None untuk "Semua Waktu"
        for label, val in LOG_WAKTU_OPTIONS:
            self._waktu_combo.addItem(label, val)
        self._waktu_combo.currentIndexChanged.connect(self._on_waktu_changed)
        log_row.addWidget(self._waktu_combo)

        # Tombol refresh manual — berguna saat log baru ditambahkan dari halaman Irfan
        refresh_btn = QPushButton("↻  Refresh Log")
        refresh_btn.setFixedHeight(32)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                border: 1.5px solid {GRAY_BORDER};
                border-radius: 8px;
                padding: 0 12px;
                background: white;
                color: {GRAY_TEXT};
                font-size: 12px;
            }}
            QPushButton:hover {{
                border-color: {GREEN_PRIMARY};
                color: {GREEN_PRIMARY};
            }}
        """)
        refresh_btn.clicked.connect(self._load_logs)
        log_row.addWidget(refresh_btn)

        # Label jumlah log yang cocok
        self._log_count = QLabel("")
        self._log_count.setStyleSheet(f"color: {GRAY_TEXT}; font-size: 11px;")
        log_row.addWidget(self._log_count)
        log_row.addStretch()
        root.addLayout(log_row)

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

    def _on_waktu_changed(self, _index: int):
        """Ambil nilai category dari combo waktu lalu re-filter log."""
        self._active_waktu = self._waktu_combo.currentData()  # None atau string category
        self._update_log_display()

    # ── Logika Pencarian & Filter ─────────────────────────────────────────────

    def _do_search(self):
        """
        Query ke DBHelper berdasarkan teks di search bar.

        - Query kosong → ambil semua makanan (get_all_makanan)
        - Query ada    → gunakan search_makanan(query) yang pakai LIKE di SQL
        Hasil disimpan ke _all_results sebagai cache, lalu difilter + dirender.
        """
        query = self._search_input.text().strip()

        raw = self._db.search_makanan(query) if query else self._db.get_all_makanan()

        self._all_results = raw
        self._render(self._filter_sort(raw))

    def filterLogBerWaktu(self, waktu: str | None) -> List[dict]:
        """
        Filter log harian berdasarkan kategori waktu makan.

        Sesuai diagram class: filterLogBerWaktu(waktu: String) : List<LogHarian>

        Parameter:
            waktu : string kategori ("Sarapan", "Makan Siang", dll)
                    atau None untuk mengembalikan semua log.

        Return:
            List dict log harian yang cocok, diambil dari cache _all_logs.
            Setiap dict berisi kolom dari tabel LogHarian + food_name dari JOIN Makanan.

        Catatan:
            Fungsi ini bekerja dari cache _all_logs (diisi oleh _load_logs).
            Panggil _load_logs() terlebih dahulu jika data mungkin sudah berubah.
        """
        if waktu is None:
            return list(self._all_logs)
        return [
            log for log in self._all_logs
            if log.get("category", "").lower() == waktu.lower()
        ]

    def _load_logs(self):
        """
        Ambil semua log harian dari DB ke cache _all_logs, lalu update tampilan.

        Dipanggil saat:
        - Pertama kali halaman dibuat (via _do_search awal)
        - User klik tombol Refresh Log
        - Dipanggil dari luar (misal LogPage Irfan setelah simpan log baru)
        """

        self._all_logs = self._db.get_all_logs()

        self._update_log_display()

    def _update_log_display(self):
        """
        Update label jumlah log sesuai filter waktu yang aktif.
        Dipanggil setiap kali _all_logs atau _active_waktu berubah.
        """
        filtered = self.filterLogBerWaktu(self._active_waktu)
        total    = len(self._all_logs)
        shown    = len(filtered)

        if total == 0:
            self._log_count.setText("Belum ada log hari ini")
        elif self._active_waktu is None:
            self._log_count.setText(f"{total} log harian tersimpan")
        else:
            self._log_count.setText(
                f"{shown} dari {total} log · waktu: {self._active_waktu}"
            )

    def _filter_sort(self, data: List[dict]) -> List[dict]:
        cfg = FILTER_CHIPS.get(self._active_chip, {"type": "semua"})
        ftype = cfg.get("type", "semua")

        if ftype == "nutrisi":
            key = cfg["key"]
            min_val = cfg.get("min")
            max_val = cfg.get("max")
            def passes_nutrisi(m):
                val = m.get(key) or 0.0
                if min_val is not None and val < min_val:
                    return False
                if max_val is not None and val > max_val:
                    return False
                return True
            data = [m for m in data if passes_nutrisi(m)]
        
        elif ftype == "nama":
            keywords = [k.lower() for k in cfg.get("keywords", [])]
            data = [
                m for m in data
                if any(k in m.get("food_name", "").lower() for k in keywords)
            ]

        return sorted(data, key=lambda m: m.get(self._sort_key, 0) or 0, reverse=self._sort_desc)

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _render(self, results: List[dict]):
        """
        Hapus semua card lama dan buat ulang dari daftar hasil.

        Stretch di posisi terakhir layout dipertahankan (tidak dihapus)
        agar card selalu rata atas di scroll area.
        """
        # Hapus semua item kecuali stretch terakhir (index = count - 1)
        while self._result_layout.count() > 1:
            item = self._result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not results:
            self._show_empty_state()
            self._status.setText("❌  Makanan tidak ditemukan.")
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

        for mkn in results:
            card = FoodCard(mkn)
            card.clicked.connect(self._on_card_click)
            # insertWidget(count-1) = sisipkan sebelum stretch agar card tetap di atas
            self._result_layout.insertWidget(self._result_layout.count() - 1, card)

    def _show_empty_state(self):
        """Tampilkan pesan terpusat saat tidak ada hasil pencarian."""
        empty = QLabel("🔍\n\nMakanan tidak ditemukan.\nCoba kata kunci lain atau ubah filter.")
        empty.setAlignment(Qt.AlignCenter)
        empty.setStyleSheet(f"color: {GRAY_TEXT}; font-size: 13px; padding: 40px;")
        self._result_layout.insertWidget(0, empty)

    # ── Callback ke MainWindow ────────────────────────────────────────────────

    def _on_card_click(self, makanan: dict):
        """
        Dikirim ke MainWindow via callback yang diinjeksikan saat SearchPage dibuat.
        MainWindow kemudian meneruskan ke LogPage milik Irfan.
        """
        print(f"[SearchPage] Dipilih: {makanan.get('food_name')}")
        if self._callback:
            self._callback(makanan)