import sys
import os

# Tambahkan root proyek ke sys.path agar import fatih_GUI dikenali saat run mandiri
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functools import partial
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QStackedWidget, QFileDialog, QMessageBox, QApplication, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal
from fatih_GUI.toast_notification import show_toast, TOAST_SUCCESS, TOAST_ERROR
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QPainter, QPageLayout, QFont

# Import semua widget
from fatih_GUI.widgets import (
    KaloriMingguanWidget,
    KomposisiGiziWidget,
    DetailMakroWidget,
    TopMakananWidget,
)

# ═══ BAGIAN BESAR: HALAMAN VISUALISASI ═══
class HalamanVisualisasi(QWidget):
    # Signal untuk memberitahu main_window jika tab diubah dari dalam visualisasi
    tab_changed = pyqtSignal(int)

    _id_user = 1
    
    def __init__(self, id_user: int = 1, db_path: str = None, parent=None):
        super().__init__(parent)
        self._id_user = id_user
        self._db_path = db_path
        self._active_tab = 0
        self._tab_buttons = []
        
        # ── Setup Layout Utama ──
        self.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 32)
        main_layout.setSpacing(16)
        main_layout.setAlignment(Qt.AlignTop)

        # ── Header (Judul & Export) ──
        header_row = QHBoxLayout()
        title_desc_layout = QVBoxLayout()
        title_desc_layout.setSpacing(4)
        
        self._page_title = QLabel('Grafik & Visualisasi')
        self._page_title.setStyleSheet("color: #1C1C1C; background: transparent; font-family: 'Montserrat Alternates'; font-size: 32px; font-weight: bold;")
        
        self._page_desc = QLabel('Analisis tren asupan nutrisimu')
        self._page_desc.setStyleSheet("color: #555555; background: transparent; font-family: 'Montserrat'; font-size: 14px;")
        
        title_desc_layout.addWidget(self._page_title)
        title_desc_layout.addWidget(self._page_desc)
        
        header_row.addLayout(title_desc_layout)
        header_row.addStretch()

        # ── Tombol Export PDF ──
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
        header_row.addWidget(self._btn_export)

        main_layout.addLayout(header_row)
        main_layout.addSpacing(16)

        # ── Baris tombol tab ──
        tab_row = self._build_tab_row()
        main_layout.addLayout(tab_row)

        # ── QStackedWidget untuk konten 3 tab ──
        self._stack = QStackedWidget()
        self._stack.setStyleSheet('background: transparent;')

        # Tab 0: Kalori Mingguan
        self._w_kalori = KaloriMingguanWidget(id_user=self._id_user, db_path=self._db_path)
        self._stack.addWidget(self._w_kalori)

        # Tab 1: Komposisi Gizi (2 kolom kiri-kanan)
        tab_komposisi = self._build_tab_komposisi()
        self._stack.addWidget(tab_komposisi)

        # Tab 2: Top 10
        self._w_top10 = TopMakananWidget(id_user=self._id_user, db_path=self._db_path)
        self._stack.addWidget(self._w_top10)
        
        main_layout.addWidget(self._stack)
        
        # Init state tab
        self._update_tab_styles()

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

        self._w_komposisi = KomposisiGiziWidget(id_user=self._id_user, db_path=self._db_path)
        self._w_detail    = DetailMakroWidget(id_user=self._id_user, db_path=self._db_path)

        row.addWidget(self._w_komposisi, 55)
        row.addWidget(self._w_detail, 45)
        return tab

    # ── Logika Tab ──
    def _on_tab_clicked(self, index: int):
        self.set_tab(index)
        self.tab_changed.emit(index)

    def set_tab(self, index: int):
        if 0 <= index < self._stack.count():
            self._stack.setCurrentIndex(index)
            self._active_tab = index
            self._update_tab_styles()

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

    # ── Refresh Semua Visualisasi ──
    def refresh(self):
        """Memanggil method refresh() pada setiap widget grafik untuk update data dari database."""
        if hasattr(self, '_w_kalori') and hasattr(self._w_kalori, 'refresh'):
            self._w_kalori.refresh()
        if hasattr(self, '_w_komposisi') and hasattr(self._w_komposisi, 'refresh'):
            self._w_komposisi.refresh()
        if hasattr(self, '_w_detail') and hasattr(self._w_detail, 'refresh'):
            self._w_detail.refresh()
        if hasattr(self, '_w_top10') and hasattr(self._w_top10, 'refresh'):
            self._w_top10.refresh()

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
            
            show_toast(self, f'PDF berhasil disimpan:\n{file_path}', TOAST_SUCCESS)
        except Exception as e:
            show_toast(self, f'Terjadi kesalahan:\n{str(e)}', TOAST_ERROR)

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
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec_())
