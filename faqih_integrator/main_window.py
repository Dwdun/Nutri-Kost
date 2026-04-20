
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

#collor pallete
SIDEBAR_BG     = "#1A7A34"   
SIDEBAR_HOVER  = "#155f28"   
SIDEBAR_ACTIVE = "#0f4a1f"   
SIDEBAR_TEXT   = "#ffffff"
SIDEBAR_WIDTH  = 210            
CONTENT_BG     = "#f5f7f5"   
HEADER_BG      = "#ffffff"
ACCENT_GREEN   = "#1A7A34"


#tombol navbar/sidebar
class SidebarButton(QPushButton):

    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(parent)
        self.setText(f"  {icon_text}  {label}")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(46)
        self.setFont(QFont("Montserrat Alternates", 11))
        self._apply_style(active=False)

    #ubah state saat di klik atau aktif
    def set_active(self, active: bool):
        self._apply_style(active)

    #style UI
    def _apply_style(self, active: bool):
        bg     = SIDEBAR_ACTIVE if active else SIDEBAR_BG
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

class MainWindow(QMainWindow):
    #daftar halaman
    PAGES = [
        ("", "Dashboard",    "dashboard"),
        ("", "Cari Makanan", "search"),
        ("", "Log Harian",   "log"),
        ("", "Rekomendasi Resep",  "rekomendasi"),
        ("", "Profil",       "profil"),
        ("", "Visualisasi",   "visualisasi"),
    ]

    #judul
    PAGE_TITLES = {
        "dashboard":   "Dashboard",
        "search":      "Cari Makanan",
        "log":         "Log Harian",
        "rekomendasi": "Rekomendasi Resep",
        "profil":      "Profil",
        "visualisasi" : "Visualisasi",
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NutriKost — Pemantau Gizi Mahasiswa Kos")
        self.setMinimumSize(1000, 640)
        self.resize(1200, 720)

        #dict untuk referensi tombol dan widget
        self._sidebar_buttons: dict[str, SidebarButton] = {}
        self._page_widgets:    dict[str, QWidget]       = {}

        self._build_ui()
        self.setupRouting()

        # Buka halaman dashboard sebagai tampilan awal
        self.navigate("dashboard")

    #setup layout navbar
    def _build_ui(self):
        """Susun layout root: sidebar (kiri) + area konten (kanan)."""
        root = QWidget()
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)  

        #add sidebar ke layout
        root_layout.addWidget(self._build_sidebar())

        #setup area content
        content_area = QWidget()
        content_area.setStyleSheet(f"background-color: {CONTENT_BG};")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        #header judul halaman
        content_layout.addWidget(self._build_header())

        # QStackedWidget: cuma satu halaman yang keliatan dalam satu waktu
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background-color: transparent;")
        content_layout.addWidget(self._stack)

        root_layout.addWidget(content_area, stretch=1)  # konten mengisi sisa lebar

    def _build_sidebar(self) -> QWidget:
        #bikin navbar berisi logo, tombol menu, versi apk
        sidebar = QWidget()
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar.setStyleSheet(f"background-color: {SIDEBAR_BG};")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Brand / logo teks
        brand = QLabel("NutriKost")
        brand.setAlignment(Qt.AlignCenter)
        brand.setFixedHeight(64)
        brand.setFont(QFont("Montserrat Alternates", 16, QFont.Bold))
        brand.setStyleSheet(
            f"color: white; background-color: {SIDEBAR_BG}; border-bottom: 1px solid #145e27;"
        )
        layout.addWidget(brand)

        #loop bikin tombol dari list PAGES di atas
        for icon, label, page_key in self.PAGES:
            btn = SidebarButton(icon, label)
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
        #nampilin judul halaman aktif
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

    #INTEGRASI SISTEM
    def setupRouting(self):

        #Halaman Search
        from search_page import SearchPage
        self._add_page("search", SearchPage(on_pilih_makanan=self._on_pilih_makanan))

        # Halaman Log Harian
        # from log_page import LogPage #sementara di komen dulu
        # self._add_page("log", LogPage())
        self._add_page("log", self._placeholder("  Log Harian", "Modul Irfan"))

        # ── Halaman Rekomendasi Resep (Bima) ──────────────────────────────
        # from rekomendasi_page import RekomendasiPage
        # self._add_page("rekomendasi", RekomendasiPage())
        self._add_page("rekomendasi", self._placeholder(" Rekomendasi Resep", "Modul Bima"))

        # ── Halaman Profil (Anin) ─────────────────────────────────────────
        # from profil_page import ProfilPage
        # self._add_page("profil", ProfilPage())
        self._add_page("profil", self._placeholder("  Profil", "Modul Anin"))

        # ── Dashboard (Fatih) ─────────────────────────────────────────────
        # from dashboard import DashboardUI
        # self._add_page("dashboard", DashboardUI())
        self._add_page("dashboard", self._placeholder("  Dashboard", "Modul Fatih"))

    def _add_page(self, key: str, widget: QWidget):
        #daftarin widget halaman ke stack
        self._page_widgets[key] = widget
        self._stack.addWidget(widget)

    @staticmethod
    def _placeholder(title: str, owner: str) -> QWidget:
        #tampilan smentara page kosong
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

    def navigate(self, page_key: str):
        #fungsi buat pindah halaman
        if page_key not in self._page_widgets:
            return

        #Reset semua tombol ke inactive, lalu aktifkan yang sesuai
        for key, btn in self._sidebar_buttons.items():
            btn.set_active(key == page_key)

        #ganti halaman dan update header page
        self._stack.setCurrentWidget(self._page_widgets[page_key])
        self._page_title.setText(self.PAGE_TITLES.get(page_key, page_key.title()))

    #CALLBACK INTEGRASI (untuk add makanan)
    def _on_pilih_makanan(self, makanan: dict):
        #pindahin user ke halaman log harian dan bawa data makanannya
        print(f"[MainWindow] Makanan dipilih → {makanan.get('food_name')} ({makanan.get('cal')} kkal)")

        #pindah ke halaman log
        self.navigate("log")

        #open data makanan ke fungsi show tambah makanan
        log_widget = self._page_widgets.get("log")
        if hasattr(log_widget, "show_tambah_makan"):
            log_widget.show_tambah_makan(makanan)