from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QSizePolicy,QMessageBox
)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer, QTime, QSettings
from PyQt5.QtGui import QFont, QPixmap, QIcon, QCursor, QPainter, QColor
from fatih_GUI.toast_notification import show_toast, TOAST_NORMAL, TOAST_ERROR
import os
import sqlite3 as _sqlite3

# collor pallete
SIDEBAR_BG     = "#1A7A34"   
SIDEBAR_HOVER  = "#3C8E52"   
SIDEBAR_ACTIVE = "#5EA271"   
SIDEBAR_TEXT   = "#ffffff"
SIDEBAR_EXP    = 280      #lebar sidebar dibuka       
SIDEBAR_COL    = 76       #lebar sidebar ditutup
CONTENT_BG     = "#F2F4F0"   
HEADER_BG      = "#ffffff"
ACCENT_GREEN   = "#1A7A34"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(BASE_DIR, '..', 'assets', 'icons')
PATTERN_PATH = os.path.join(BASE_DIR, '..', 'assets', 'pattern.png')

#pattern background
class PatternWidget(QWidget):
    #constructor
    def __init__(self, parent=None):
        super().__init__(parent)
        raw = QPixmap(PATTERN_PATH)
        if not raw.isNull():
            self._tile = raw.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            self._tile = QPixmap()
    #cat bg
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(CONTENT_BG))
        if not self._tile.isNull():
            painter.setOpacity(0.1)
            tw = self._tile.width() #lebar tile
            th = self._tile.height() #tinggi tile
            
            x = 0
            while x < self.width(): #loop kiri ke kanan
                y = 0
                while y < self.height(): #loop atas ke bawah
                    painter.drawPixmap(x, y, self._tile)
                    y += th
                x += tw
        painter.end()

