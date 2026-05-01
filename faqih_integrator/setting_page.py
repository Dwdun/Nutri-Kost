import csv
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QMessageBox, QFileDialog,
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont

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
        self.toggled.connect(self._update_style)
        self._update_style(False)

    #ubah tampilan visual sesuai state
    def _update_style(self, checked: bool):
        if checked:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #1A7A34;
                    border-radius: 14px;
                    border: none;
                }
                QPushButton::after {
                    content: '';
                }
            """)
            self.setText("✓")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #1A7A34;
                    color: white;
                    border-radius: 14px;
                    border: none;
                    font-size: 14px;
                    font-weight: bold;
                    padding-right: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #d1d5db;
                    color: transparent;
                    border-radius: 14px;
                    border: none;
                    font-size: 14px;
                }
            """)
            self.setText("  ")


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
        lbl_title.setFont(QFont("Montserrat Alternates", 11, QFont.Bold))
        lbl_title.setStyleSheet(f"color: {TEXT_MAIN}; border: none; background: transparent;")

        lbl_desc = QLabel(description)
        lbl_desc.setFont(QFont("Montserrat Alternates", 9))
        lbl_desc.setStyleSheet(f"color: {TEXT_SUB}; border: none; background: transparent;")
        lbl_desc.setWordWrap(True)

        text_col.addWidget(lbl_title)
        text_col.addWidget(lbl_desc)

        layout.addLayout(text_col, stretch=1)
        layout.addWidget(action_widget, alignment=Qt.AlignVCenter | Qt.AlignRight)


# ── Section header ────────────────────────────────
def _make_section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont("Montserrat Alternates", 11, QFont.Bold))
    lbl.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
    lbl.setContentsMargins(4, 0, 0, 0)
    return lbl


# ── Halaman Pengaturan ────────────────────────────────────────────────────────
class SettingPage(QWidget):

    #inisialisasi page
    def __init__(self, parent=None):
        super().__init__(parent)
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
        lbl_title.setFont(QFont("Montserrat Alternates", 18, QFont.Bold))
        lbl_title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")

        lbl_sub = QLabel("Sesuaikan preferensi aplikasimu")
        lbl_sub.setFont(QFont("Montserrat Alternates", 10))
        lbl_sub.setStyleSheet(f"color: {TEXT_SUB}; background: transparent;")

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
        main_layout.addSpacing(8)
        main_layout.addWidget(SettingItem(
            "Peringatan Kalori",
            "Notifikasi jika kalori melebihi atau terlalu rendah",
            self._toggle_kalori
        ))

        main_layout.addSpacing(20)

        # ── Section Data ────────────────────────────────────────────────────────
        main_layout.addWidget(_make_section_label("Data"))
        main_layout.addSpacing(6)

        # Tombol Export
        btn_export = QPushButton("  Export Data")
        btn_export.setFixedSize(130, 36)
        btn_export.setCursor(Qt.PointingHandCursor)
        btn_export.setFont(QFont("Montserrat Alternates", 10))
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
        btn_hapus.setFont(QFont("Montserrat Alternates", 10, QFont.Bold))
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

    # ── Preferensi ────────────────────────────────────────────────────────────
    def _save_preference(self, key: str, value: bool):
        self._settings.setValue(key, value)

    def _load_preferences(self):
        notif_makan  = self._settings.value("notif_makan",  False, type=bool)
        notif_kalori = self._settings.value("notif_kalori", False, type=bool)

        # blockSignals agar toggled tidak trigger save ulang saat load
        self._toggle_makan.blockSignals(True)
        self._toggle_kalori.blockSignals(True)

        self._toggle_makan.setChecked(notif_makan)
        self._toggle_kalori.setChecked(notif_kalori)

        self._toggle_makan.blockSignals(False)
        self._toggle_kalori.blockSignals(False)

    # ── Export CSV ────────────────────────────────────────────────────────────
    def exportToCSV(self):
        if self._db is None:
            QMessageBox.warning(self, "Error", "Database tidak tersedia.")
            return

        # Ambil data log dari DB
        try:
            logs = self._db.get_all_logs(limit=10000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal mengambil data:\n{e}")
            return

        if not logs:
            QMessageBox.information(self, "Export Data", "Belum ada data log yang tersimpan.")
            return

        # Dialog pilih lokasi simpan
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Simpan CSV", "nutrikost_log.csv", "CSV Files (*.csv)"
        )
        if not filepath:
            return  # user cancel

        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=logs[0].keys())
                writer.writeheader()
                writer.writerows(logs)

            QMessageBox.information(
                self, "Export Berhasil",
                f"Data berhasil disimpan ke:\n{filepath}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Gagal", f"Terjadi kesalahan:\n{e}")

    # ── Hapus Semua Data ──────────────────────────────────────────────────────
    def deleteAllData(self):
        reply = QMessageBox.warning(
            self,
            "Hapus Semua Data",
            "Tindakan ini akan menghapus SEMUA log harian dan profil secara permanen.\n\n"
            "Apakah kamu yakin?",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel
        )

        if reply != QMessageBox.Yes:
            return

        if self._db is None:
            QMessageBox.warning(self, "Error", "Database tidak tersedia.")
            return

        try:
            conn = self._db._get_connection()
            conn.execute("DELETE FROM LogHarian")
            conn.execute("DELETE FROM ProfilUser")
            conn.commit()
            conn.close()

            QMessageBox.information(
                self, "Berhasil",
                "Semua data telah dihapus."
            )
        except Exception as e:
            QMessageBox.critical(self, "Gagal", f"Terjadi kesalahan saat menghapus data:\n{e}")