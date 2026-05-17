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


class DialogDetailBahan(QDialog):
    """Pop-up yang menampilkan daftar bahan dari data_json_bahan."""

    def __init__(self, nama_makanan, data_json_bahan, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Detail Bahan — {nama_makanan.title()}")
        self.setMinimumWidth(420)
        self.setModal(True)

        layout = QVBoxLayout(self)
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
        btn_tutup.setFixedHeight(36)
        btn_tutup.setCursor(Qt.PointingHandCursor)
        btn_tutup.setStyleSheet("""
            QPushButton {
                background-color: #1A7A34;
                color: white;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #155f28;
            }
        """)
        btn_tutup.clicked.connect(self.accept)
        layout.addWidget(btn_tutup, alignment=Qt.AlignRight)


class RequestPage(PageTemplate):
    PAGE_NAME = "Cache Resep"
    PAGE_DESC = "Daftar makanan yang sudah pernah dianalisis dan disimpan di cache lokal"

    def __init__(self):
        self.db = models.DBHelper()
        super().__init__()

    def build_content(self, container):
        self.container = container
        main_layout = self._scroll.widget().layout()

        # Pin semua konten ke atas
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # --- HEADER ---
        h_header_layout = QHBoxLayout()
        text_vbox = QVBoxLayout()
        text_vbox.addWidget(self._page_title)
        text_vbox.addWidget(self._page_desc)
        h_header_layout.addLayout(text_vbox)
        h_header_layout.addStretch()
        main_layout.insertLayout(0, h_header_layout)

        # --- MAIN CARD --- (disisipkan di index 1, tepat setelah header)
        self.card = QWidget()
        self.card.setStyleSheet("""
            QWidget {
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
        main_layout.insertWidget(1, self.card)

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
            elif has_nutrisi:
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
                    QPushButton:disabled {
                        background-color: #AAAAAA;
                        color: #EEEEEE;
                    }
                """)
                btn_accept.clicked.connect(
                    lambda checked, n=nama, c=cal, p=protein, k=carb, l=fat, btn=btn_accept:
                        self._accept_makanan(n, c, p, k, l, btn)
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
            self.rows_layout.addWidget(aksi_widget, data_row, 8, Qt.AlignVCenter)

            # --- Garis pemisah ---
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("background-color: rgba(26, 122, 52, 0.2); border: none;")
            line.setFixedHeight(1)
            self.rows_layout.addWidget(line, sep_row, 0, 1, 9)

    def _accept_makanan(self, nama_makanan, cal, protein, carb, fat, btn_accept):
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
            QMessageBox.information(
                self, "Berhasil Ditambahkan",
                f"{pesan}\n\nKode Makanan : {code}"
            )
        else:
            QMessageBox.warning(self, "Gagal", pesan)

    def _show_detail(self, nama_makanan, data_json_bahan):
        dialog = DialogDetailBahan(nama_makanan, data_json_bahan, parent=self)
        dialog.exec_()


# ==================  ENTRY POINT (Untuk Testing) ==================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RequestPage()
    window.show()
    sys.exit(app.exec_())