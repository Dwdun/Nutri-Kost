import sys
import os
import re
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'fatih_GUI')))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QMessageBox,
    QFrame, QStackedWidget, QCheckBox, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect, QScrollArea, QDialog, QListView
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread
from fatih_GUI.toast_notification import show_toast, TOAST_SUCCESS, TOAST_ERROR, TOAST_NORMAL
from PyQt5.QtGui import QFont, QPixmap, QIcon, QColor, QPainter, QCursor

import email_sender
from profil_system import ProfilSystem
from fatih_GUI.template_halaman import (
    PageTemplate, PatternWidget, ICONS_DIR, 
    font_title, font_body, font_label, load_fonts,
    C_NAVBAR_HVR, C_TEXT_DARK, C_TEXT_SUB
)

# ==========================================
# CONSTANTS & COLORS
# ==========================================
GREEN_PRIMARY = "#1A7A34"
GREEN_LIGHT   = "#CAEED4"
GREEN_BG      = "#1f7a36" 
GREEN_CARD    = "#32b856"   
GREEN_BTN     = "#24833c" 
GREEN_DARK    = "#145925"
GRAY_TXT      = "#555555"

def buat_input(placeholder, is_password=False):
    f = QLineEdit()
    f.setPlaceholderText(placeholder)
    f.setFixedHeight(48)
    f.setFont(font_body(10))
    if is_password:
        f.setEchoMode(QLineEdit.Password)
    f.setStyleSheet("""
        QLineEdit {
            border: none;
            border-radius: 24px;
            padding: 0 20px;
            background: white;
            color: #333333;
        }
    """)
    return f

def buat_label(text, size=10, bold=False):
    l = QLabel(text)
    l.setFont(font_label(size, bold=bold))
    l.setStyleSheet("color: white; background: transparent;")
    return l


