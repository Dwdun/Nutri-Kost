import csv
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QMessageBox, QFileDialog,
    QScrollArea, QSizePolicy, QTimeEdit, QSpinBox, QDialog
)
from PyQt5.QtCore import Qt, QSettings, QPropertyAnimation, pyqtProperty, QEasingCurve, QTime
from PyQt5.QtGui import QFont, QPainter, QColor
from fatih_GUI.toast_notification import show_toast, TOAST_SUCCESS, TOAST_ERROR, TOAST_NORMAL

ACCENT_GREEN  = "#1A7A34"
CONTENT_BG    = "#f5f7f5"
CARD_BG       = "#ffffff"
TEXT_MAIN     = "#1a1a1a"
TEXT_SUB      = "#6b7280"
BORDER_COLOR  = "#e5e7eb"
RED_DANGER    = "#dc2626"
RED_HOVER     = "#b91c1c"


# ── Widget toggle on/off ──────────────────────────────────────────────────────
class ToggleSwitch(QPushButton):

    #inisialisasi tombol toggle
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(52, 28)
        self.setCursor(Qt.PointingHandCursor)
        self._position = 0
        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.setDuration(200)
        self.toggled.connect(self.setup_animation)

    @pyqtProperty(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos
        self.update()

    def setup_animation(self, value):
        self.animation.stop()
        self.animation.setEndValue(1.0 if value else 0.0)
        self.animation.start()

    def setChecked(self, checked):
        super().setChecked(checked)
        self._position = 1.0 if checked else 0.0
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        track_color = QColor("#1A7A34") if self.isChecked() else QColor("#e5e7eb")
        painter.setBrush(track_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)

        # Thumb
        thumb_color = QColor("#ffffff")
        thumb_radius = self.height() - 4
        
        # Calculate thumb position
        travel = self.width() - thumb_radius - 4
        x = 2 + travel * self._position
        y = 2
        
        # Draw shadow
        painter.setBrush(QColor(0, 0, 0, 30))
        painter.drawEllipse(int(x), int(y) + 1, thumb_radius, thumb_radius)
        
        # Draw thumb
        painter.setBrush(thumb_color)
        painter.drawEllipse(int(x), int(y), thumb_radius, thumb_radius)
        
        painter.end()


# ── Card Settings ────────────────────
class SettingItem(QFrame):

    #inisialisasi card
    def __init__(self, title: str, description: str, action_widget: QWidget, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border-radius: 10px;
                border: 1px solid {BORDER_COLOR};
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # Teks kiri
        text_col = QVBoxLayout()
        text_col.setSpacing(3)

        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Montserrat", 11, QFont.Bold))
        lbl_title.setStyleSheet(f"color: {TEXT_MAIN}; border: none; background: transparent;")

        lbl_desc = QLabel(description)
        lbl_desc.setFont(QFont("Montserrat", 9))
        lbl_desc.setStyleSheet(f"color: {TEXT_SUB}; border: none; background: transparent;")
        lbl_desc.setWordWrap(True)

        text_col.addWidget(lbl_title)
        text_col.addWidget(lbl_desc)

        layout.addLayout(text_col, stretch=1)
        layout.addWidget(action_widget, alignment=Qt.AlignVCenter | Qt.AlignRight)


# ── Section header ────────────────────────────────
def _make_section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont("Montserrat", 11, QFont.Bold))
    lbl.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
    lbl.setContentsMargins(4, 0, 0, 0)
    return lbl


# ── Halaman Pengaturan ────────────────────────────────────────────────────────
class SettingPage(QWidget):

    def __init__(self, sistem_profil=None, parent=None):
        super().__init__(parent)
        self.sistem_profil = sistem_profil
        self.setStyleSheet(f"background-color: {CONTENT_BG};")

        # QSettings untuk menyimpan preferensi notifikasi
        self._settings = QSettings("NutriKost", "Pengaturan")

        # Lazy-load DBHelper (sama seperti modul lain)
        try:
            from models import DBHelper
            self._db = DBHelper()
        except ImportError:
            self._db = None

        self._build_ui()
        self._load_preferences()

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Scroll area agar konten tidak terpotong di layar kecil
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(32, 28, 32, 32)
        main_layout.setSpacing(8)
        main_layout.setAlignment(Qt.AlignTop)

        # ── Judul halaman ─────────────────────────────────────────────────────
        lbl_title = QLabel("Pengaturan")
        lbl_title.setFont(QFont("Montserrat Alternates", 32, QFont.Bold))
        lbl_title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent; font-family: 'Montserrat Alternates'; font-size: 32px; font-weight: bold;")

        lbl_sub = QLabel("Sesuaikan preferensi aplikasimu")
        lbl_sub.setFont(QFont("Montserrat", 10))
        lbl_sub.setStyleSheet(f"color: {TEXT_SUB}; background: transparent; font-family: 'Montserrat'; font-size: 14px;")

        main_layout.addWidget(lbl_title)
        main_layout.addWidget(lbl_sub)
        main_layout.addSpacing(16)

        # ── Seksi Notifikasi ──────────────────────────────────────────────────
        main_layout.addWidget(_make_section_label("Notifikasi"))
        main_layout.addSpacing(6)

        self._toggle_makan   = ToggleSwitch()
        self._toggle_kalori  = ToggleSwitch()

        # Hubungkan toggle ke handler penyimpanan preferensi
        self._toggle_makan.toggled.connect(
            lambda val: self._save_preference("notif_makan", val)
        )
        self._toggle_kalori.toggled.connect(
            lambda val: self._save_preference("notif_kalori", val)
        )

        main_layout.addWidget(SettingItem(
            "Pengingat Makan",
            "Ingatkan saat waktunya Sarapan, Makan Siang, Makan Malam",
            self._toggle_makan
        ))
        
        # Detail Pengingat Makan
        self._makan_details = QWidget()
        makan_layout = QVBoxLayout(self._makan_details)
        makan_layout.setContentsMargins(40, 0, 20, 10)
        
        def create_time_picker(label_text):
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFont(QFont("Montserrat", 10))
            lbl.setStyleSheet(f"color: {TEXT_SUB};")
            te = QTimeEdit()
            te.setDisplayFormat("HH:mm")
            te.setStyleSheet(f"QTimeEdit {{ border: 1px solid {BORDER_COLOR}; border-radius: 4px; padding: 4px; background: {CARD_BG}; color: {TEXT_MAIN}; }}")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(te)
            return row, te

        row_sarapan, self._time_sarapan = create_time_picker("Sarapan")
        row_siang, self._time_siang = create_time_picker("Makan Siang")
        row_malam, self._time_malam = create_time_picker("Makan Malam")
        
        makan_layout.addLayout(row_sarapan)
        makan_layout.addLayout(row_siang)
        makan_layout.addLayout(row_malam)
        
        self._time_sarapan.timeChanged.connect(lambda t: self._save_preference("waktu_sarapan", t.toString("HH:mm")))
        self._time_siang.timeChanged.connect(lambda t: self._save_preference("waktu_siang", t.toString("HH:mm")))
        self._time_malam.timeChanged.connect(lambda t: self._save_preference("waktu_malam", t.toString("HH:mm")))
        
        self._time_sarapan.editingFinished.connect(lambda: self._show_time_notification("Sarapan", self._time_sarapan))
        self._time_siang.editingFinished.connect(lambda: self._show_time_notification("Makan Siang", self._time_siang))
        self._time_malam.editingFinished.connect(lambda: self._show_time_notification("Makan Malam", self._time_malam))
        
        main_layout.addWidget(self._makan_details)
        self._toggle_makan.toggled.connect(self._makan_details.setVisible)

        main_layout.addSpacing(8)
        
        main_layout.addWidget(SettingItem(
            "Peringatan Kalori",
            "Notifikasi jika kalori mendekati atau melebihi batas",
            self._toggle_kalori
        ))
        
        # Detail Peringatan Kalori
        self._kalori_details = QWidget()
        kalori_layout = QVBoxLayout(self._kalori_details)
        kalori_layout.setContentsMargins(40, 0, 20, 10)
        
        row_kalori = QHBoxLayout()
        lbl_batas = QLabel("Batas Maksimal Kalori")
        lbl_batas.setFont(QFont("Montserrat", 10))
        lbl_batas.setStyleSheet(f"color: {TEXT_SUB};")
        
        self._spin_batas = QSpinBox()
        self._spin_batas.setRange(50, 150)
        self._spin_batas.setSingleStep(5)
        self._spin_batas.setSuffix(" %")
        self._spin_batas.setStyleSheet(f"QSpinBox {{ border: 1px solid {BORDER_COLOR}; border-radius: 4px; padding: 4px; background: {CARD_BG}; color: {TEXT_MAIN}; width: 60px; }}")
        
        row_kalori.addWidget(lbl_batas)
        row_kalori.addStretch()
        row_kalori.addWidget(self._spin_batas)
        
        kalori_layout.addLayout(row_kalori)
        
        self._lbl_keterangan_kalori = QLabel("Setara dengan: - kkal")
        font_ket = QFont("Montserrat", 9)
        font_ket.setItalic(True)
        self._lbl_keterangan_kalori.setFont(font_ket)
        self._lbl_keterangan_kalori.setStyleSheet("color: #059669;") # Greenish
        kalori_layout.addWidget(self._lbl_keterangan_kalori)
        
        self._spin_batas.valueChanged.connect(self._on_batas_changed)
        
        main_layout.addWidget(self._kalori_details)
        self._toggle_kalori.toggled.connect(self._kalori_details.setVisible)

        main_layout.addSpacing(20)

        # ── Section Data ────────────────────────────────────────────────────────
        main_layout.addWidget(_make_section_label("Data"))
        main_layout.addSpacing(6)

        # Tombol Export
        btn_export = QPushButton("  Export Data")
        btn_export.setFixedSize(130, 36)
        btn_export.setCursor(Qt.PointingHandCursor)
        btn_export.setFont(QFont("Montserrat", 10))
        btn_export.setStyleSheet(f"""
            QPushButton {{
                background-color: {CARD_BG};
                color: {TEXT_MAIN};
                border: 1.5px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: #f3f4f6;
                border-color: #9ca3af;
            }}
        """)
        btn_export.clicked.connect(self.exportToCSV)

        main_layout.addWidget(SettingItem(
            "Export Data",
            "Unduh semua data log makananmu sebagai CSV",
            btn_export
        ))
        main_layout.addSpacing(8)

        # Tombol Hapus
        btn_hapus = QPushButton("  Hapus Data")
        btn_hapus.setFixedSize(130, 36)
        btn_hapus.setCursor(Qt.PointingHandCursor)
        btn_hapus.setFont(QFont("Montserrat", 10, QFont.Bold))
        btn_hapus.setStyleSheet(f"""
            QPushButton {{
                background-color: {RED_DANGER};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: {RED_HOVER};
            }}
        """)
        btn_hapus.clicked.connect(self.deleteAllData)

        main_layout.addWidget(SettingItem(
            "Hapus Semua Data",
            "Menghapus seluruh log dan riwayat secara permanen",
            btn_hapus
        ))

        main_layout.addStretch()

    def _show_time_notification(self, label: str, time_widget):
        time_str = time_widget.time().toString("HH:mm")
        show_toast(self, f"Pengingat {label} akan di set pada pukul {time_str}", TOAST_SUCCESS)

    # ── Preferensi ────────────────────────────────────────────────────────────
    def _save_preference(self, key: str, value):
        self._settings.setValue(key, value)

    def _on_batas_changed(self, v):
        self._save_preference("batas_kalori", v)
        self._update_keterangan_kalori()

    def _update_keterangan_kalori(self):
        target = 2100 # default
        try:
            sp = getattr(self, 'sistem_profil', None)
            if not sp:
                sp = getattr(self.window(), 'sistem_profil', None)
            if sp and sp.current_profil:
                target = sp.current_profil.get('calory', 2100)
        except Exception:
            pass
        
        persen = self._spin_batas.value()
        maks = int(target * (persen / 100.0))
        self._lbl_keterangan_kalori.setText(f"Setara dengan: {maks} kkal (Berdasarkan target {target} kkal)")

    def _load_preferences(self):
        notif_makan  = self._settings.value("notif_makan",  False, type=bool)
        notif_kalori = self._settings.value("notif_kalori", False, type=bool)

        waktu_sarapan = self._settings.value("waktu_sarapan", "07:00")
        waktu_siang = self._settings.value("waktu_siang", "12:00")
        waktu_malam = self._settings.value("waktu_malam", "19:00")
        batas_kalori = self._settings.value("batas_kalori", 100, type=int)

        # blockSignals agar toggled tidak trigger save ulang saat load
        self._toggle_makan.blockSignals(True)
        self._toggle_kalori.blockSignals(True)
        self._time_sarapan.blockSignals(True)
        self._time_siang.blockSignals(True)
        self._time_malam.blockSignals(True)
        self._spin_batas.blockSignals(True)

        self._toggle_makan.setChecked(notif_makan)
        self._toggle_kalori.setChecked(notif_kalori)
        
        self._time_sarapan.setTime(QTime.fromString(str(waktu_sarapan), "HH:mm"))
        self._time_siang.setTime(QTime.fromString(str(waktu_siang), "HH:mm"))
        self._time_malam.setTime(QTime.fromString(str(waktu_malam), "HH:mm"))
        self._spin_batas.setValue(batas_kalori)
        
        self._makan_details.setVisible(notif_makan)
        self._kalori_details.setVisible(notif_kalori)

        self._toggle_makan.blockSignals(False)
        self._toggle_kalori.blockSignals(False)
        self._time_sarapan.blockSignals(False)
        self._time_siang.blockSignals(False)
        self._time_malam.blockSignals(False)
        self._spin_batas.blockSignals(False)
        
        self._update_keterangan_kalori()

    # ── Export CSV ────────────────────────────────────────────────────────────
    def exportToCSV(self):
        if self._db is None:
            show_toast(self, "Database tidak tersedia.", TOAST_ERROR)
            return

        # Ambil data log dari DB
        try:
            logs = self._db.get_all_logs(limit=10000)
        except Exception as e:
            show_toast(self, f"Gagal mengambil data:\n{e}", TOAST_ERROR)
            return

        if not logs:
            show_toast(self, "Belum ada data log yang tersimpan.", TOAST_NORMAL)
            return

        # Dialog pilih lokasi simpan — nama file otomatis menyertakan timestamp
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"nutrikost_log_{ts}.csv"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Simpan CSV", default_name, "CSV Files (*.csv)"
        )
        if not filepath:
            return  # user cancel

        try:
            # Menggunakan format file dari Code 1 (utf-8-sig, delimiter=';')
            with open(filepath, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file, delimiter=';', quoting=csv.QUOTE_MINIMAL)
                
                # Header custom dipertahankan
                writer.writerow(["Tanggal", "Waktu", "Makanan", "Porsi", "Kalori", "Protein", "Karbohidrat", "Lemak"])
                
                for item in logs:
                    # Ambil string meal_time (contoh: "2026-06-07 08:30:00")
                    meal_time_str = str(item.get('meal_time', ''))
                    
                    # Memisahkan Tanggal dan Waktu berdasarkan spasi
                    if " " in meal_time_str:
                        tanggal, waktu = meal_time_str.split(" ", 1)
                    else:
                        tanggal = meal_time_str
                        waktu = "-"
                    
                    kategori = str(item.get('category') or "Lainnya").capitalize()

                    # Ambil nama makanan dan bersihkan teksnya
                    makanan = item.get('food_name', 'Lainnya')
                    makanan_bersih = self._clean_text(makanan) if hasattr(self, '_clean_text') else str(makanan).strip()

                    # Menulis data ke CSV dengan mengambil nilai langsung berdasarkan nama kolom
                    writer.writerow([
                        tanggal, 
                        kategori, 
                        makanan_bersih, 
                        round(float(item.get('portion') or 0), 1), 
                        round(float(item.get('cal') or 0), 1), 
                        round(float(item.get('protein') or 0), 1), 
                        round(float(item.get('carb') or 0), 1), 
                        round(float(item.get('fat') or 0), 1)
                    ])

            show_toast(self, f"Data berhasil disimpan ke:\n{filepath}", TOAST_SUCCESS)
            
        except Exception as e:
            show_toast(self, f"Terjadi kesalahan:\n{e}", TOAST_ERROR)

    # ── Hapus Semua Data ──────────────────────────────────────────────────────
    def deleteAllData(self):
        # ── Custom styled confirmation dialog (sesuai gaya TambahPopup) ──────
        win = self.window()
        dlg = QDialog(win)
        dlg.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dlg.setAttribute(Qt.WA_TranslucentBackground)
        dlg.setModal(True)
        dlg.setFixedSize(win.width(), win.height())

        # Overlay menutupi seluruh dialog
        overlay = QWidget(dlg)
        overlay.setFixedSize(win.width(), win.height())
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 120);")
        overlay.setAttribute(Qt.WA_StyledBackground, True)

        # Card di tengah overlay
        card = QFrame(overlay)
        card.setFixedSize(400, 270)
        card.move((win.width() - 400) // 2, (win.height() - 270) // 2)
        card.setStyleSheet("""
            QFrame  { background: white; border-radius: 25px; border: none; }
            QLabel  { border: none; background: transparent; color: #555555; font-family: 'Poppins'; }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(12)

        # Judul
        lbl_title = QLabel("🗑️  Hapus Semua Data")
        lbl_title.setFont(QFont('Poppins', 14, QFont.Bold))
        lbl_title.setStyleSheet("color: #dc2626;")
        card_layout.addWidget(lbl_title)

        # Pesan
        lbl_msg = QLabel(
            "Tindakan ini akan menghapus <b>SEMUA</b> log harian &amp; profil "
            "secara permanen dan tidak dapat dibatalkan.<br><br>Apakah kamu yakin?"
        )
        lbl_msg.setFont(QFont('Poppins', 10))
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("color: #555555;")
        card_layout.addWidget(lbl_msg)

        card_layout.addStretch()

        # Tombol
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_cancel = QPushButton("Batal")
        btn_cancel.setFixedHeight(50)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setFont(QFont('Poppins', 12))
        btn_cancel.setStyleSheet(
            "QPushButton { background-color: white; color: rgba(26,122,52,0.7); "
            "border: 1.5px solid #1A7A34; border-radius: 25px; font-size: 16px; } "
            "QPushButton:hover { color: #1A7A34; }"
        )
        btn_cancel.clicked.connect(dlg.reject)

        btn_yes = QPushButton("Ya, Hapus")
        btn_yes.setFixedHeight(50)
        btn_yes.setCursor(Qt.PointingHandCursor)
        btn_yes.setFont(QFont('Poppins', 12, QFont.Bold))
        btn_yes.setStyleSheet(
            "QPushButton { background-color: #dc2626; color: white; "
            "border-radius: 25px; font-size: 16px; border: none; } "
            "QPushButton:hover { background-color: #b91c1c; }"
        )
        btn_yes.clicked.connect(dlg.accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_yes)
        card_layout.addLayout(btn_row)

        if dlg.exec_() != QDialog.Accepted:
            return

        if self._db is None:
            show_toast(self, "Database tidak tersedia.", TOAST_ERROR)
            return

        try:
            conn = self._db._get_connection()
            conn.execute("DELETE FROM LogHarian")
            conn.execute("DELETE FROM ProfilUser")
            conn.commit()
            conn.close()

            show_toast(self, "Semua data telah dihapus.", TOAST_SUCCESS)
        except Exception as e:
            show_toast(self, f"Terjadi kesalahan saat menghapus data:\n{e}", TOAST_ERROR)