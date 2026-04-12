
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# ── Palet warna NutriKost ─────────────────────────────────────────────────────
# Didefinisikan di sini agar mudah diganti sekaligus jika desain berubah.
SIDEBAR_BG     = "#1A7A34"   # hijau utama — warna brand NutriKost
SIDEBAR_HOVER  = "#155f28"   # sedikit lebih gelap saat kursor di atas tombol
SIDEBAR_ACTIVE = "#0f4a1f"   # paling gelap — menandai halaman yang sedang dibuka
SIDEBAR_TEXT   = "#ffffff"
SIDEBAR_WIDTH  = 210         # lebar sidebar dalam pixel
CONTENT_BG     = "#f5f7f5"   # abu-abu sangat muda untuk area konten
HEADER_BG      = "#ffffff"
ACCENT_GREEN   = "#1A7A34"

# ── Komponen: Tombol Sidebar ──────────────────────────────────────────────────

class SidebarButton(QPushButton):

    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(parent)
        # Format teks: "  🔍  Cari Makanan" — spasi kiri berfungsi sebagai padding visual
        self.setText(f"  {icon_text}  {label}")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(46)
        self.setFont(QFont("Montserrat Alternates", 11))
        self._apply_style(active=False)

    def set_active(self, active: bool):
        self._apply_style(active)

    def _apply_style(self, active: bool):
        bg     = SIDEBAR_ACTIVE if active else SIDEBAR_BG
        # Garis putih tipis di sisi kiri = indikator visual halaman aktif
        border = "border-left: 4px solid #ffffff;" if active else "border-left: 4px solid transparent;"
        weight = "bold" if active else "normal"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {SIDEBAR_TEXT};
                text-align: left;
                padding-left: 16px;
                border: none;
                {border}
                border-radius: 0px;
                font-weight: {weight};
            }}
            QPushButton:hover {{
                background-color: {SIDEBAR_HOVER};
            }}
        """)


# ── Window Utama ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """
    Kerangka utama aplikasi NutriKost.

    Layout:
        ┌──────────┬──────────────────────────────┐
        │          │  Header (judul halaman)       │
        │ Sidebar  ├──────────────────────────────┤
        │          │                              │
        │          │   Area Konten (QStackedWidget)│
        │          │   — hanya 1 halaman tampil   │
        └──────────┴──────────────────────────────┘

    Cara kerja routing:
        navigate("search") → sidebar tombol Search jadi active
            → stack menampilkan SearchPage
            → judul header berubah jadi "Cari Makanan"
    """

    # Daftar halaman: (ikon, label sidebar, page_key)
    # page_key adalah ID internal yang dipakai navigate() dan setupRouting()
    PAGES = [
        ("🏠", "Dashboard",    "dashboard"),
        ("🔍", "Cari Makanan", "search"),
        ("📋", "Log Harian",   "log"),
        ("🍽️", "Rekomendasi",  "rekomendasi"),
        ("👤", "Profil",       "profil"),
    ]

    PAGE_TITLES = {
        "dashboard":   "Dashboard",
        "search":      "Cari Makanan",
        "log":         "Log Harian",
        "rekomendasi": "Rekomendasi Resep",
        "profil":      "Profil",
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NutriKost — Pemantau Gizi Mahasiswa Kos")
        self.setMinimumSize(1000, 640)
        self.resize(1200, 720)

        # Dua dict ini adalah "daftar isi" navigasi:
        # _sidebar_buttons: page_key → tombol sidebar (untuk set_active)
        # _page_widgets   : page_key → widget halaman (untuk QStackedWidget)
        self._sidebar_buttons: dict[str, SidebarButton] = {}
        self._page_widgets:    dict[str, QWidget]       = {}

        self._build_ui()
        self.setupRouting()

        # Buka halaman Search sebagai tampilan awal
        self.navigate("search")

    # ── Membangun Tampilan ────────────────────────────────────────────────────

    def _build_ui(self):
        """Susun layout root: sidebar (kiri) + area konten (kanan)."""
        root = QWidget()
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)   # tidak ada celah antara sidebar dan konten

        root_layout.addWidget(self._build_sidebar())

        # Area konten = header di atas + stack halaman di bawah
        content_area = QWidget()
        content_area.setStyleSheet(f"background-color: {CONTENT_BG};")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._build_header())

        # QStackedWidget: wadah semua halaman, hanya 1 yang terlihat
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background-color: transparent;")
        content_layout.addWidget(self._stack)

        root_layout.addWidget(content_area, stretch=1)  # konten mengisi sisa lebar

    def _build_sidebar(self) -> QWidget:
        """Buat sidebar: logo brand di atas + tombol navigasi + versi di bawah."""
        sidebar = QWidget()
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar.setStyleSheet(f"background-color: {SIDEBAR_BG};")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Brand / logo teks
        brand = QLabel("🥗  NutriKost")
        brand.setAlignment(Qt.AlignCenter)
        brand.setFixedHeight(64)
        brand.setFont(QFont("Montserrat Alternates", 14, QFont.Bold))
        brand.setStyleSheet(
            f"color: white; background-color: {SIDEBAR_BG}; border-bottom: 1px solid #145e27;"
        )
        layout.addWidget(brand)

        # Buat tombol untuk setiap halaman yang terdaftar di PAGES
        for icon, label, page_key in self.PAGES:
            btn = SidebarButton(icon, label)
            # lambda dengan default arg (k=page_key) mencegah closure bug —
            # tanpa itu semua tombol akan navigate ke page_key terakhir di loop
            btn.clicked.connect(lambda checked, k=page_key: self.navigate(k))
            self._sidebar_buttons[page_key] = btn
            layout.addWidget(btn)

        layout.addStretch()   # dorong elemen versi ke bawah

        version = QLabel("v1.0 · A1 POLBAN")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 10px; padding: 8px;")
        layout.addWidget(version)

        return sidebar

    def _build_header(self) -> QWidget:
        """
        Bar tipis di atas area konten yang menampilkan judul halaman aktif.
        Judul diupdate otomatis oleh navigate().
        """
        header = QFrame()
        header.setFixedHeight(52)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {HEADER_BG};
                border-bottom: 1px solid #e0e0e0;
            }}
        """)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)

        self._page_title = QLabel("Cari Makanan")
        self._page_title.setFont(QFont("Montserrat Alternates", 14, QFont.Bold))
        self._page_title.setStyleSheet(
            f"color: {ACCENT_GREEN}; background: transparent; border: none;"
        )
        layout.addWidget(self._page_title)
        layout.addStretch()

        return header

    # ── Mendaftarkan Halaman ──────────────────────────────────────────────────

    def setupRouting(self):
        """
        Tempat semua halaman didaftarkan ke QStackedWidget.

        PANDUAN INTEGRASI untuk anggota lain:
        Ketika halaman kalian sudah siap, uncomment baris import + _add_page,
        dan hapus baris placeholder di bawahnya.

        Contoh untuk Irfan:
            # Sebelum (hapus ini):
            self._add_page("log", self._placeholder("📋  Log Harian", "Modul Irfan"))

            # Sesudah (aktifkan ini):
            from log_page import LogPage
            self._add_page("log", LogPage())
        """

        # ── Halaman Search (Faqih) — SUDAH AKTIF ─────────────────────────
        from search_page import SearchPage
        self._add_page("search", SearchPage(on_pilih_makanan=self._on_pilih_makanan))

        # ── Halaman Log Harian (Irfan) ────────────────────────────────────
        # from log_page import LogPage
        # self._add_page("log", LogPage())
        self._add_page("log", self._placeholder("📋  Log Harian", "Modul Irfan"))

        # ── Halaman Rekomendasi Resep (Bima) ──────────────────────────────
        # from rekomendasi_page import RekomendasiPage
        # self._add_page("rekomendasi", RekomendasiPage())
        self._add_page("rekomendasi", self._placeholder("🍽️  Rekomendasi Resep", "Modul Bima"))

        # ── Halaman Profil (Anin) ─────────────────────────────────────────
        # from profil_page import ProfilPage
        # self._add_page("profil", ProfilPage())
        self._add_page("profil", self._placeholder("👤  Profil", "Modul Anin"))

        # ── Dashboard (Fatih) ─────────────────────────────────────────────
        # from dashboard import DashboardUI
        # self._add_page("dashboard", DashboardUI())
        self._add_page("dashboard", self._placeholder("🏠  Dashboard", "Modul Fatih"))

    def _add_page(self, key: str, widget: QWidget):
        """Daftarkan widget ke stack dan simpan referensinya di _page_widgets."""
        self._page_widgets[key] = widget
        self._stack.addWidget(widget)

    @staticmethod
    def _placeholder(title: str, owner: str) -> QWidget:
        """
        Widget sementara untuk halaman yang belum diintegrasikan.
        Menampilkan pesan agar jelas halaman mana yang masih kosong.
        """
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)

        lbl = QLabel(title)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFont(QFont("Montserrat Alternates", 18))
        lbl.setStyleSheet("color: #bbb;")
        layout.addWidget(lbl)

        sub = QLabel(f"({owner} — belum diintegrasikan)")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #ccc; font-size: 12px;")
        layout.addWidget(sub)

        return w

    # ── Navigasi ──────────────────────────────────────────────────────────────

    def navigate(self, page_key: str):
        """
        Pindah ke halaman berdasarkan page_key.

        Yang dilakukan:
        - Semua tombol sidebar di-nonaktifkan, lalu tombol page_key diaktifkan
        - QStackedWidget menampilkan widget yang sesuai
        - Judul di header diperbarui
        """
        if page_key not in self._page_widgets:
            return

        # Reset semua tombol ke inactive, lalu aktifkan yang sesuai
        for key, btn in self._sidebar_buttons.items():
            btn.set_active(key == page_key)

        self._stack.setCurrentWidget(self._page_widgets[page_key])
        self._page_title.setText(self.PAGE_TITLES.get(page_key, page_key.title()))

    # ── Callback Antar Modul ──────────────────────────────────────────────────

    def _on_pilih_makanan(self, makanan: dict):
        """
        Dipanggil oleh SearchPage saat user menekan tombol '+ Pilih' pada sebuah makanan.

        Alur:
        SearchPage._on_card_click()
            → callback(makanan)
            → MainWindow._on_pilih_makanan(makanan)   ← di sini
            → navigate("log")
            → LogPage.show_tambah_makan(makanan)      ← milik Irfan

        Parameter makanan berisi dict:
        { code, food_name, cal, protein, fat, carb }

        CATATAN UNTUK IRFAN:
        Tambahkan method ini di class LogPage milik kamu:
            def show_tambah_makan(self, makanan: dict):
                # isi dropdown nama makanan dengan makanan["food_name"]
                # isi preview nutrisi dengan makanan["cal"], ["protein"], dst
        Method ini akan otomatis terpanggil dari sini setelah LogPage diintegrasikan.
        """
        print(f"[MainWindow] Makanan dipilih → {makanan.get('food_name')} ({makanan.get('cal')} kkal)")

        self.navigate("log")

        log_widget = self._page_widgets.get("log")
        if hasattr(log_widget, "show_tambah_makan"):
            log_widget.show_tambah_makan(makanan)