# ==========================================
# AUTH BASE WINDOW
# ==========================================
class AuthBaseWidget(QWidget):
    def __init__(self, right_widget, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Left Panel (Green with Logo)
        left_panel = QFrame()
        left_panel.setStyleSheet(f"background-color: {GREEN_PRIMARY};")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignCenter)
        
        # Logo widget (to group both)
        lw = QWidget()
        ll = QVBoxLayout(lw)
        ll.setAlignment(Qt.AlignCenter)

        logo = QLabel()
        logo_path = os.path.join(ICONS_DIR, 'Logo.png')
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            logo.setPixmap(pix.scaled(130, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)
        
        logo_text = QLabel()
        logo_text_path = os.path.join(ICONS_DIR, 'Logo text.png')
        if os.path.exists(logo_text_path):
            pix2 = QPixmap(logo_text_path)
            logo_text.setPixmap(pix2.scaled(140, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_text.setAlignment(Qt.AlignCenter)

        ll.addWidget(logo)
        ll.addWidget(logo_text)
        
        left_layout.addWidget(lw)
        
        # Right Panel (Pattern with central widget)
        right_panel = PatternWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(right_widget)
        
        layout.addWidget(left_panel, 1)   # Ratio 1:1 or 4:6 -> we use 1:1 for simplicity
        layout.addWidget(right_panel, 1)


class AuthCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(500)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {GREEN_CARD};
                border-radius: 16px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

# ==========================================
# AUTH WIDGETS
# ==========================================
class HalamanLogin(QWidget):
    go_register = pyqtSignal()
    login_success = pyqtSignal()
    go_back = pyqtSignal()

    def __init__(self, sistem: ProfilSystem, parent=None):
        super().__init__(parent)
        self._sistem = sistem
        layout = QVBoxLayout(self)
        layout.addStretch(1)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(24)

        # Title
        title = QLabel("Welcome Back, User")
        title.setAlignment(Qt.AlignCenter)
        f = QFont('Montserrat Alternates Medium', 32)
        f.setStyleHint(QFont.SansSerif)
        title.setFont(f)
        title.setMinimumHeight(60)
        title.setWordWrap(False)
        title.setStyleSheet("color: #1C1C1C; font-size: 32px; font-family: 'Montserrat Alternates Medium';")
        layout.addWidget(title)
        layout.addSpacing(20)

        # Card
        card = AuthCard()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(30, 24, 30, 36)
        cl.setSpacing(10)

        # Header Row inside Card
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        
        header_row.addStretch()
        
        internal_title = QLabel("Login Page")
        internal_title.setFont(font_label(12, bold=False))
        internal_title.setStyleSheet("color: black; background: transparent;")
        header_row.addWidget(internal_title)
        
        header_row.addStretch()
        
        cl.addLayout(header_row)
        cl.addSpacing(10)

        # Email
        lbl_email = buat_label("Email", 10)
        lbl_email.setStyleSheet("color: #115724; background: transparent;")
        cl.addWidget(lbl_email)
        self.inp_user = buat_input("Type Here")
        cl.addWidget(self.inp_user)

        cl.addSpacing(6)

        # Password 
        pw_row = QHBoxLayout()
        lbl_pass = buat_label("Password", 10)
        lbl_pass.setStyleSheet("color: #115724; background: transparent;")
        pw_row.addWidget(lbl_pass)
        pw_row.addStretch()
        lupa = QPushButton("Lupa Password?")
        lupa.setFont(font_label(10))
        lupa.setCursor(Qt.PointingHandCursor)
        lupa.setStyleSheet("QPushButton { background: transparent; color: black; border: none; text-align: right; }")
        lupa.clicked.connect(self._aksi_lupa)
        pw_row.addWidget(lupa)

        cl.addLayout(pw_row)
        
        self.inp_pass = buat_input("********", True)
        cl.addWidget(self.inp_pass)
        
        cl.addSpacing(16)

        self.btn_masuk = QPushButton("Masuk")
        self.btn_masuk.setFixedHeight(48)
        self.btn_masuk.setFont(QFont('Poppins SemiBold', 10))
        self.btn_masuk.setCursor(Qt.PointingHandCursor)
        self.btn_masuk.setStyleSheet(f"""
            QPushButton {{
                background-color: #1A7A34;
                color: white; border-radius: 24px;
            }}
            QPushButton:hover {{ background-color: #145925; }}
        """)
        self.btn_masuk.clicked.connect(self._aksi_masuk)
        cl.addWidget(self.btn_masuk)

        cl.addSpacing(6)

        # Divider (atau masuk dengan)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #1A7A34;")
        cl.addWidget(line)

        div_lbl = QLabel("atau masuk dengan")
        div_lbl.setFont(font_label(8))
        div_lbl.setStyleSheet("color: #115724;")
        div_lbl.setAlignment(Qt.AlignCenter)
        cl.addWidget(div_lbl)

        # Google button
        btn_google = QPushButton("  Masuk dengan Google")
        g_icon_path = os.path.join(ICONS_DIR, 'google.png')
        if os.path.exists(g_icon_path):
             btn_google.setIcon(QIcon(g_icon_path))
             btn_google.setIconSize(QSize(30, 30))
        btn_google.setFixedHeight(48)
        btn_google.setFont(QFont('Poppins SemiBold', 10))
        btn_google.setCursor(Qt.PointingHandCursor)
        btn_google.setStyleSheet("""
            QPushButton {
                background-color: #d4d4d4; color: #828282; border-radius: 24px;
            }
            QPushButton:hover { background-color: #D1D5DB; }
        """)
        cl.addWidget(btn_google)

        cl.addSpacing(12)

        # Daftar text
        dr = QHBoxLayout()
        dr.addStretch()
        lbl_punya = buat_label("belum punya akun?", 8)
        lbl_punya.setStyleSheet("color: black; background: transparent;")
        dr.addWidget(lbl_punya)
        btn_daftar = QPushButton("Daftar Sekarang")
        btn_daftar.setFont(font_label(8, bold=True))
        btn_daftar.setCursor(Qt.PointingHandCursor)
        btn_daftar.setStyleSheet("QPushButton { background: transparent; color: white; border: none; text-decoration: underline; padding: 0; margin: 0; }")
        btn_daftar.clicked.connect(self.go_register.emit)
        dr.addWidget(btn_daftar)
        dr.addStretch()
        dr.setAlignment(Qt.AlignCenter)
        cl.addLayout(dr)

        layout.addWidget(card, alignment=Qt.AlignCenter)
        layout.addStretch(1)

    def clear_fields(self):
        self.inp_user.clear()
        self.inp_pass.clear()

    def _aksi_masuk(self):
        usr = self.inp_user.text()
        pwd = self.inp_pass.text()
        success, msg = self._sistem.login(usr, pwd)
        if success:
            self.login_success.emit()
        else:
            show_toast(self, msg, TOAST_ERROR)

    def _aksi_lupa(self):
        dlg = ForgotPasswordDialog(self.window())
        dlg.setGeometry(0, 0, self.window().width(), self.window().height())
        if dlg.exec_() == QDialog.Accepted:
            email = dlg.email_value
            if email:
                if self._sistem.cekEmailTerdaftar(email):
                    # 1. Cek apakah email config sudah diisi atau masih dummy
                    cfg = email_sender.load_config()
                    if email_sender.is_config_dummy(cfg):
                        # Tampilkan panduan konfigurasi email
                        guide = EmailConfigGuideDialog(self.window())
                        guide.setGeometry(0, 0, self.window().width(), self.window().height())
                        guide.exec_()
                        return
                    
                    # 2. Buat password sementara acak
                    temp_pwd = email_sender.generate_temp_password()
                    
                    # 3. Tampilkan loading overlay
                    self.loading_dlg = EmailSendingDialog(self.window())
                    self.loading_dlg.setGeometry(0, 0, self.window().width(), self.window().height())
                    
                    # 4. Buat background thread worker
                    self.worker = EmailSenderWorker(self._sistem, email, temp_pwd)
                    
                    # Hubungkan signal dari worker
                    def on_finished(success, message):
                        self.loading_dlg.accept() # Tutup loading dialog
                        if success:
                            show_toast(self, f"Reset sukses! Silakan cek email Anda: {email}", TOAST_SUCCESS)
                        else:
                            # Jika terjadi error pengiriman, tampilkan box detail
                            QMessageBox.critical(
                                self, 
                                "Gagal Mengirim Email", 
                                f"Terjadi kesalahan saat mengirim email reset:\n\n{message}\n\n"
                                "Pastikan koneksi internet aktif dan kredensial di email_config.json sudah benar."
                            )
                    
                    self.worker.finished.connect(on_finished)
                    
                    # Jalankan worker di background thread
                    self.worker.start()
                    
                    # Tampilkan dialog secara modal (akan memblokir interaksi user sampai thread selesai)
                    self.loading_dlg.exec_()
                else:
                    show_toast(self, "Email tidak terdaftar!", TOAST_ERROR)



class HalamanRegister(QWidget):
    go_datadiri = pyqtSignal(dict)
    go_back = pyqtSignal()

    def __init__(self, sistem=None, parent=None):
        super().__init__(parent)
        self._sistem = sistem
        layout = QVBoxLayout(self)
        layout.addStretch(1)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(24)

        title = QLabel("Daftar")
        title.setAlignment(Qt.AlignCenter)
        f = QFont('Montserrat Alternates Medium', 32)
        f.setStyleHint(QFont.SansSerif)
        title.setFont(f)
        title.setMinimumHeight(60)
        title.setWordWrap(False)
        title.setStyleSheet("color: #1C1C1C; font-size: 32px; font-family: 'Montserrat Alternates Medium';")
        layout.addWidget(title)
        layout.addSpacing(20)

        card = AuthCard()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(32, 24, 32, 24)
        cl.setSpacing(8)

        # Header Row inside Card
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        
        self.btn_back = QPushButton()
        self.btn_back.setFixedSize(32, 32)
        self.btn_back.setCursor(Qt.PointingHandCursor)
        arrow_path = os.path.join(ICONS_DIR, 'famicons_arrow-back-outline.png')
        if os.path.exists(arrow_path):
            self.btn_back.setIcon(QIcon(arrow_path))
            self.btn_back.setIconSize(QSize(24, 24))
        self.btn_back.setStyleSheet("QPushButton { background: transparent; border: none; }")
        self.btn_back.clicked.connect(self.go_back.emit)
        header_row.addWidget(self.btn_back)
        
        header_row.addStretch()
        
        internal_title = QLabel("Register Page")
        internal_title.setFont(font_label(12, bold=False))
        internal_title.setStyleSheet("color: black; background: transparent;")
        header_row.addWidget(internal_title)
        
        header_row.addStretch()
        header_row.addSpacing(30) # Spacer to center title
        
        cl.addLayout(header_row)
        cl.addSpacing(10)

        lbl_nama = buat_label("Nama Lengkap")
        lbl_nama.setStyleSheet("color: #115724; background: transparent;")
        cl.addWidget(lbl_nama)
        self.inp_nama = buat_input("Type Here")
        cl.addWidget(self.inp_nama)

        lbl_email = buat_label("Email")
        lbl_email.setStyleSheet("color: #115724; background: transparent;")
        cl.addWidget(lbl_email)
        self.inp_email = buat_input("Type Here")
        cl.addWidget(self.inp_email)

        lbl_pass = buat_label("Password")
        lbl_pass.setStyleSheet("color: #115724; background: transparent;")
        cl.addWidget(lbl_pass)
        self.inp_pass = buat_input("********", True)
        cl.addWidget(self.inp_pass)

        lbl_konf = buat_label("Konfirmasi Password")
        lbl_konf.setStyleSheet("color: #115724; background: transparent;")
        cl.addWidget(lbl_konf)
        self.inp_konf = buat_input("********", True)
        cl.addWidget(self.inp_konf)

        chk_row = QHBoxLayout()
        self.chk_terms = QCheckBox("Saya setuju dengan Syarat dan Ketentuan")
        self.chk_terms.setStyleSheet(f"""
            QCheckBox {{ 
                color: white; 
                font-size: 11px; 
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                background-color: #E0E0E0;
            }}
            QCheckBox::indicator:checked {{
                background-color: #1A7A34;
                image: url({os.path.join(ICONS_DIR, 'checkmark_white.png').replace('\\', '/')});
            }}
        """)
        chk_row.addWidget(self.chk_terms)
        cl.addLayout(chk_row)

        self.btn_lanjut = QPushButton("Lanjutkan")
        self.btn_lanjut.setFixedHeight(48)
        self.btn_lanjut.setFont(QFont('Poppins SemiBold', 10))
        self.btn_lanjut.setCursor(Qt.PointingHandCursor)
        self.btn_lanjut.setStyleSheet(f"""
            QPushButton {{ background-color: {GREEN_BTN}; color: white; border-radius: 24px; }}
            QPushButton:hover {{ background-color: {GREEN_PRIMARY}; }}
        """)
        self.btn_lanjut.clicked.connect(self._lanjut)
        cl.addWidget(self.btn_lanjut)

        layout.addWidget(card, alignment=Qt.AlignCenter)
        layout.addStretch(1)

    def clear_fields(self):
        self.inp_nama.clear()
        self.inp_email.clear()
        self.inp_pass.clear()
        self.inp_konf.clear()
        self.chk_terms.setChecked(False)

    def _lanjut(self):
        full_name = self.inp_nama.text().strip()
        email = self.inp_email.text().strip()
        sistem = self._sistem or ProfilSystem()

        if not full_name:
            show_toast(self, "Nama tidak boleh kosong!", TOAST_ERROR)
            return

        valid, msg = sistem.is_email_allowed(email)
        if not valid:
            show_toast(self, msg, TOAST_ERROR)
            return

        if not self.chk_terms.isChecked():
            show_toast(self, "Anda harus setuju dengan S&K", TOAST_ERROR)
            return

        p1 = self.inp_pass.text()
        p2 = self.inp_konf.text()

        if len(p1) < 6:
            show_toast(self, "Password minimal 6 karakter!", TOAST_ERROR)
            return

        if p1 != p2:
            show_toast(self, "Password tidak cocok!", TOAST_ERROR)
            return

        # Validasi Email Duplikat
        # Dilakukan sebelum pindah ke halaman Data Diri
        if sistem.cekEmailTerdaftar(email):
            show_toast(self, "Email sudah terdaftar. Silakan gunakan email lain.", TOAST_ERROR)
            return

        data = {
            'full_name': full_name,
            'email': email,
            'password': p1
        }
        self.go_datadiri.emit(data)

class HalamanDataDiri(QWidget):
    register_success = pyqtSignal()
    go_back = pyqtSignal()
    register_data = {}

    def __init__(self, sistem: ProfilSystem, parent=None):
        super().__init__(parent)
        # Pastikan sistem selalu tersedia agar halaman tidak crash jika data tidak terpasang
        self._sistem = sistem or ProfilSystem()
        # Salin data pendaftaran agar tidak memodifikasi referensi yang tidak aman
        self.register_data = dict(getattr(self, 'register_data', {}) or {})
        layout = QVBoxLayout(self)
        layout.addStretch(1)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(24)

        title = QLabel("Data Diri")
        title.setAlignment(Qt.AlignCenter)
        f = QFont('Montserrat Alternates Medium', 32)
        f.setStyleHint(QFont.SansSerif)
        title.setFont(f)
        title.setMinimumHeight(60)
        title.setWordWrap(False)
        title.setStyleSheet("color: #1C1C1C; font-size: 32px; font-family: 'Montserrat Alternates Medium';")
        layout.addWidget(title)
        layout.addSpacing(20)

        card = AuthCard()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(32, 24, 32, 24)
        cl.setSpacing(8)

        # Header Row inside Card
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        
        self.btn_back = QPushButton()
        self.btn_back.setFixedSize(32, 32)
        self.btn_back.setCursor(Qt.PointingHandCursor)
        arrow_path = os.path.join(ICONS_DIR, 'famicons_arrow-back-outline.png')
        if os.path.exists(arrow_path):
            self.btn_back.setIcon(QIcon(arrow_path))
            self.btn_back.setIconSize(QSize(24, 24))
        self.btn_back.setStyleSheet("QPushButton { background: transparent; border: none; }")
        self.btn_back.clicked.connect(self.go_back.emit)
        header_row.addWidget(self.btn_back)
        
        header_row.addStretch()
        
        internal_title = QLabel("Register Page") # Using 'Register Page' as seen in the mockup for this step
        internal_title.setFont(font_label(12, bold=False))
        internal_title.setStyleSheet("color: black; background: transparent;")
        header_row.addWidget(internal_title)
        
        header_row.addStretch()
        header_row.addSpacing(30) # Spacer to center title
        
        cl.addLayout(header_row)
        cl.addSpacing(10)

        # Layout: Jenis Kelamin (Full)
        lbl_jk = buat_label("Jenis Kelamin")
        lbl_jk.setStyleSheet("color: #115724; background: transparent;")
        cl.addWidget(lbl_jk)
        self.inp_jk = QComboBox()
        self.inp_jk.addItems(["", "Perempuan", "Laki-laki"])
        self.inp_jk.setFixedHeight(48)
        combo_style = '''
            QComboBox {
                border: none;
                border-radius: 24px;
                padding: 5px 16px;
                background: white;
                color: #333333;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border: none;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #1A7A34;
                border-radius: 0px;
                background-color: white;
                outline: 0px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 40px;
                padding-left: 10px;
                color: #555555;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: rgba(26, 122, 52, 0.15);
                color: #1A7A34;
            }
        '''
        self.inp_jk.setView(QListView())
        self.inp_jk.setStyleSheet(combo_style)
        cl.addWidget(self.inp_jk)

        # Row 2: Usia | Aktivitas
        r2 = QHBoxLayout()
        c21 = QVBoxLayout()
        lbl_usia = buat_label("Usia (tahun)")
        lbl_usia.setStyleSheet("color: #115724; background: transparent;")
        c21.addWidget(lbl_usia)
        self.inp_usia = buat_input("Type Here")
        c21.addWidget(self.inp_usia)
        r2.addLayout(c21, 1)

        c22 = QVBoxLayout()
        lbl_akt = buat_label("Aktivitas")
        lbl_akt.setStyleSheet("color: #115724; background: transparent;")
        c22.addWidget(lbl_akt)
        self.inp_akt = QComboBox()
        self.inp_akt.addItems(["Sedentary (jarang olahraga)", "Ringan", "Sedang", "Berat"])
        self.inp_akt.setFixedHeight(48)
        self.inp_akt.setView(QListView())
        self.inp_akt.setStyleSheet(combo_style)
        c22.addWidget(self.inp_akt)
        r2.addLayout(c22, 1)
        cl.addLayout(r2)

        # Row 3: BB | TB
        r3 = QHBoxLayout()
        c31 = QVBoxLayout()
        lbl_bb = buat_label("Berat Badan (kg)")
        lbl_bb.setStyleSheet("color: #115724; background: transparent;")
        c31.addWidget(lbl_bb)
        self.inp_bb = buat_input("Type Here")
        c31.addWidget(self.inp_bb)
        r3.addLayout(c31, 1)

        c32 = QVBoxLayout()
        lbl_tb = buat_label("Tinggi Badan (cm)")
        lbl_tb.setStyleSheet("color: #115724; background: transparent;")
        c32.addWidget(lbl_tb)
        self.inp_tb = buat_input("Type Here")
        c32.addWidget(self.inp_tb)
        r3.addLayout(c32, 1)
        cl.addLayout(r3)

        # Row 4: Tujuan Diet
        lbl_diet = buat_label("Tujuan Diet")
        lbl_diet.setStyleSheet("color: #115724; background: transparent;")
        cl.addWidget(lbl_diet)
        self.inp_diet = QComboBox()
        self.inp_diet.addItems(["Maintain Berat Badan", "Turun Berat Badan", "Naik Berat Badan"])
        self.inp_diet.setFixedHeight(48)
        self.inp_diet.setView(QListView())
        self.inp_diet.setStyleSheet(combo_style)
        cl.addWidget(self.inp_diet)

        cl.addSpacing(10)
        
        cl.addSpacing(12)

        # Target box
        tgt = QFrame()
        tgt.setStyleSheet("background-color: rgba(0,0,0,0.1); border-radius: 12px;")
        tl = QVBoxLayout(tgt)
        tl.setContentsMargins(16, 8, 16, 8)
        tl.setSpacing(0)
        
        lbl_tgt = QLabel("Target Kalori Harian (estimasi)")
        lbl_tgt.setFont(font_label(8))
        lbl_tgt.setStyleSheet("color: white; background: transparent;")
        tl.addWidget(lbl_tgt)

        self.val_cal = QLabel("2100 kkal/hari")
        self.val_cal.setFont(QFont('Montserrat Alternates SemiBold', 26))
        self.val_cal.setStyleSheet("color: #115724; background: transparent; font-weight: bold;")
        tl.addWidget(self.val_cal)
        
        lbl_note = QLabel("Berdasarkan BMR + tingkat aktivitas (bisa diubah)")
        lbl_note.setFont(font_label(8))
        lbl_note.setStyleSheet("color: rgba(255,255,255,0.8); background: transparent;")
        lbl_note.setWordWrap(True)
        tl.addWidget(lbl_note)
        cl.addWidget(tgt)
        
        # Connections for real-time calc
        self.inp_bb.textChanged.connect(self._update_estimasi)
        self.inp_tb.textChanged.connect(self._update_estimasi)
        self.inp_usia.textChanged.connect(self._update_estimasi)
        self.inp_jk.currentTextChanged.connect(self._update_estimasi)
        self.inp_akt.currentTextChanged.connect(self._update_estimasi)

        # Skip
        skip = QPushButton("Lewati, isi nanti")
        skip.setCursor(Qt.PointingHandCursor)
        skip.setFont(font_label(10))
        skip.setStyleSheet("QPushButton { background: transparent; color: #E0E0E0; border: none; margin: 10px 0 2px 0; }")
        skip.clicked.connect(self._lewati)
        cl.addWidget(skip, alignment=Qt.AlignCenter)

        # Daftar btn
        btn_daftar = QPushButton("Daftar")
        btn_daftar.setFixedHeight(48)
        btn_daftar.setFont(QFont('Poppins SemiBold', 10))
        btn_daftar.setCursor(Qt.PointingHandCursor)
        btn_daftar.setStyleSheet(f"""
            QPushButton {{ background-color: {GREEN_BTN}; color: white; border-radius: 24px; }}
            QPushButton:hover {{ background-color: {GREEN_PRIMARY}; }}
        """)
        btn_daftar.clicked.connect(self._daftar)
        cl.addWidget(btn_daftar)

        layout.addWidget(card)
        layout.addStretch(1)

    def _show_error(self, message):
        # Tangani pesan error secara aman agar UI tidak crash jika toast gagal
        try:
            show_toast(self, str(message), TOAST_ERROR)
        except Exception:
            print(f"[HalamanDataDiri] Failed to show toast: {message}")

    def _parse_input_angka(self):
        # Validasi input angka sebelum lanjut ke proses pendaftaran
        try:
            bb = float(self.inp_bb.text() or 0)
            tb = float(self.inp_tb.text() or 0)
            usia = int(float(self.inp_usia.text() or 0))
            if bb <= 0 or tb <= 0 or usia <= 0:
                return None, "Usia, berat, dan tinggi harus lebih besar dari 0."
            return (bb, tb, usia), None
        except (TypeError, ValueError):
            return None, "Input tidak valid! Pastikan Usia, BB, dan TB berisi nilai angka."

    def _build_register_payload(self):
        # Pastikan data awal pendaftaran lengkap sebelum membuat profil
        try:
            payload = dict(getattr(self, 'register_data', {}) or {})
        except Exception:
            payload = {}

        if not isinstance(payload, dict):
            payload = {}

        required = ['full_name', 'email', 'password']
        missing = [key for key in required if not payload.get(key)]
        if missing:
            return None, "Data pendaftaran belum lengkap. Silakan kembali dan isi ulang."

        return payload, None

    def _update_estimasi(self):
        try:
            bb = float(self.inp_bb.text() or 0)
            tb = float(self.inp_tb.text() or 0)
            usia = int(self.inp_usia.text() or 0)
            jk = self.inp_jk.currentText()
            akt = self.inp_akt.currentText()
            if bb > 0 and tb > 0 and usia > 0 and jk in ["Perempuan", "Laki-laki"]:
                calc = self._sistem.calculatorHarrisBenedict(jk, bb, tb, usia, akt)
                self.val_cal.setText(f"{calc} kkal/hari")
            else:
                self.val_cal.setText("--- kkal/hari")
        except Exception:
            self.val_cal.setText("--- kkal/hari")

    def _create(self, bb, tb, usia, jk, aktivitas):
        try:
            # Ambil data awal dari register dulu, lalu tambahkan data data diri
            payload, error = self._build_register_payload()
            if error:
                self._show_error(error)
                return False

            data = dict(payload)
            data['weight'] = bb
            data['height'] = tb
            data['age'] = usia
            data['gender'] = jk
            data['activity'] = aktivitas
            data['diet_goal'] = self.inp_diet.currentText() if hasattr(self, 'inp_diet') and self.inp_diet else 'Maintain Berat Badan'

            res = self._sistem.createProfil(data)
            if isinstance(res, tuple):
                success, msg = res
            else:
                success = bool(res)
                msg = "Gagal mendaftar. Periksa input anda."

            if success:
                # Beri tahu launcher bahwa proses pendaftaran selesai
                self.register_success.emit()
                return True

            self._show_error(str(msg))
            return False
        except Exception:
            # Simpan traceback untuk debugging, tapi jangan biarkan aplikasi crash
            traceback.print_exc()
            self._show_error("Terjadi kesalahan saat menyimpan profil. Silakan coba lagi.")
            return False

    def _lewati(self):
        try:
            # Gunakan nilai default agar alur tetap bisa lanjut tanpa data lengkap
            self._create(50, 150, 20, "Perempuan", "Sedentary (Jarang Olahraga)")
        except Exception:
            traceback.print_exc()
            self._show_error("Terjadi kesalahan saat melewati langkah. Silakan coba lagi.")

    def _daftar(self):
        try:
            jk = self.inp_jk.currentText()
            if not jk or jk not in ["Perempuan", "Laki-laki"]:
                self._show_error("Jenis kelamin harus dipilih!")
                return

            # Parse input dahulu untuk mencegah exception dari float/int conversion
            parsed, error = self._parse_input_angka()
            if error:
                self._show_error(error)
                return

            bb, tb, usia = parsed
            self._create(
                bb,
                tb,
                usia,
                jk,
                self.inp_akt.currentText() or "Sedentary (Jarang Olahraga)",
            )
        except Exception:
            traceback.print_exc()
            self._show_error("Terjadi kesalahan saat mendaftar. Silakan coba lagi.")

    def clear_fields(self):
        self.register_data = {}
        self.inp_jk.setCurrentIndex(0)  # Empty ""
        self.inp_usia.clear()
        self.inp_akt.setCurrentIndex(0)  # Sedentary (Jarang Olahraga)
        self.inp_bb.clear()
        self.inp_tb.clear()
        self.inp_diet.setCurrentIndex(0)  # Maintain Berat Badan
        self.val_cal.setText("--- kkal/hari")


class EditProfileDialog(QDialog):
    def __init__(self, sistem: ProfilSystem, parent=None):
        super().__init__(parent)
        self.sistem = sistem
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("OverlayDialog")
        self.setStyleSheet("#OverlayDialog { background-color: rgba(0, 0, 0, 120); }")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignCenter)
        
        self.card = QFrame()
        self.card.setFixedSize(400, 680)
        self.card.setStyleSheet("""
            QFrame { background: white; border-radius: 25px; border: none; }
            QLabel { border: none; background: transparent; color: #555555; font-family: 'Poppins'; }
            QLineEdit { border: none; border-radius: 20px; padding-left: 15px; background: rgba(26, 122, 52, 0.25); color: #1A7A34; }
        """)

        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(12)


        title = QLabel("Edit Profile")
        title.setFont(QFont('Poppins', 14, QFont.Bold))
        title.setStyleSheet("color: #1A7A34;")
        card_layout.addWidget(title)

        profil = self.sistem.current_profil or {}
        
        def lbl_blk(text):
            l = QLabel(text)
            return l

        # Nama
        card_layout.addWidget(lbl_blk("Nama Lengkap"))
        self.inp_nama = QLineEdit()
        self.inp_nama.setFixedHeight(45)
        self.inp_nama.setText(profil.get("full_name", ""))
        card_layout.addWidget(self.inp_nama)

        row = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(lbl_blk("Usia (tahun)"))
        self.inp_usia = QLineEdit()
        self.inp_usia.setFixedHeight(45)
        self.inp_usia.setText(str(profil.get("age", "")))
        v1.addWidget(self.inp_usia)
        
        v2 = QVBoxLayout()
        v2.addWidget(lbl_blk("BB (kg)"))
        self.inp_bb = QLineEdit()
        self.inp_bb.setFixedHeight(45)
        self.inp_bb.setText(str(profil.get("weight", "")))
        v2.addWidget(self.inp_bb)

        v3 = QVBoxLayout()
        v3.addWidget(lbl_blk("TB (cm)"))
        self.inp_tb = QLineEdit()
        self.inp_tb.setFixedHeight(45)
        self.inp_tb.setText(str(profil.get("height", "")))
        v3.addWidget(self.inp_tb)
        
        row.addLayout(v1)
        row.addLayout(v2)
        row.addLayout(v3)
        card_layout.addLayout(row)
        
        card_layout.addSpacing(5)


        combo_style = '''
            QComboBox {
                border: none;
                border-radius: 16px;
                padding: 5px 10px;
                background: rgba(26, 122, 52, 0.25);
                color: #1A7A34;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border: none;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #1A7A34;
                border-radius: 0px;
                background-color: white;
                outline: 0px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 40px;
                padding-left: 10px;
                color: #555555;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: rgba(26, 122, 52, 0.15);
                color: #1A7A34;
            }
        '''

        card_layout.addWidget(lbl_blk("Aktivitas"))
        self.inp_akt = QComboBox()
        self.inp_akt.setView(QListView())
        self.inp_akt.addItems(["Sedentary (Jarang Olahraga)", "Ringan", "Sedang", "Berat"])
        self.inp_akt.setCurrentText(profil.get("activity", "Sedentary (Jarang Olahraga)"))
        self.inp_akt.setFixedHeight(45)
        self.inp_akt.setStyleSheet(combo_style)
        card_layout.addWidget(self.inp_akt)

        card_layout.addWidget(lbl_blk("Tujuan Diet"))
        self.inp_diet = QComboBox()
        self.inp_diet.setView(QListView())
        self.inp_diet.addItems(["Maintain Berat Badan", "Turun Berat Badan", "Naik Berat Badan"])
        self.inp_diet.setCurrentText(profil.get("diet_goal", "Maintain Berat Badan"))
        self.inp_diet.setFixedHeight(45)
        self.inp_diet.setStyleSheet(combo_style)
        card_layout.addWidget(self.inp_diet)

        # Password Baru (Optional)
        card_layout.addWidget(lbl_blk("Password Baru (Kosongkan jika tidak diubah)"))
        self.inp_pwd = QLineEdit()
        self.inp_pwd.setFixedHeight(45)
        self.inp_pwd.setEchoMode(QLineEdit.Password)
        self.inp_pwd.setPlaceholderText("Masukkan password baru")
        card_layout.addWidget(self.inp_pwd)

        card_layout.addStretch()

        btns = QHBoxLayout()
        btn_batal = QPushButton("Batal")
        btn_batal.setFixedHeight(50)
        btn_batal.setCursor(Qt.PointingHandCursor)
        btn_batal.setStyleSheet(
            "QPushButton { background-color: white; color: rgba(26, 122, 52, 0.5); "
            "border: 1px solid #1A7A34; border-radius: 25px; font-size: 16px; font-weight: bold; } "
            "QPushButton:hover { color: #1A7A34; }"
        )
        btn_batal.clicked.connect(self.reject)

        btn_simpan = QPushButton("Simpan")
        btn_simpan.setFixedHeight(50)
        btn_simpan.setCursor(Qt.PointingHandCursor)
        btn_simpan.setStyleSheet(
            "QPushButton { background-color: #1A7A34; color: white; "
            "border-radius: 25px; font-weight: bold; font-size: 16px; }"
        )
        btn_simpan.clicked.connect(self._simpan)

        btns.addWidget(btn_batal)
        btns.addWidget(btn_simpan)
        
        card_layout.addLayout(btns)
        main_layout.addWidget(self.card)

    def resizeEvent(self, event):
        if self.parent():
            self.resize(self.parent().size())
        super().resizeEvent(event)

    def _simpan(self):
        try:
            nama = self.inp_nama.text().strip()
            if not nama:
                show_toast(self, "Nama tidak boleh kosong!", TOAST_ERROR)
                return
            
            bb = float(self.inp_bb.text() or 0)
            tb = float(self.inp_tb.text() or 0)
            usia = int(self.inp_usia.text() or 0)
            akt = self.inp_akt.currentText()
            jk = self.sistem.current_profil.get("gender", "Perempuan")
            
            calc = self.sistem.calculatorHarrisBenedict(jk, bb, tb, usia, akt)
            if calc is None: calc = 2100

            data = {
                'full_name': nama,
                'age': usia,
                'weight': bb,
                'height': tb,
                'activity': akt,
                'diet_goal': self.inp_diet.currentText(),
                'calory': calc
            }

            pwd = self.inp_pwd.text().strip()
            if pwd:
                if len(pwd) < 6:
                    show_toast(self, "Password baru minimal 6 karakter!", TOAST_ERROR)
                    return
                data['password'] = self.sistem._hash_password(pwd)

            if self.sistem.updateProfil(data):
                show_toast(self, "Update data berhasil!", TOAST_SUCCESS)
                self.accept()
            else:
                show_toast(self, "Gagal update profile!", TOAST_ERROR)
        except ValueError:
             show_toast(self, "Usia, BB, TB harus angka!", TOAST_ERROR)

class LogoutConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("OverlayDialog")
        self.setStyleSheet("#OverlayDialog { background-color: rgba(0, 0, 0, 120); }")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignCenter)
        
        self.card = QFrame()
        self.card.setFixedSize(420, 280)
        self.card.setStyleSheet("""
            QFrame { background: white; border-radius: 25px; border: none; }
            QLabel { border: none; background: transparent; color: #555555; font-family: 'Poppins'; }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 10)
        self.card.setGraphicsEffect(shadow)

        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(35, 35, 35, 35)
        card_layout.setSpacing(20)

        title = QLabel("Konfirmasi Keluar")
        title.setFont(QFont('Poppins', 16, QFont.Bold))
        title.setStyleSheet("color: #1A7A34;")
        card_layout.addWidget(title)

        message = QLabel("Apakah Anda yakin ingin keluar?")
        message.setFont(QFont('Poppins', 12))
        message.setWordWrap(True)
        message.setStyleSheet("line-height: 150%;")
        card_layout.addWidget(message)

        card_layout.addStretch()


        btns = QHBoxLayout()
        btns.setSpacing(15)
        
        btn_batal = QPushButton("Batal")
        btn_batal.setFixedHeight(50)
        btn_batal.setCursor(Qt.PointingHandCursor)
        btn_batal.setStyleSheet(
            "QPushButton { background-color: white; color: #1A7A34; "
            "border: 2px solid #1A7A34; border-radius: 25px; font-size: 16px; font-weight: bold; } "
            "QPushButton:hover { background-color: #f0fdf4; }"
        )
        btn_batal.clicked.connect(self.reject)

        btn_keluar = QPushButton("Ya, Keluar")
        btn_keluar.setFixedHeight(50)
        btn_keluar.setCursor(Qt.PointingHandCursor)
        btn_keluar.setStyleSheet(
            "QPushButton { background-color: #1A7A34; color: white; "
            "border-radius: 25px; font-weight: bold; font-size: 16px; }"
            "QPushButton:hover { background-color: #145925; }"
        )
        btn_keluar.clicked.connect(self.accept)


        btns.addWidget(btn_batal)
        btns.addWidget(btn_keluar)
        
        card_layout.addLayout(btns)
        main_layout.addWidget(self.card)

    def resizeEvent(self, event):
        if self.parent():
            self.resize(self.parent().size())
        super().resizeEvent(event)

class EmailSenderWorker(QThread):
    finished = pyqtSignal(bool, str) # Emits (success, error_message)

    def __init__(self, sistem, email, temp_password):
        super().__init__()
        self.sistem = sistem
        self.email = email
        self.temp_password = temp_password

    def run(self):
        try:
            # 1. Update password di SQLite/Mock DB terlebih dahulu
            db_success = self.sistem.resetPasswordByEmail(self.email, self.temp_password)
            if not db_success:
                self.finished.emit(False, "Gagal meriset password di database. Silakan coba lagi.")
                return

            # 2. Kirim email secara real-time via SMTP
            email_sender.send_reset_email(self.email, self.temp_password)
            self.finished.emit(True, "Email berhasil dikirim!")
        except Exception as e:
            self.finished.emit(False, str(e))

class EmailSendingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("SendingOverlay")
        self.setStyleSheet("#SendingOverlay { background-color: rgba(0, 0, 0, 150); }")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignCenter)
        
        card = QFrame()
        card.setFixedSize(300, 200)
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 20px;
                border: none;
            }
            QLabel {
                color: #333333;
                font-family: 'Poppins';
                background: transparent;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        card.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        # Loading indicator (pulse text or dot animations)
        self.spinner_lbl = QLabel("⏳")
        self.spinner_lbl.setFont(QFont('Poppins', 28))
        self.spinner_lbl.setAlignment(Qt.AlignCenter)
        
        self.msg_lbl = QLabel("Mengirim email...")
        self.msg_lbl.setFont(QFont('Poppins', 12, QFont.Bold))
        self.msg_lbl.setStyleSheet("color: #1A7A34;")
        self.msg_lbl.setAlignment(Qt.AlignCenter)
        
        self.sub_lbl = QLabel("Mohon tunggu sebentar...")
        self.sub_lbl.setFont(font_body(9))
        self.sub_lbl.setStyleSheet("color: #777777;")
        self.sub_lbl.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.spinner_lbl)
        layout.addWidget(self.msg_lbl)
        layout.addWidget(self.sub_lbl)
        
        main_layout.addWidget(card)

    def resizeEvent(self, event):
        if self.parent():
            self.resize(self.parent().size())
        super().resizeEvent(event)

class EmailConfigGuideDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("GuideOverlay")
        self.setStyleSheet("#GuideOverlay { background-color: rgba(0, 0, 0, 150); }")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignCenter)
        
        self.card = QFrame()
        self.card.setFixedSize(520, 480)
        self.card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 25px;
                border: none;
            }
            QLabel {
                border: none;
                background: transparent;
                color: #444444;
                font-family: 'Poppins';
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 8)
        self.card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(35, 30, 35, 30)
        card_layout.setSpacing(12)
        
        # Header
        title = QLabel("Konfigurasi Email Pengirim")
        title.setFont(QFont('Poppins', 16, QFont.Bold))
        title.setStyleSheet("color: #1A7A34;")
        card_layout.addWidget(title)
        
        sub = QLabel("Untuk mengirim email reset password secara nyata, Anda perlu menyetting email pengirim (SMTP) terlebih dahulu.")
        sub.setFont(font_body(9))
        sub.setStyleSheet("color: #666666;")
        sub.setWordWrap(True)
        card_layout.addWidget(sub)
        
        # Line divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #f0f0f0;")
        card_layout.addWidget(line)
        
        # Steps
        steps = QLabel(
            "<b>Langkah Setup Gmail SMTP:</b><br>"
            "1. Buka <b>Google Account</b> Anda.<br>"
            "2. Aktifkan <b>2-Step Verification (Verifikasi 2 Langkah)</b> di tab Keamanan.<br>"
            "3. Cari menu <b>App Passwords (Sandi Aplikasi)</b>.<br>"
            "4. Buat sandi aplikasi baru (pilih Kategori 'Lainnya' dan beri nama 'Nutri-Kost').<br>"
            "5. Salin 16-karakter sandi yang muncul.<br>"
            "6. Klik tombol di bawah untuk membuka file konfigurasi, lalu ganti email & password dengan email dan sandi aplikasi Anda."
        )
        steps.setFont(font_body(10))
        steps.setWordWrap(True)
        steps.setStyleSheet("line-height: 150%; color: #333333;")
        card_layout.addWidget(steps)
        
        card_layout.addStretch()
        
        # Buttons
        btns = QVBoxLayout()
        btns.setSpacing(10)
        
        btn_open = QPushButton("📂  Buka File Konfigurasi (email_config.json)")
        btn_open.setFixedHeight(48)
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.setStyleSheet("""
            QPushButton {
                background-color: #1A7A34;
                color: white;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #145925;
            }
        """)
        btn_open.clicked.connect(self._open_config_file)
        
        btn_tutup = QPushButton("Tutup")
        btn_tutup.setFixedHeight(44)
        btn_tutup.setCursor(Qt.PointingHandCursor)
        btn_tutup.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: 1px solid #cccccc;
                border-radius: 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f9f9f9;
                color: #555555;
            }
        """)
        btn_tutup.clicked.connect(self.reject)
        
        btns.addWidget(btn_open)
        btns.addWidget(btn_tutup)
        card_layout.addLayout(btns)
        
        main_layout.addWidget(self.card)

    def _open_config_file(self):
        # Membuat file config jika belum ada
        email_sender.load_config()
        # Membuka file menggunakan program default (Notepad/VS Code/dll)
        try:
            os.startfile(email_sender.CONFIG_PATH)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Gagal membuka file: {e}")

    def resizeEvent(self, event):
        if self.parent():
            self.resize(self.parent().size())
        super().resizeEvent(event)

class ForgotPasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.email_value = ""
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("OverlayDialog")
        self.setStyleSheet("#OverlayDialog { background-color: rgba(0, 0, 0, 120); }")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignCenter)
        
        self.card = QFrame()
        self.card.setFixedSize(420, 320)
        self.card.setStyleSheet("""
            QFrame { background: white; border-radius: 25px; border: none; }
            QLabel { border: none; background: transparent; color: #555555; font-family: 'Poppins'; }
            QLineEdit { border: none; border-radius: 20px; padding-left: 15px; background: rgba(26, 122, 52, 0.1); color: #1A7A34; }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 10)
        self.card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(35, 35, 35, 35)
        card_layout.setSpacing(15)

        title = QLabel("Lupa Password")
        title.setFont(QFont('Poppins', 16, QFont.Bold))
        title.setStyleSheet("color: #1A7A34;")
        card_layout.addWidget(title)

        message = QLabel("Masukkan email Anda untuk reset password:")
        message.setFont(QFont('Poppins', 10))
        message.setWordWrap(True)
        card_layout.addWidget(message)

        self.inp_email = QLineEdit()
        self.inp_email.setFixedHeight(45)
        self.inp_email.setPlaceholderText("yourname@mail.com")
        card_layout.addWidget(self.inp_email)

        card_layout.addStretch()

        btns = QHBoxLayout()
        btns.setSpacing(15)
        
        btn_batal = QPushButton("Batal")
        btn_batal.setFixedHeight(50)
        btn_batal.setCursor(Qt.PointingHandCursor)
        btn_batal.setStyleSheet(
            "QPushButton { background-color: white; color: #1A7A34; "
            "border: 2px solid #1A7A34; border-radius: 25px; font-size: 16px; font-weight: bold; } "
            "QPushButton:hover { background-color: #f0fdf4; }"
        )
        btn_batal.clicked.connect(self.reject)

        btn_kirim = QPushButton("Kirim")
        btn_kirim.setFixedHeight(50)
        btn_kirim.setCursor(Qt.PointingHandCursor)
        btn_kirim.setStyleSheet(
            "QPushButton { background-color: #1A7A34; color: white; "
            "border-radius: 25px; font-weight: bold; font-size: 16px; }"
            "QPushButton:hover { background-color: #145925; }"
        )
        btn_kirim.clicked.connect(self._handle_kirim)

        btns.addWidget(btn_batal)
        btns.addWidget(btn_kirim)
        
        card_layout.addLayout(btns)
        main_layout.addWidget(self.card)

    def _handle_kirim(self):
        self.email_value = self.inp_email.text().strip()
        self.accept()

    def resizeEvent(self, event):
        if self.parent():
            self.resize(self.parent().size())
        super().resizeEvent(event)


# ==========================================
# MAIN DASHBOARD / PROFILE 
# ==========================================
class ProfilApp(QWidget):
    PAGE_NAME = 'Profile'
    PAGE_DESC = 'Data diri dan target nutrisi harianmu'
    NAV_INDEX = 5

    logout_signal = pyqtSignal()
    refresh_me = pyqtSignal()
    go_back = pyqtSignal()

    def __init__(self, sistem: ProfilSystem):
        super().__init__()
        self._sistem = sistem

        self.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        self.build_content(layout)

    def _aksi_logout(self):
        dlg = LogoutConfirmDialog(self.window())
        dlg.setGeometry(0, 0, self.window().width(), self.window().height())
        if dlg.exec_() == QDialog.Accepted:
            self._sistem.current_profil = None
            self.logout_signal.emit()



    def build_content(self, layout: QVBoxLayout):
        profil = self._sistem.current_profil or {}
        
        # Top Header Area
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        
        
        header_text_layout = QVBoxLayout()

        header_text_layout.setSpacing(2)
        profile_title = QLabel("Profile")
        profile_title.setFont(QFont('Montserrat Alternates SemiBold', 24))
        profile_title.setStyleSheet(f"color: {C_TEXT_DARK}; background: transparent;")
        
        profile_desc = QLabel("Data diri dan target nutrisi harianmu")
        profile_desc.setFont(font_body(11))
        profile_desc.setStyleSheet(f"color: {C_TEXT_SUB}; background: transparent;")
        
        header_text_layout.addWidget(profile_title)
        header_text_layout.addWidget(profile_desc)
        top_row.addLayout(header_text_layout)
        
        top_row.addStretch()
        
        self.btn_edit = QPushButton("  Edit Profile")
        self.btn_edit.setFixedSize(180, 52)
        self.btn_edit.setCursor(Qt.PointingHandCursor)
        # Attempt to use a generic edit icon if available, otherwise just text
        edit_icon_path = os.path.join(ICONS_DIR, 'solar_pen-new-square-bold.png')
        if os.path.exists(edit_icon_path):
            self.btn_edit.setIcon(QIcon(edit_icon_path))
            self.btn_edit.setIconSize(QSize(20, 20))
        
        self.btn_edit.setFont(font_label(10, bold=True))
        self.btn_edit.setStyleSheet(f"""
            QPushButton {{
                background-color: {GREEN_PRIMARY};
                color: white;
                border-radius: 12px;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {C_NAVBAR_HVR};
            }}
        """)
        top_row.addWidget(self.btn_edit)

        self.btn_keluar = QPushButton("Keluar")
        self.btn_keluar.setFixedSize(120, 52)
        self.btn_keluar.setCursor(Qt.PointingHandCursor)
        self.btn_keluar.setFont(font_label(10, bold=True))
        self.btn_keluar.setStyleSheet(f"""
            QPushButton {{
                background-color: #E03030;
                color: white;
                border-radius: 12px;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: #B71C1C;
            }}
        """)
        self.btn_keluar.clicked.connect(self._aksi_logout)
        top_row.addWidget(self.btn_keluar)
        
        # Insert top_row at the beginning of the layout
        layout.insertLayout(0, top_row)
        
        self.btn_edit.clicked.connect(self._go_to_edit)
        
        # Data area row
        content_row = QHBoxLayout()
        content_row.setSpacing(24)
        content_row.setContentsMargins(0, 4, 0, 0)

        # --- LEFT CARD: Avatar & Stats ---
        left_card = QFrame()
        left_card.setFixedWidth(420)
        left_card.setStyleSheet("QFrame { background-color: white; border-radius: 16px; border: none; }")
        
        # Add slight shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 15))
        left_card.setGraphicsEffect(shadow)
        
        lc_lay = QVBoxLayout(left_card)
        lc_lay.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        lc_lay.setContentsMargins(24, 24, 24, 24)
        lc_lay.setSpacing(12)

        # Avatar circle
        av = QLabel()
        
        icon_path = os.path.join(ICONS_DIR, 'gg_profile.png')
        av_pix = QPixmap(icon_path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Colorize the icon to GREEN_PRIMARY
        painter = QPainter(av_pix)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(av_pix.rect(), QColor(GREEN_PRIMARY))
        painter.end()
        
        av.setPixmap(av_pix)
        av.setStyleSheet("background: transparent;")
        av.setFixedSize(130, 130)
        av.setAlignment(Qt.AlignCenter)
        lc_lay.addWidget(av, alignment=Qt.AlignCenter)
        
        lc_lay.addSpacing(16)
        
        profil = self._sistem.current_profil or {}
        p_name = profil.get("full_name", "Unknown")
        p_email = profil.get("email", "unknown@mail.com")

        name_lbl = QLabel(p_name)
        name_lbl.setFont(QFont('Montserrat Alternates SemiBold', 20))
        name_lbl.setStyleSheet(f"color: {C_TEXT_DARK};")
        name_lbl.setWordWrap(True)  # Enable wrap for long names
        name_lbl.setAlignment(Qt.AlignCenter)
        lc_lay.addWidget(name_lbl, alignment=Qt.AlignCenter)

        email_lbl = QLabel(p_email)
        email_lbl.setFont(font_body(10))
        email_lbl.setStyleSheet(f"color: {C_TEXT_SUB};")
        email_lbl.setWordWrap(True)
        email_lbl.setAlignment(Qt.AlignCenter)
        lc_lay.addWidget(email_lbl, alignment=Qt.AlignCenter)

        lc_lay.addSpacing(16)
        
        # Stats row
        st_row = QFrame()
        st_row.setStyleSheet(f"background-color: {GREEN_LIGHT}; border-radius: 12px; border: none;")
        st_l = QHBoxLayout(st_row)
        st_l.setContentsMargins(20, 12, 20, 12)
        st_l.setSpacing(15)

        val_bb = profil.get("weight", 0)
        val_tb = profil.get("height", 0)

        def set_st(val, lbl):
            vbox = QVBoxLayout()
            vbox.setSpacing(2)
            v = QLabel(str(val))
            v.setFont(QFont('Montserrat Alternates SemiBold', 18))
            v.setStyleSheet(f"color: {GREEN_DARK}; background: transparent;")
            l = QLabel(lbl)
            l.setFont(font_label(8, bold=True))
            l.setStyleSheet(f"color: {GREEN_DARK}; background: transparent; opacity: 0.8;")
            vbox.addWidget(v, alignment=Qt.AlignCenter)
            vbox.addWidget(l, alignment=Qt.AlignCenter)
            st_l.addLayout(vbox)

        # Dynamic BMI Badge Calculator
        bmi_status_str = "Error BMI"
        try:
             bmi_status_str = self._sistem.calculatorBMI(float(val_bb), float(val_tb))
             if bmi_status_str is None: bmi_status_str = "BMI Kosong"
        except:
             pass

        status_word = ""
        bmi_num = 0
        if "(" in bmi_status_str:
             bmi_num = bmi_status_str.split(" (")[0]
             status_word = bmi_status_str.split(" (")[1].replace(")", "")
             
        badge_color = GREEN_LIGHT
        text_color = GREEN_DARK
        
        if "Kurus" in status_word or "Obesitas" in status_word:
            badge_color = "#FFEBEB" # Light red
            text_color = "#D32F2F"  # Dark red
        elif "Gemuk" in status_word:
            badge_color = "#FFF5E6" # Light orange
            text_color = "#E65100"  # Orange

        set_st(val_bb, "kg BB")
        set_st(val_tb, "cm TB")
        set_st(bmi_num, "BMI")
        lc_lay.addWidget(st_row)

        lc_lay.addSpacing(8)
        norm_badge = QLabel(f"✓ Berat Badan {status_word}" if status_word else bmi_status_str)
        norm_badge.setFixedHeight(34)
        norm_badge.setAlignment(Qt.AlignCenter)
        norm_badge.setFont(font_label(9, bold=True))
        norm_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {badge_color};
                color: {text_color};
                padding: 0 16px;
                border-radius: 10px;
            }}
        """)
        lc_lay.addWidget(norm_badge, alignment=Qt.AlignCenter)
        lc_lay.addStretch()


        # --- RIGHT COLUMN: List Data ---
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        def make_list_card(title, data_dict):
            f = QFrame()
            f.setStyleSheet("QFrame { background-color: white; border-radius: 16px; border: none; }")
            
            sh2 = QGraphicsDropShadowEffect()
            sh2.setBlurRadius(20)
            sh2.setXOffset(0)
            sh2.setYOffset(4)
            sh2.setColor(QColor(0, 0, 0, 15))
            f.setGraphicsEffect(sh2)
            
            fl = QVBoxLayout(f)
            fl.setContentsMargins(20, 16, 20, 16)
            fl.setSpacing(2)
            
            t = QLabel(title)
            t.setFont(QFont('Montserrat Alternates Medium', 12))
            t.setStyleSheet(f"color: {C_TEXT_DARK}; margin-bottom: 12px; padding: 0;")
            fl.addWidget(t)
            
            for k, v in data_dict.items():
                r = QHBoxLayout()
                r.setContentsMargins(0, 4, 0, 4)
                lbl1 = QLabel(k)
                lbl1.setFont(font_label(10))
                lbl1.setStyleSheet(f"color: {GREEN_PRIMARY};")
                lbl2 = QLabel(v)
                lbl2.setFont(font_label(10, bold=True))
                lbl2.setStyleSheet(f"color: {GREEN_PRIMARY};")
                lbl2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                r.addWidget(lbl1)
                r.addStretch()
                r.addWidget(lbl2)
                
                fl.addLayout(r)
                div = QFrame()
                div.setFrameShape(QFrame.HLine)
                div.setStyleSheet("background-color: #DCDCDC; border: none;")
                div.setFixedHeight(1)
                fl.addWidget(div)
            return f

        aktivitas = profil.get("activity", "Sedentary (Jarang Olahraga)")
        
        usia_val = profil.get("age", 20)
        jk_val = profil.get("gender", "Perempuan")
        calc = self._sistem.calculatorHarrisBenedict(jk_val, float(val_bb), float(val_tb), int(usia_val), aktivitas)
        target_cal = calc if calc is not None else profil.get("calory", 2100)
        
        tujuan_diet = profil.get("diet_goal", "Maintain Berat Badan")

        d_diri = {
            "Nama Lengkap": profil.get("full_name", "-"),
            "Usia": f"{profil.get('age', '-')} Tahun",
            "Jenis Kelamin": profil.get("gender", "-"),
            "Berat Badan": f"{val_bb} kg",
            "Tinggi Badan": f"{val_tb} cm",
            "Aktivitas": aktivitas
        }
        
        akg_user = self._sistem.getAKGUser() or {}
        tar_pro = akg_user.get("protein", 75)
        tar_kar = akg_user.get("carb", 325)
        tar_lem = akg_user.get("fat", 70)
        
        d_target = {
            "Target Kalori": f"{target_cal} kkal",
            "Target Protein": f"{tar_pro}g",
            "Target Karbohidrat": f"{tar_kar}g",
            "Target Lemak": f"{tar_lem}g",
            "Tujuan Diet": tujuan_diet
        }

        right_col.addWidget(make_list_card("Data Diri", d_diri))
        right_col.addWidget(make_list_card("Target Harian", d_target))
        right_col.addStretch()

        content_row.addWidget(left_card, 1)
        content_row.addLayout(right_col, 1)

        layout.addLayout(content_row)
        layout.addStretch()


    def _go_to_edit(self):
        dlg = EditProfileDialog(self._sistem, self.window())
        dlg.setGeometry(0, 0, self.window().width(), self.window().height())
        if dlg.exec_() == QDialog.Accepted:
            self.refresh_me.emit()