#sidebar
class NavItem(QPushButton):
    #constructor
    def __init__(self, icon_filename: str, label: str, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(48)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._collapsed = False #terbuka atau enga
        
        #layout
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 16, 0) #margin kiri, atas, kanan, bawah
        self._layout.setSpacing(0)

        #icon
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedWidth(SIDEBAR_COL)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet("background: transparent;")

        if icon_filename:
            path = os.path.join(ICONS_DIR, icon_filename)
            if os.path.exists(path):
                pix = QPixmap(path).scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.icon_lbl.setPixmap(pix)
            else:
                self.icon_lbl.setText("•")
                self.icon_lbl.setStyleSheet("color: white; background: transparent; font-size: 16px;")

        #text
        self.text_lbl = QLabel(label)
        self.text_lbl.setFont(QFont("Poppins", 10))
        self.text_lbl.setStyleSheet("color: white; background: transparent;")

        #integrasi text dan icon ke layout
        self._layout.addWidget(self.icon_lbl)
        self._layout.addWidget(self.text_lbl, 1)
        self._apply_style(active=False)

    #pas halaman aktif
    def set_active(self, active: bool):
        self._apply_style(active)
        font = QFont("Poppins", 10, QFont.Bold if active else QFont.Normal)
        self.text_lbl.setFont(font)

    #animasi kalo biasa dan di hover
    def _apply_style(self, active: bool):
        bg     = SIDEBAR_ACTIVE if active else "transparent"
        border = "border-left: 3px solid #ffffff;" if active else "border-left: 3px solid transparent;"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                border: none;
                {border}
            }}
            QPushButton:hover {{
                background-color: {SIDEBAR_HOVER};
            }}
        """)
    
    #animasi kalo di hide dan show
    def set_collapsed(self, collapsed: bool):
        self._collapsed = collapsed
        self.text_lbl.setVisible(not collapsed)

#judul section sidebar
class SectionLabel(QLabel):
    #constructor
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Poppins", 8, QFont.Medium))
        self.setFixedHeight(32)
        self.setContentsMargins(SIDEBAR_COL, 0, 0, 0)
        self.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.setStyleSheet("color: rgba(255,255,255,0.55); background: transparent;")
        self._full_text = text

    #kalo dihide bakal dikosongin
    def set_collapsed(self, collapsed: bool):
        self.setText("" if collapsed else self._full_text)


class MainWindow(QMainWindow):
    # Struktur menu (tuple, ordered)
    MENU_UTAMA = [
        ("material-symbols_home-rounded.png", "Home Dashboard", "dashboard"),
        ("fe_search.png", "Cari Makanan", "search"),
        ("material-symbols_list-alt-rounded.png", "Log Makanan", "log"),
        ("iconamoon_history-bold.png", "Riwayat", "riwayat"),
        ("fluent_bowl-salad-24-filled.png", "Resep Makanan", "rekomendasi"),
    ]
    
    VISUALISASI = [
        ("material-symbols_bar-chart-rounded.png", "Kalori Mingguan", "kalori_mingguan"),
        ("fa7-solid_chart-pie.png", "Komposisi Gizi", "komposisi_gizi"),
        ("mingcute_list-ordered-fill.png", "Top 10 Makanan", "top_10_makanan"),
    ]

    #judul dengan dict
    PAGE_TITLES = {
        "dashboard":       "Home Dashboard",
        "search":          "Cari Makanan",
        "log":             "Log Makanan",
        "riwayat":         "Riwayat",
        "rekomendasi":     "Rekomendasi Resep",
        "kalori_mingguan": "Kalori Mingguan",
        "komposisi_gizi":  "Komposisi Gizi",
        "top_10_makanan":  "Top 10 Makanan",
        "profil":          "Profil",
        "setting":         "Pengaturan",
    }

    #sinyal logout
    from PyQt5.QtCore import pyqtSignal
    logout_signal = pyqtSignal()

    #constructor
    def __init__(self, sistem_profil=None):
        super().__init__()
        self.sistem_profil = sistem_profil
        self.is_admin = False
        if self.sistem_profil and self.sistem_profil.current_profil and self.sistem_profil.current_profil.get('email') == 'admin123@gmail.com':
            self.is_admin = True
        
        #judul atas
        self.setWindowTitle("NutriKost — Pemantau Gizi Mahasiswa Kos")
        self.setMinimumSize(1000, 640)
        self.resize(1200, 720)

        #wadah tombol
        self._sidebar_buttons: dict[str, NavItem] = {}
        #wadah halaman
        self._page_widgets: dict[str, QWidget] = {}
        #wadah label page
        self._section_labels: list[SectionLabel] = []
        #status sidebar
        self._collapsed = False

        #buat kerangka, daftarin halaman, tampilin halaman pertama, jalanin timer notif
        self._build_ui()
        self.setupRouting()
        self.navigate("dashboard")
        self.setupNotificationTimer()

    #timer notif
    def setupNotificationTimer(self):
        self._notif_timer = QTimer(self)
        self._notif_timer.timeout.connect(self._check_notifications)
        self._notif_timer.start(10000) # Cek setiap 10 detik agar responsif
        
        # Menyimpan notifikasi yang sudah muncul agar tidak spam di menit yang sama
        self._shown_notifs = set()

    #cek apakah tombol notif on/off
    def _check_notifications(self):
        settings = QSettings("NutriKost", "Pengaturan")
        if settings.value("notif_makan", False, type=bool):
            now = QTime.currentTime()
            current_hm = now.toString("HH:mm")
            
            #default
            times = {
                "Sarapan": str(settings.value("waktu_sarapan", "07:00")),
                "Makan Siang": str(settings.value("waktu_siang", "12:00")),
                "Makan Malam": str(settings.value("waktu_malam", "19:00"))
            }
            
            #looping jadwal makanan
            for meal, time_str in times.items():
                if current_hm == time_str:
                    notif_id = f"{meal}_{current_hm}"
                    if notif_id not in self._shown_notifs:
                        self._shown_notifs.add(notif_id)
                        show_toast(self, f"Hai, sudah waktunya {meal}! Jangan lupa catat asupan makananmu ya.", TOAST_NORMAL)
        
        # Reset list shown_notifs ketika jam berganti
        current_hm = QTime.currentTime().toString("HH:mm")
        self._shown_notifs = {n for n in self._shown_notifs if n.split("_")[1] == current_hm}

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)  

        # Header
        header = QFrame()
        header.setFixedHeight(76)
        header.setStyleSheet(f"background-color: {SIDEBAR_BG}; border: none;")

        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 24, 0)
        h_layout.setSpacing(16)

        #hamburger button
        toggle_btn = QPushButton("☰")
        toggle_btn.setFixedSize(36, 36)
        toggle_btn.setFont(QFont("Segoe UI Symbol", 16))
        toggle_btn.setCursor(Qt.PointingHandCursor)
        toggle_btn.setStyleSheet(f"""
            QPushButton {{ color: white; background: transparent; border: none; border-radius: 6px; }}
            QPushButton:hover {{ background: {SIDEBAR_HOVER}; }}
            QPushButton:pressed {{ background: {SIDEBAR_ACTIVE}; }}
        """)
        toggle_btn.clicked.connect(self._toggle_sidebar)

        self._page_title = QLabel("NutriKos — Cari Makanan")
        self._page_title.setFont(QFont("Poppins", 11, QFont.Bold))
        self._page_title.setStyleSheet("color: white; background: transparent; border: none;")
        self._page_title.setAlignment(Qt.AlignCenter)

        h_layout.addWidget(toggle_btn)
        h_layout.addWidget(self._page_title, 1)
        root_layout.addWidget(header)

        # Body Container
        body_container = QWidget()
        body_layout = QHBoxLayout(body_container)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(SIDEBAR_EXP)
        self.sidebar.setStyleSheet(f"background-color: {SIDEBAR_BG};")
        
        #aimasi sidebar
        self._anim = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self._anim.setDuration(280)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._anim_max = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self._anim_max.setDuration(280)
        self._anim_max.setEasingCurve(QEasingCurve.InOutCubic)

        sb_layout = QVBoxLayout(self.sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Brand / Logo
        logo_widget = QWidget()
        logo_widget.setFixedHeight(76)
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(0)

        logo_icon = QLabel()
        logo_icon.setFixedSize(SIDEBAR_COL, 76)
        logo_icon.setAlignment(Qt.AlignCenter)
        path = os.path.join(ICONS_DIR, 'Logo.png')
        if os.path.exists(path):
            logo_icon.setPixmap(QPixmap(path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        self._logo_text = QLabel()
        self._logo_text.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        text_path = os.path.join(ICONS_DIR, 'Logo text.png')
        if os.path.exists(text_path):
            self._logo_text.setPixmap(QPixmap(text_path).scaled(140, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self._logo_text.setText("NUTRIKOST")
            self._logo_text.setFont(QFont("Montserrat Alternates", 13, QFont.Bold))
            self._logo_text.setStyleSheet("color: white; letter-spacing: 1px;")

        logo_layout.addWidget(logo_icon)
        logo_layout.addWidget(self._logo_text, 1)
        sb_layout.addWidget(logo_widget)

        # Pemisah antar halaman sidebar
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: rgba(255,255,255,0.25); border: none;")
        sb_layout.addWidget(divider)
        sb_layout.addSpacing(16)

        #selain admin
        if not self.is_admin:
            # Menu Utama
            lbl_menu = SectionLabel("Menu Utama")
            self._section_labels.append(lbl_menu)
            sb_layout.addWidget(lbl_menu)

            for icon, label, key in self.MENU_UTAMA:
                btn = NavItem(icon, label)
                btn.clicked.connect(lambda checked, k=key: self.navigate(k))
                self._sidebar_buttons[key] = btn
                sb_layout.addWidget(btn)

            sb_layout.addSpacing(16)

            # Visualisasi
            lbl_vis = SectionLabel("Visualisasi")
            self._section_labels.append(lbl_vis)
            sb_layout.addWidget(lbl_vis)

            for icon, label, key in self.VISUALISASI:
                btn = NavItem(icon, label)
                btn.clicked.connect(lambda checked, k=key: self.navigate(k))
                self._sidebar_buttons[key] = btn
                sb_layout.addWidget(btn)

            #ruang kosong
            sb_layout.addStretch()

            # Pengaturan
            btn_setting = NavItem("solar_settings-bold.png", "Pengaturan")
            btn_setting.clicked.connect(lambda checked, k="setting": self.navigate(k))
            self._sidebar_buttons["setting"] = btn_setting
            sb_layout.addWidget(btn_setting)
        else:
            # Hide logo for admin
            logo_icon.setVisible(False)
            self._logo_text.setVisible(False)
            
            # Hanya Dashboard untuk admin
            btn_admin_dash = NavItem("material-symbols_home-rounded.png", "Dashboard Admin")
            btn_admin_dash.clicked.connect(lambda checked, k="dashboard": self.navigate(k))
            self._sidebar_buttons["dashboard"] = btn_admin_dash
            sb_layout.addWidget(btn_admin_dash)

            # --- Tombol Ekspor Schema ---
            btn_export = NavItem("material-symbols_list-alt-rounded.png", "Ekspor Schema")
            btn_export.clicked.connect(self._export_schema)
            self._sidebar_buttons["export_schema"] = btn_export
            sb_layout.addWidget(btn_export)

            # --- Tombol Impor Schema ---
            btn_import = NavItem("iconamoon_history-bold.png", "Impor Schema")
            btn_import.clicked.connect(self._import_schema)
            self._sidebar_buttons["import_schema"] = btn_import
            sb_layout.addWidget(btn_import)
            
            sb_layout.addStretch()

        # Divider sebelum profile
        div_prof = QFrame()
        div_prof.setFrameShape(QFrame.HLine)
        div_prof.setFixedHeight(1)
        div_prof.setStyleSheet("background: rgba(255,255,255,0.25); border: none;")
        sb_layout.addWidget(div_prof)

        # Profile area
        self._prof_btn = QPushButton()
        self._prof_btn.setFixedHeight(64)
        self._prof_btn.setCursor(Qt.PointingHandCursor)
        self._prof_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; }}
            QPushButton:hover {{ background: {SIDEBAR_HOVER}; }}
        """)
        self._prof_btn.clicked.connect(lambda: self.navigate("profil"))
        self._sidebar_buttons["profil"] = self._prof_btn  

        prof_lay = QHBoxLayout(self._prof_btn)
        prof_lay.setContentsMargins(0, 0, 8, 0)
        prof_lay.setSpacing(0)

        prof_icon = QLabel()
        prof_icon.setFixedSize(SIDEBAR_COL, 64)
        prof_icon.setAlignment(Qt.AlignCenter)
        prof_path = os.path.join(ICONS_DIR, 'gg_profile.png')
        if os.path.exists(prof_path):
            prof_icon.setPixmap(QPixmap(prof_path).scaled(26, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        self._prof_info = QWidget()
        info_lay = QVBoxLayout(self._prof_info)
        info_lay.setContentsMargins(0, 0, 0, 0)
        info_lay.setSpacing(1)
        info_lay.setAlignment(Qt.AlignVCenter)

        profil_data = {}
        if hasattr(self, 'sistem_profil') and self.sistem_profil and self.sistem_profil.current_profil:
            profil_data = self.sistem_profil.current_profil
            
        u_lbl = QLabel(profil_data.get("full_name", "User Profile"))
        u_lbl.setFont(QFont("Poppins", 10, QFont.Bold))
        u_lbl.setStyleSheet("color: white;")
        e_lbl = QLabel(profil_data.get("email", "username@email.com"))
        e_lbl.setFont(QFont("Poppins", 8))
        e_lbl.setStyleSheet("color: rgba(255,255,255,0.55);")

        info_lay.addWidget(u_lbl)
        info_lay.addWidget(e_lbl)

        self._logout_icon = QLabel()
        self._logout_icon.setFixedSize(36, 36)
        self._logout_icon.setAlignment(Qt.AlignCenter)
        logout_path = os.path.join(ICONS_DIR, 'material-symbols_logout-rounded.png')
        if os.path.exists(logout_path):
            self._logout_icon.setPixmap(QPixmap(logout_path).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        prof_lay.addWidget(prof_icon)
        prof_lay.addWidget(self._prof_info, 1)
        prof_lay.addWidget(self._logout_icon)

        sb_layout.addWidget(self._prof_btn)
        body_layout.addWidget(self.sidebar)

        # Content Area
        content_area = PatternWidget() #pattern 
        content_layout = QVBoxLayout(content_area) #wadah all page
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background-color: transparent;")
        content_layout.addWidget(self._stack, 1)

        body_layout.addWidget(content_area, stretch=1)
        root_layout.addWidget(body_container, stretch=1)

    def _toggle_sidebar(self):
        self._collapsed = not self._collapsed #balik state
        target_w = SIDEBAR_COL if self._collapsed else SIDEBAR_EXP
        current_w = self.sidebar.width()

        self._anim.stop() #berhentiin animasi
        self._anim_max.stop()
        self._anim.setStartValue(current_w)
        self._anim.setEndValue(target_w)
        self._anim_max.setStartValue(current_w)
        self._anim_max.setEndValue(target_w)
        self._anim.start()
        self._anim_max.start()

        if not self.is_admin:
            self._logo_text.setVisible(not self._collapsed)
        for lbl in self._section_labels:
            lbl.set_collapsed(self._collapsed)
        self._prof_info.setVisible(not self._collapsed)
        self._logout_icon.setVisible(not self._collapsed)

        for key, btn in self._sidebar_buttons.items():
            if isinstance(btn, NavItem):
                btn.set_collapsed(self._collapsed)

    #routing halaman
    def setupRouting(self):
        #admin gaperlu didaftarin halamannya
        if self.is_admin:
            from bima_scrapper.halaman_request import RequestPage
            self.dashboard_page = RequestPage()
            self._add_page("dashboard", self.dashboard_page)
            
            from anindya_profil import test as anindya_test
            
            self.profil_app = anindya_test.ProfilApp(self.sistem_profil)
            self.profil_app.logout_signal.connect(self.logout_signal.emit)
            self.profil_app.go_back.connect(lambda: self.navigate("dashboard"))
            self._add_page("profil", self.profil_app)
            return
        
        #search page
        from faqih_integrator.search_page import SearchPage
        self._add_page("search", SearchPage(on_pilih_makanan=self._on_pilih_makanan))
        
        #dashboard
        from fatih_GUI.halaman_dashboard import HalamanDashboard
        import os as _os
        _db_path = _os.path.normpath(_os.path.join(BASE_DIR, '..', 'bima_scrapper', 'nutrikost.db'))
        _id_user = (
            self.sistem_profil.current_profil.get('id_user', 1)
            if (hasattr(self, 'sistem_profil') and self.sistem_profil and self.sistem_profil.current_profil)
            else 1
        )
        self.dashboard_page = HalamanDashboard(id_user=_id_user, db_path=_db_path)
        self.dashboard_page.navigate_to.connect(self.navigate)
        self.dashboard_page.tambah_makanan_clicked.connect(lambda: self.navigate("log"))
        self._add_page("dashboard", self.dashboard_page)
        from irfan_calculator.test import LogPage
        self.log_page = LogPage(self.sistem_profil)
        self._add_page("log", self.log_page)
        
        #riwayat
        from irfan_calculator.riwayat import RiwayatPage
        
        self.riwayat_page = RiwayatPage()
        self._add_page("riwayat", self.riwayat_page)
        
        # Hubungkan update log makanan ke refresh data di riwayat
        self.log_page.log_updated.connect(self.riwayat_page.refresh_data)
        # Hubungkan update log makanan ke refresh dashboard
        self.log_page.log_updated.connect(self.dashboard_page.refresh)
        
        #rekomendasi resep
        from bima_scrapper.test_resep import RekomendasiPage
        self._add_page("rekomendasi", RekomendasiPage())
        
        #visualisasi
        from fatih_GUI.halaman_visualisasi import HalamanVisualisasi
        
        self.visualisasi_page = HalamanVisualisasi(id_user=_id_user, db_path=_db_path)
        self.visualisasi_page.tab_changed.connect(self._on_visualisasi_tab_changed)
        
        # Sambungkan sinyal log_updated ke visualisasi_page.refresh agar otomatis update
        self.log_page.log_updated.connect(self.visualisasi_page.refresh)
        # Dan untuk mengecek batas kalori
        self.log_page.log_updated.connect(self._check_calorie_limit)
        
        self._add_page("kalori_mingguan", self.visualisasi_page)
        self._add_page("komposisi_gizi", self.visualisasi_page)
        self._add_page("top_10_makanan", self.visualisasi_page)
        
        #profil
        from anindya_profil import test as anindya_test
        
        self.profil_app = anindya_test.ProfilApp(self.sistem_profil)
        self.profil_app.logout_signal.connect(self.logout_signal.emit)
        self.profil_app.go_back.connect(lambda: self.navigate("dashboard"))
        self._add_page("profil", self.profil_app)
        
        #settings
        from faqih_integrator.setting_page import SettingPage
        self._add_page("setting", SettingPage(self.sistem_profil))

    #cek batas kalori
    def _check_calorie_limit(self):
        settings = QSettings("NutriKost", "Pengaturan")
        if settings.value("notif_kalori", False, type=bool):
            try:
                if self.sistem_profil and self.sistem_profil.current_profil:
                    target_cal = self.sistem_profil.current_profil.get('calory', 2100)
                    persentase = settings.value("batas_kalori", 100, type=int)
                    maks_kalori = int(target_cal * (persentase / 100.0))
                    
                    realisasi = self.sistem_profil.getRealisasiKalori()
                    
                    if realisasi >= maks_kalori:
                        show_toast(self, f"Kalori ({realisasi} kkal) melebihi batas {maks_kalori} kkal!\nKurangi porsi makan atau olahraga.", TOAST_ERROR)
            except Exception as e:
                print(f"Error checking calorie limit: {e}")

    #mendaftarkan halaman
    def _add_page(self, key: str, widget: QWidget):
        self._page_widgets[key] = widget #simpan di dict
        self._stack.addWidget(widget) #tambah ke qstackwidget

    #saat belum terintegrasi
    @staticmethod
    def _placeholder(title: str, owner: str) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel(title)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFont(QFont("Montserrat Alternates", 18, QFont.Bold))
        lbl.setStyleSheet("color: #888;")
        layout.addWidget(lbl)
        sub = QLabel(f"({owner} — belum diintegrasikan)")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #aaa; font-size: 13px;")
        layout.addWidget(sub)
        return w

    # ── Admin: path DB dan schema ─────────────────────────────────────────────
    @property
    def _db_path(self) -> str:
        return os.path.normpath(os.path.join(BASE_DIR, '..', 'bima_scrapper', 'nutrikost.db'))

    @property
    def _schema_path(self) -> str:
        return os.path.normpath(os.path.join(BASE_DIR, '..', 'bima_scrapper', 'db_schema.sql'))

    # ── Admin: Ekspor schema (sqlite3 nutrikost.db .dump > db_schema.sql) ────
    def _export_schema(self):
        reply = QMessageBox.question(
            self, "Konfirmasi Ekspor",
            f"Ekspor seluruh isi database ke:\n{self._schema_path}\n\nLanjutkan?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            conn = _sqlite3.connect(self._db_path)
            with open(self._schema_path, 'w', encoding='utf-8') as f:
                for line in conn.iterdump():
                    f.write(line + '\n')
            conn.close()
            show_toast(self, "✅ Schema berhasil diekspor ke db_schema.sql", TOAST_NORMAL)
        except Exception as e:
            show_toast(self, f"❌ Gagal ekspor schema: {e}", TOAST_ERROR)

    # ── Admin: Impor schema (sqlite3 nutrikost.db < db_schema.sql) ───────────
    def _import_schema(self):
        if not os.path.exists(self._schema_path):
            show_toast(self, f"❌ File db_schema.sql tidak ditemukan!", TOAST_ERROR)
            return
        reply = QMessageBox.warning(
            self, "Konfirmasi Impor",
            f"⚠️ PERINGATAN: Impor akan menimpa data database saat ini!\n\n"
            f"Sumber: {self._schema_path}\n"
            f"Target: {self._db_path}\n\n"
            f"Lanjutkan?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            with open(self._schema_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            conn = _sqlite3.connect(self._db_path)
            conn.executescript(sql_script)
            conn.close()
            show_toast(self, "✅ Schema berhasil diimpor dari db_schema.sql", TOAST_NORMAL)
        except Exception as e:
            show_toast(self, f"❌ Gagal impor schema: {e}", TOAST_ERROR)

    #navigasi halaman
    def navigate(self, page_key: str):
        if page_key not in self._page_widgets:
            return
            
        if page_key in ["kalori_mingguan", "komposisi_gizi", "top_10_makanan"]:
            if hasattr(self, 'visualisasi_page'):
                if page_key == "kalori_mingguan":
                    self.visualisasi_page.set_tab(0)
                elif page_key == "komposisi_gizi":
                    self.visualisasi_page.set_tab(1)
                elif page_key == "top_10_makanan":
                    self.visualisasi_page.set_tab(2)

        if page_key == "dashboard" and hasattr(self, 'dashboard_page'):
            self.dashboard_page.refresh()
                    
        for key, btn in self._sidebar_buttons.items():
            if isinstance(btn, NavItem):
                btn.set_active(key == page_key)
        self._stack.setCurrentWidget(self._page_widgets[page_key])
        title_text = self.PAGE_TITLES.get(page_key, page_key.title())
        self._page_title.setText(f"NutriKos — {title_text}")

    #navigasi halaman visualisasi
    def _on_visualisasi_tab_changed(self, index: int):
        if index == 0:
            self.navigate("kalori_mingguan")
        elif index == 1:
            self.navigate("komposisi_gizi")
        elif index == 2:
            self.navigate("top_10_makanan")

    #kalo pilih makanan di search langsung ke log harian
    def _on_pilih_makanan(self, makanan: dict):
        print(f"[MainWindow] Makanan dipilih → {makanan.get('food_name')} ({makanan.get('cal')} kkal)")
        self.navigate("log")
        log_widget = self._page_widgets.get("log")
        if hasattr(log_widget, "show_tambah_makan"):
            log_widget.show_tambah_makan(makanan)