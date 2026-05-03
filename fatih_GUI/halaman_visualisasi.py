import sys
import os

# Tambahkan root proyek ke sys.path agar import fatih_GUI dikenali saat run mandiri
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functools import partial
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QStackedWidget, QFileDialog, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QPainter, QPageLayout, QFont

import matplotlib.backends.backend_pdf as pdf_backend
from matplotlib.figure import Figure
from matplotlib.image import imread

# Import dari template_halaman.py
from fatih_GUI.template_halaman import (
    PageTemplate,
    font_title, font_body, font_label,
    load_fonts,
    C_WHITE, C_TEXT_DARK, C_TEXT_SUB,
)

# Import semua widget
from fatih_GUI.widgets import (
    KaloriMingguanWidget,
    KomposisiGiziWidget,
    DetailMakroWidget,
    TopMakananWidget,
)

# ═══ BAGIAN BESAR: HALAMAN VISUALISASI ═══
class HalamanVisualisasi(PageTemplate):
    PAGE_NAME = 'Grafik & Visualisasi'
    PAGE_DESC = 'Analisis tren asupan nutrsimu'
    NAV_INDEX = 5

    _id_user = 1
    
    def __init__(self):
        self._active_tab = 0
        self._tab_buttons = []
        super().__init__()

    # ── Membangun Konten ──
    def build_content(self, container: QWidget):
        """
        container sudah punya QVBoxLayout — tinggal addWidget().
        Jangan buat layout baru di level root.
        """
        layout = container.layout()

        # ── Tombol Export PDF dipindah ke sebelah judul ──
        self._btn_export = QPushButton('↓  Export PDF')
        self._btn_export.setFont(QFont('Poppins', 10, QFont.Bold))
        self._btn_export.setCursor(Qt.PointingHandCursor)
        self._btn_export.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #1A7A34;
                border: 2px solid #1A7A34;
                border-radius: 12px;
                padding: 10px 24px;
                font-family: 'Poppins';
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(26, 122, 52, 0.08);
            }
        """)
        self._btn_export.clicked.connect(self._on_export_pdf)
        self._header_row.addWidget(self._btn_export)

        # ── Baris tombol tab ──
        tab_row = self._build_tab_row()
        layout.addLayout(tab_row)

        # ── QStackedWidget untuk konten 3 tab ──
        self._stack = QStackedWidget()
        self._stack.setStyleSheet('background: transparent;')

        # Tab 0: Kalori Mingguan
        self._w_kalori = KaloriMingguanWidget(id_user=self._id_user)
        self._stack.addWidget(self._w_kalori)

        # Tab 1: Komposisi Gizi (2 kolom kiri-kanan)
        tab_komposisi = self._build_tab_komposisi()
        self._stack.addWidget(tab_komposisi)

        # Tab 2: Top 10
        self._w_top10 = TopMakananWidget(id_user=self._id_user)
        self._stack.addWidget(self._w_top10)
        
        layout.addWidget(self._stack)
        
        # Init state tab
        self._update_tab_styles()

        # ── Connect Sidebar Visualisasi ──
        if hasattr(self, '_sidebar') and len(self._sidebar._nav_items) > 7:
            self._sidebar._nav_items[5].clicked.connect(lambda: self._on_tab_clicked(0))
            self._sidebar._nav_items[6].clicked.connect(lambda: self._on_tab_clicked(1))
            self._sidebar._nav_items[7].clicked.connect(lambda: self._on_tab_clicked(2))

    # ── Helper Pembangunan UI ──
    def _build_tab_row(self) -> QHBoxLayout:
        TAB_LABELS = ['Kalori Mingguan', 'Komposisi Gizi', 'Top 10']
        row = QHBoxLayout()
        row.setSpacing(12)
        
        font = QFont('Poppins', 10, QFont.Bold)
        for i, label in enumerate(TAB_LABELS):
            btn = QPushButton(label)
            btn.setFont(font)
            btn.clicked.connect(partial(self._on_tab_clicked, i))
            self._tab_buttons.append(btn)
            row.addWidget(btn)
            
        row.addStretch()
        return row

    def _build_tab_komposisi(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet('background: transparent;')
        row = QHBoxLayout(tab)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(16)

        self._w_komposisi = KomposisiGiziWidget(id_user=self._id_user)
        self._w_detail    = DetailMakroWidget(id_user=self._id_user)

        row.addWidget(self._w_komposisi, 55)
        row.addWidget(self._w_detail, 45)
        return tab

    # ── Logika Tab ──
    def _on_tab_clicked(self, index: int):
        self._stack.setCurrentIndex(index)
        self._active_tab = index
        self._update_tab_styles()

        # Sinkronisasi dengan Sidebar
        sidebar_index = index + 5
        if hasattr(self, '_sidebar') and len(self._sidebar._nav_items) > sidebar_index:
            self._sidebar.set_active_page(sidebar_index)

    def _update_tab_styles(self):
        for i, btn in enumerate(self._tab_buttons):
            btn.setCursor(Qt.PointingHandCursor)
            if i == self._active_tab:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #1A7A34;
                        color: white;
                        border: none;
                        border-radius: 20px;
                        padding: 10px 24px;
                        font-family: 'Poppins';
                        font-size: 13px;
                        font-weight: bold;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        color: #1A7A34;
                        border: 2px solid #1A7A34;
                        border-radius: 20px;
                        padding: 10px 24px;
                        font-family: 'Poppins';
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: rgba(26, 122, 52, 0.08);
                    }
                """)

    # ── Logika Export PDF ──
    def _on_export_pdf(self):
        tab_names = ['Kalori_Mingguan', 'Komposisi_Gizi', 'Top10_Makanan']
        default_name = f'NutriKos_{tab_names[self._active_tab]}.pdf'
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Simpan PDF',
            default_name,
            'PDF Files (*.pdf)',
        )
        
        if not file_path:
            return  # user cancel
        
        if not file_path.endswith('.pdf'):
            file_path += '.pdf'
        
        try:
            widget_to_export = self._stack.widget(self._active_tab)
            self._export_widget_to_pdf(widget_to_export, file_path)
            
            QMessageBox.information(
                self, 'Berhasil',
                f'PDF berhasil disimpan:\n{file_path}'
            )
        except Exception as e:
            QMessageBox.critical(
                self, 'Gagal Export',
                f'Terjadi kesalahan:\n{str(e)}'
            )

    def _export_widget_to_pdf(self, widget: QWidget, file_path: str):
        """Mengekspor isi dari widget secara persis (WYSIWYG) ke PDF A4 Landscape."""
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)
        printer.setPageSize(QPrinter.A4)
        printer.setPageOrientation(QPageLayout.Landscape)
        printer.setPageMargins(10, 10, 10, 10, QPrinter.Millimeter)
        
        painter = QPainter()
        if not painter.begin(printer):
            raise Exception("Gagal memulai proses render PDF.")
            
        page_rect = printer.pageRect()
        
        # Pastikan background putih
        painter.fillRect(page_rect, Qt.white)
        
        # Ambil screenshot widget yang sedang tampil
        pixmap = widget.grab()
        rect = pixmap.rect()
        
        if rect.width() > 0 and rect.height() > 0:
            # Hitung skala agar muat 1 halaman Landscape penuh
            x_scale = page_rect.width() / rect.width()
            y_scale = page_rect.height() / rect.height()
            scale = min(x_scale, y_scale, 9.0)
            
            # Posisikan gambar di tengah halaman
            x_offset = (page_rect.width() - (rect.width() * scale)) / 2.0
            y_offset = (page_rect.height() - (rect.height() * scale)) / 2.0
            
            painter.translate(x_offset, y_offset)
            painter.scale(scale, scale)
            painter.drawPixmap(0, 0, pixmap)
            
        painter.end()


# ── Standalone Preview ──
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = HalamanVisualisasi()
    window.show()
    sys.exit(app.exec_())
