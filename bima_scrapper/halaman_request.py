import sys
import os
import json
import uuid
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fatih_GUI.template_halaman import PageTemplate

import models
from PyQt5.QtGui import QColor

class DeclineConfirmDialog(QDialog):
    def __init__(self, nama_makanan, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("OverlayDialog")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
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

        title = QLabel("Konfirmasi Penolakan")
        title.setFont(QFont('Poppins', 16, QFont.Bold))
        title.setStyleSheet("color: #1A7A34;")
        card_layout.addWidget(title)

        message = QLabel(f"Apakah Anda yakin ingin menolak request makanan '{nama_makanan.title()}'?\nMakanan ini tidak akan ditambahkan ke database.")
        message.setFont(QFont('Poppins', 11))
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

        btn_keluar = QPushButton("Ya, Tolak")
        btn_keluar.setFixedHeight(50)
        btn_keluar.setCursor(Qt.PointingHandCursor)
        btn_keluar.setStyleSheet(
            "QPushButton { background-color: #1A7A34; color: white; "
            "border-radius: 25px; font-weight: bold; font-size: 16px; border: none; }"
            "QPushButton:hover { background-color: #145925; }"
        )
        btn_keluar.clicked.connect(self.accept)

        btns.addWidget(btn_batal)
        btns.addWidget(btn_keluar)
        
        card_layout.addLayout(btns)
        main_layout.addWidget(self.card)

class InfoDialog(QDialog):
    def __init__(self, title_text, message_text, is_success=True, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("OverlayDialog")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setAlignment(Qt.AlignCenter)
        
        self.card = QFrame()
        self.card.setFixedSize(420, 240)
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
        card_layout.setContentsMargins(35, 30, 35, 30)
        card_layout.setSpacing(15)

        title = QLabel(title_text)
        title.setFont(QFont('Poppins', 16, QFont.Bold))
        title.setStyleSheet(f"color: {'#1A7A34' if is_success else '#F44336'};")
        card_layout.addWidget(title)

        message = QLabel(message_text)
        message.setFont(QFont('Poppins', 11))
        message.setWordWrap(True)
        message.setStyleSheet("line-height: 150%;")
        card_layout.addWidget(message)

        card_layout.addStretch()

        btns = QHBoxLayout()
        btns.setSpacing(15)
        btns.addStretch()
        
        btn_ok = QPushButton("OK")
        btn_ok.setFixedSize(120, 45)
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet(f"""
            QPushButton {{ background-color: {'#1A7A34' if is_success else '#F44336'}; color: white; 
            border-radius: 22px; font-weight: bold; font-size: 14px; border: none; }}
            QPushButton:hover {{ background-color: {'#145925' if is_success else '#D32F2F'}; }}
        """)
        btn_ok.clicked.connect(self.accept)

        btns.addWidget(btn_ok)
        card_layout.addLayout(btns)
        main_layout.addWidget(self.card)

class DialogDetailBahan(QDialog):
    """Pop-up yang menampilkan daftar bahan dari data_json_bahan."""

    def __init__(self, nama_makanan, data_json_bahan, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Detail Bahan — {nama_makanan.title()}")
        self.setMinimumWidth(420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        self.setStyleSheet("background-color: white;")
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # --- Judul ---
        lbl_judul = QLabel(nama_makanan.title())
        lbl_judul.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl_judul.setStyleSheet("color: #1A7A34;")
        layout.addWidget(lbl_judul)

        lbl_sub = QLabel("Daftar bahan mentah (1 porsi):")
        lbl_sub.setFont(QFont("Segoe UI", 10))
        lbl_sub.setStyleSheet("color: #555555;")
        layout.addWidget(lbl_sub)

        # --- Garis pemisah ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #1A7A34;")
        line.setFixedHeight(2)
        layout.addWidget(line)

        # --- Daftar bahan ---
        try:
            bahan_list = json.loads(data_json_bahan) if isinstance(data_json_bahan, str) else data_json_bahan
        except (json.JSONDecodeError, TypeError):
            bahan_list = []

        if bahan_list:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; }")
            scroll.setMaximumHeight(320)

            bahan_widget = QWidget()
            bahan_layout = QVBoxLayout(bahan_widget)
            bahan_layout.setContentsMargins(4, 4, 4, 4)
            bahan_layout.setSpacing(6)

            for idx, bahan in enumerate(bahan_list, start=1):
                row = QHBoxLayout()

                lbl_no = QLabel(f"{idx}.")
                lbl_no.setFixedWidth(24)
                lbl_no.setFont(QFont("Segoe UI", 10))
                lbl_no.setStyleSheet("color: #999999;")

                lbl_bahan = QLabel(str(bahan))
                lbl_bahan.setFont(QFont("Segoe UI", 10))
                lbl_bahan.setStyleSheet("color: #222222;")
                lbl_bahan.setWordWrap(True)

                row.addWidget(lbl_no)
                row.addWidget(lbl_bahan, 1)
                bahan_layout.addLayout(row)

            bahan_layout.addStretch()
            scroll.setWidget(bahan_widget)
            layout.addWidget(scroll)
        else:
            lbl_kosong = QLabel("Data bahan tidak tersedia.")
            lbl_kosong.setStyleSheet("color: gray; padding: 12px;")
            lbl_kosong.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl_kosong)

        # --- Tombol Tutup ---
        btn_tutup = QPushButton("Tutup")
        btn_tutup.setFixedHeight(48)
        btn_tutup.setCursor(Qt.PointingHandCursor)
        btn_tutup.setStyleSheet("""
            QPushButton {
                background-color: #1A7A34;
                color: white;
                border-radius: 24px;
                font-size: 14px;
                font-weight: bold;
                padding: 0 24px;
            }
            QPushButton:hover {
                background-color: #145925;
            }
        """)
        btn_tutup.clicked.connect(self.accept)
        layout.addWidget(btn_tutup)


class RequestPage(PageTemplate):
    PAGE_NAME = "Cache Resep"
    PAGE_DESC = "Daftar makanan yang sudah pernah dianalisis dan disimpan di cache lokal"

    def __init__(self):
        self.db = models.DBHelper()
        super().__init__()
        if hasattr(self, '_sidebar') and self._sidebar:
            self._sidebar.hide()
        if hasattr(self, '_header') and self._header:
            self._header.hide()

    def build_content(self, container):
        self.container = container

        self.btn_refresh = QPushButton("↻ Refresh")
        self.btn_refresh.setFixedSize(145, 56)
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setFont(QFont("Poppins", 10, QFont.Bold))
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #1A7A34;
                border: 1px solid #1A7A34;
                border-radius: 16px;
                outline: none;
            }
            QPushButton:hover {
                background-color: #1A7A34;
                color: white;
            }
        """)
        self.btn_refresh.clicked.connect(self.refresh)
        self._header_row.insertWidget(1, self.btn_refresh)

        # --- MAIN CARD ---
        self.card = QFrame()
        self.card.setObjectName("MainCard")
        self.card.setStyleSheet("""
            QFrame#MainCard {
                background: white;
                border-radius: 16px;
                border: 1px solid #1A7A34;
            }
        """)
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(20, 20, 20, 20)
        self.card_layout.setSpacing(15)

        lbl_title = QLabel("Daftar Cache Resep")
        lbl_title.setFont(self.font_title(20))
        lbl_title.setStyleSheet("color: black; border: none;")
        self.card_layout.addWidget(lbl_title)

        # --- GRID TABEL ---
        self.rows_container = QWidget()
        self.rows_container.setStyleSheet("border: none;")
        self.rows_layout = QGridLayout(self.rows_container)
        self.rows_layout.setContentsMargins(10, 10, 10, 10)
        self.rows_layout.setSpacing(0)

        self.rows_layout.setColumnStretch(0, 1)   # No
        self.rows_layout.setColumnStretch(1, 4)   # Nama Makanan
        self.rows_layout.setColumnStretch(2, 2)   # Kalori
        self.rows_layout.setColumnStretch(3, 2)   # Protein
        self.rows_layout.setColumnStretch(4, 2)   # Karbo
        self.rows_layout.setColumnStretch(5, 2)   # Lemak
        self.rows_layout.setColumnStretch(6, 2)   # Air
        self.rows_layout.setColumnStretch(7, 2)   # Serat
        self.rows_layout.setColumnStretch(8, 3)   # Aksi

        self.card_layout.addWidget(self.rows_container)
        container.layout().addWidget(self.card)

        self.load_data()

    def refresh(self):
        self.load_data()

    def load_data(self):
        # Bersihkan tabel
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # --- HEADER TABEL ---
        headers = ["No", "Nama Makanan", "Kal (kcal)", "Protein (g)", "Karbo (g)", "Lemak (g)", "Air (g)", "Serat (g)", "Aksi"]
        for col, text in enumerate(headers):
            lbl = QLabel(text)
            lbl.setFont(self.font_title(12))
            # Kolom nutrisi rata tengah
            if col >= 2 and col <= 7:
                lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: black; border: none; padding: 6px 4px;")
            self.rows_layout.addWidget(lbl, 0, col)

        # Sub-header keterangan satuan per 100g
        lbl_per100 = QLabel("* Nilai nutrisi per 100 gram")
        lbl_per100.setFont(QFont("Segoe UI", 9))
        lbl_per100.setStyleSheet("color: #888888; border: none; padding: 0 4px 4px 4px;")
        self.rows_layout.addWidget(lbl_per100, 1, 0, 1, 9)

        header_line = QFrame()
        header_line.setFrameShape(QFrame.HLine)
        header_line.setStyleSheet("background-color: #1A7A34; border: none;")
        header_line.setFixedHeight(2)
        self.rows_layout.addWidget(header_line, 2, 0, 1, 9)

        # --- AMBIL DATA DARI CacheResep (termasuk nutrisi) ---
        try:
            conn = self.db._get_connection()
            cursor = conn.execute(
                "SELECT id, nama_makanan, data_json_bahan, cal, protein, carb, fat, water, fiber, status "
                "FROM CacheResep ORDER BY id ASC"
            )
            cache_data = [dict(row) for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            print(f"[ERROR] Gagal mengambil data cache: {e}")
            cache_data = []

        if not cache_data:
            empty_lbl = QLabel("Belum ada data di cache resep.")
            empty_lbl.setStyleSheet("color: gray; border: none; padding: 20px;")
            self.rows_layout.addWidget(empty_lbl, 3, 0, 1, 9, Qt.AlignCenter)
            return

        # --- TAMPILKAN BARIS DATA ---
        for i, entry in enumerate(cache_data, start=1):
            data_row = 3 + (i - 1) * 2   # baris 2 sekarang jadi sub-header, garis di baris 2
            sep_row  = data_row + 1

            nama      = entry.get('nama_makanan', '-')
            data_json = entry.get('data_json_bahan', '[]')
            cal       = entry.get('cal')
            protein   = entry.get('protein')
            carb      = entry.get('carb')
            fat       = entry.get('fat')
            water     = entry.get('water')
            fiber     = entry.get('fiber')
            status    = entry.get('status', 1)  # 1=menunggu, 2=sudah disetujui

            has_nutrisi = all(v is not None for v in [cal, protein, carb, fat])

            def fmt(v):
                return f"{round(v, 1)}" if v is not None else "—"

            # --- Kolom No ---
            lbl_no = QLabel(str(i))
            lbl_no.setContentsMargins(4, 6, 4, 6)
            lbl_no.setFont(self.font_body(12))
            lbl_no.setStyleSheet("color: #555555; border: none;")
            self.rows_layout.addWidget(lbl_no, data_row, 0)

            # --- Kolom Nama Makanan ---
            lbl_nama = QLabel(nama.title())
            lbl_nama.setContentsMargins(4, 6, 4, 6)
            lbl_nama.setFont(self.font_label(12, bold=True))
            lbl_nama.setStyleSheet("color: #1A7A34; border: none;")
            self.rows_layout.addWidget(lbl_nama, data_row, 1)

            # --- Kolom Nutrisi (kal, protein, karbo, lemak, air, serat) ---
            nutrisi_vals = [fmt(cal), fmt(protein), fmt(carb), fmt(fat), fmt(water), fmt(fiber)]
            for col_idx, val in enumerate(nutrisi_vals, start=2):
                lbl_val = QLabel(val)
                lbl_val.setContentsMargins(4, 6, 4, 6)
                lbl_val.setFont(self.font_body(12))
                lbl_val.setAlignment(Qt.AlignCenter)
                lbl_val.setStyleSheet(
                    "color: #333333; border: none;" if val != "—"
                    else "color: #BBBBBB; border: none;"
                )
                self.rows_layout.addWidget(lbl_val, data_row, col_idx)

            # --- Kolom Aksi: dua tombol dalam satu widget ---
            aksi_widget = QWidget()
            aksi_widget.setStyleSheet("border: none;")
            aksi_layout = QHBoxLayout(aksi_widget)
            aksi_layout.setContentsMargins(4, 4, 4, 4)
            aksi_layout.setSpacing(6)

            btn_lihat = QPushButton("Lihat Bahan")
            btn_lihat.setFixedHeight(30)
            btn_lihat.setCursor(Qt.PointingHandCursor)
            btn_lihat.setStyleSheet("""
                QPushButton {
                    background-color: #1A7A34;
                    color: white;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 10px;
                    border: none;
                }
                QPushButton:hover { background-color: #155f28; }
            """)
            btn_lihat.clicked.connect(lambda checked, n=nama, d=data_json: self._show_detail(n, d))

            btn_accept = QPushButton("✓ Accept")
            btn_accept.setFixedHeight(30)
            btn_accept.setCursor(Qt.PointingHandCursor)
            btn_accept.setObjectName(f"accept_{nama}")
            
            btn_decline = QPushButton("✗ Decline")
            btn_decline.setFixedHeight(30)
            btn_decline.setCursor(Qt.PointingHandCursor)
            btn_decline.setObjectName(f"decline_{nama}")

            if status == 2:
                # Sudah di-accept sebelumnya
                btn_accept.setEnabled(False)
                btn_accept.setText("✓ Ditambahkan")
                btn_accept.setToolTip("Makanan ini sudah pernah disetujui dan ditambahkan ke database.")
                btn_accept.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: bold;
                        padding: 0 10px;
                        border: none;
                    }
                """)
                btn_decline.setVisible(False)
            elif status == 3:
                # Sudah di-decline sebelumnya
                btn_accept.setVisible(False)
                btn_decline.setEnabled(False)
                btn_decline.setText("✗ Ditolak")
                btn_decline.setToolTip("Makanan ini sudah ditolak.")
                btn_decline.setStyleSheet("""
                    QPushButton {
                        background-color: #F44336;
                        color: white;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: bold;
                        padding: 0 10px;
                        border: none;
                    }
                """)
            else:
                btn_decline.setStyleSheet("""
                    QPushButton {
                        background-color: #F44336;
                        color: white;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: bold;
                        padding: 0 10px;
                        border: none;
                    }
                    QPushButton:hover { background-color: #D32F2F; }
                """)
                btn_decline.clicked.connect(
                    lambda checked=False, n=nama, ba=btn_accept, bd=btn_decline:
                        self._decline_makanan(n, ba, bd)
                )

                if has_nutrisi:
                    btn_accept.setStyleSheet("""
                        QPushButton {
                            background-color: #2196F3;
                            color: white;
                            border-radius: 6px;
                            font-size: 11px;
                            font-weight: bold;
                            padding: 0 10px;
                            border: none;
                        }
                        QPushButton:hover { background-color: #1565C0; }
                    """)
                    btn_accept.clicked.connect(
                        lambda checked=False, n=nama, c=cal, p=protein, k=carb, l=fat, ba=btn_accept, bd=btn_decline:
                            self._accept_makanan(n, c, p, k, l, ba, bd)
                    )
                else:
                    btn_accept.setEnabled(False)
                    btn_accept.setToolTip("Nutrisi belum tersedia. Jalankan analisis lewat CLI terlebih dahulu.")
                    btn_accept.setStyleSheet("""
                        QPushButton {
                            background-color: #CCCCCC;
                            color: #888888;
                            border-radius: 6px;
                            font-size: 11px;
                            font-weight: bold;
                            padding: 0 10px;
                            border: none;
                        }
                    """)

            aksi_layout.addWidget(btn_lihat)
            aksi_layout.addWidget(btn_accept)
            aksi_layout.addWidget(btn_decline)
            self.rows_layout.addWidget(aksi_widget, data_row, 8, Qt.AlignVCenter)

            # --- Garis pemisah ---
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("background-color: rgba(26, 122, 52, 0.2); border: none;")
            line.setFixedHeight(1)
            self.rows_layout.addWidget(line, sep_row, 0, 1, 9)

    def _accept_makanan(self, nama_makanan, cal, protein, carb, fat, btn_accept, btn_decline):
        """Insert entri CacheResep ke tabel Makanan dengan kode unik."""
        success, code, pesan = self.db.accept_cache_to_makanan(nama_makanan, cal, protein, carb, fat)

        if success:
            btn_accept.setEnabled(False)
            btn_accept.setText("✓ Ditambahkan")
            btn_accept.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 10px;
                    border: none;
                }
            """)
            btn_accept.setToolTip(f"Kode: {code}")
            btn_decline.setVisible(False)
            msg = InfoDialog("Berhasil Ditambahkan", f"{pesan}\n\nKode Makanan : {code}", is_success=True, parent=self)
            msg.exec_()
        else:
            msg = InfoDialog("Gagal", pesan, is_success=False, parent=self)
            msg.exec_()

    def _decline_makanan(self, nama_makanan, btn_accept, btn_decline):
        dialog = DeclineConfirmDialog(nama_makanan, self)
        reply = dialog.exec_()
        
        if reply == QDialog.Accepted:
            success, pesan = self.db.decline_cache(nama_makanan)
            if success:
                btn_accept.setVisible(False)
                btn_decline.setEnabled(False)
                btn_decline.setText("✗ Ditolak")
                btn_decline.setStyleSheet("""
                    QPushButton {
                        background-color: #F44336;
                        color: white;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: bold;
                        padding: 0 10px;
                        border: none;
                    }
                """)
                msg_info = InfoDialog("Ditolak", pesan, is_success=True, parent=self)
                msg_info.exec_()
            else:
                msg_err = InfoDialog("Gagal", pesan, is_success=False, parent=self)
                msg_err.exec_()

    def _show_detail(self, nama_makanan, data_json_bahan):
        dialog = DialogDetailBahan(nama_makanan, data_json_bahan, parent=self)
        dialog.exec_()


# ==================  ENTRY POINT (Untuk Testing) ==================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RequestPage()
    window.show()
    sys.exit(app.exec_())