# ==========================================
# MAIN APP STACK
# ==========================================
class MainApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        load_fonts()
        self.setWindowTitle("NutriKost")
        self.resize(1200, 720)
        self._sistem = ProfilSystem()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.init_auth_flow()
        
        # Selalu tampilkan halaman login di awal (jangan auto-login)
        self.show_login()

    def init_auth_flow(self):
        # Create auth pages inside their wrapper
        self.login_p = HalamanLogin(self._sistem)
        self.register_p = HalamanRegister(self._sistem)
        self.datadiri_p = HalamanDataDiri(self._sistem)

        self.login_wrapper = AuthBaseWidget(self.login_p)
        self.register_wrapper = AuthBaseWidget(self.register_p)
        self.datadiri_wrapper = AuthBaseWidget(self.datadiri_p)

        self.login_p.go_register.connect(self.show_register)
        self.login_p.login_success.connect(self.show_dashboard)
        self.login_p.go_back.connect(self.show_login) # Or exit? For now just stay on login
        
        self.register_p.go_datadiri.connect(self.show_datadiri)
        self.register_p.go_back.connect(self.show_login)
        
        self.datadiri_p.register_success.connect(self.show_dashboard)
        self.datadiri_p.go_back.connect(self.show_register_simple) # Need a helper to show register without clearing it if possible, but stack is fine

        # 0
        self.stack.addWidget(self.login_wrapper)
        # 1
        self.stack.addWidget(self.register_wrapper)
        # 2
        self.stack.addWidget(self.datadiri_wrapper)

    def show_login(self):
        self.stack.setCurrentWidget(self.login_wrapper)
        
    def show_register(self):
        self.stack.setCurrentWidget(self.register_wrapper)

    def show_datadiri(self, data):
        self.datadiri_p.register_data = data
        self.stack.setCurrentWidget(self.datadiri_wrapper)

    def show_register_simple(self):
        self.stack.setCurrentWidget(self.register_wrapper)

    def show_dashboard(self):
        self.dashboard = ProfilApp(self._sistem)
        self.dashboard.logout_signal.connect(self.show_login)
        self.dashboard.refresh_me.connect(self.refresh_dashboard)
        
        # 3
        self.stack.addWidget(self.dashboard)
        self.stack.setCurrentWidget(self.dashboard)

    def refresh_dashboard(self):
        idx = self.stack.indexOf(self.dashboard)
        self.stack.removeWidget(self.dashboard)
        self.dashboard.deleteLater()
        
        self.dashboard = ProfilApp(self._sistem)
        self.dashboard.logout_signal.connect(self.show_login)
        self.dashboard.refresh_me.connect(self.refresh_dashboard)
        self.stack.insertWidget(idx, self.dashboard)
        self.stack.setCurrentIndex(idx)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    app.setStyleSheet("""
        QMessageBox {
            background-color: white;
        }
        QMessageBox QLabel {
            color: #333333;
            background-color: transparent;
        }
        QMessageBox QPushButton {
            background-color: #1A7A34;
            color: white;
            border-radius: 4px;
            padding: 5px 15px;
            min-width: 60px;
        }
        QMessageBox QPushButton:hover {
            background-color: #145925;
        }
    """)
    
    window = MainApplication()
    window.show()
    sys.exit(app.exec_())