import sys
import os
import io
from contextlib import redirect_stdout
from datetime import date
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QEvent, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QDoubleValidator, QIcon

# Ensure the system can find LogSystem and templates
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from LogSystem import LogSystem

# ─── Import AI module dari bima_scrapper ───────────────────────────────────────
_bima_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bima_scrapper"))
if _bima_path not in sys.path:
    sys.path.append(_bima_path)

try:
    from test_ai import init_cache_table, proses_nutrisi_terminal
    init_cache_table()          # pastikan tabel CacheResep sudah ada
    AI_AVAILABLE = True
except Exception as _e:
    print(f"[WARN] Modul AI tidak tersedia: {_e}")
    AI_AVAILABLE = False
# ───────────────────────────────────────────────────────────────────────────────


# ==================  AI WORKER THREAD  ==================
class AIWorkerThread(QThread):
    """Menjalankan proses_nutrisi_terminal di background agar UI tidak freeze."""
    finished = pyqtSignal(str, bool, str, str)   # (nama_makanan, sukses, status, detail)

    def __init__(self, nama_makanan):
        super().__init__()
        self.nama_makanan = nama_makanan

    def run(self):
        try:
            # Suppress output terminal supaya tidak banjir di konsol GUI
            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                res = proses_nutrisi_terminal(self.nama_makanan)
                if isinstance(res, tuple):
                    status, detail = res
                else:
                    status, detail = "SUCCESS", ""
            self.finished.emit(self.nama_makanan, True, status, detail or "")
        except Exception as e:
            print(f"[AI Error] {e}")
            self.finished.emit(self.nama_makanan, False, "FAILED", str(e))


# ==================  AI TAMBAH POPUP  ==================
class AITambahPopup(QWidget):
    """
    Popup untuk menambahkan makanan yang tidak ada di database
    menggunakan analisis AI dari test_ai.py (bima_scrapper).
    """
    def __init__(self, parent, back_callback, success_callback):
        super().__init__(parent)
        self.back_callback   = back_callback
        self.success_callback = success_callback
        self.worker = None

        # ── Overlay gelap ──
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignCenter)

        # ── Card ── (style identik dengan TambahPopup)
        self.card = QFrame()
        self.card.setFixedSize(380, 370)
        self.card.setStyleSheet("""
            QFrame  { background: white; border-radius: 25px; border: none; }
            QLabel  { border: none; background: transparent; color: #555555; font-family: 'Poppins'; }
            #AIInput {
                padding: 5px 15px;
                border: none;
                border-radius: 20px;
                background: rgba(26, 122, 52, 0.25);
                color: #1A7A34;
            }
        """)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(10)

        # ── Judul ──
        lbl_title = QLabel("Tambah Makanan via AI 🤖")
        lbl_title.setFont(QFont('Poppins', 14, QFont.Bold))
        lbl_title.setStyleSheet("color: #1A7A34;")
        card_layout.addWidget(lbl_title)

        # ── Keterangan singkat ──
        lbl_desc = QLabel(
            "Masukkan nama makanan yang belum terdaftar.\n"
            "AI akan menganalisis bahan & nutrisinya secara otomatis."
        )
        lbl_desc.setFont(QFont('Poppins', 9))
        lbl_desc.setWordWrap(True)
        card_layout.addWidget(lbl_desc)

        # ── Input nama makanan ──
        card_layout.addWidget(QLabel("Nama Makanan"))
        self.input_nama = QLineEdit()
        self.input_nama.setObjectName("AIInput")
        self.input_nama.setPlaceholderText("contoh: ayam geprek, nasi padang ...")
        self.input_nama.setFixedHeight(45)
        self.input_nama.setStyleSheet(
            "QLineEdit { border: none; border-radius: 20px; padding-left: 15px; "
            "background: rgba(26, 122, 52, 0.25); color: #1A7A34; }"
        )
        # Tekan Enter juga memicu pencarian
        self.input_nama.returnPressed.connect(self._start_search)
        card_layout.addWidget(self.input_nama)

        # ── Label status / loading ──
        self.lbl_status = QLabel("")
        self.lbl_status.setFont(QFont('Poppins', 9))
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setFixedHeight(50)
        card_layout.addWidget(self.lbl_status)

        # ── Tombol aksi ──
        btns = QHBoxLayout()

        self.btn_back = QPushButton("Kembali")
        self.btn_back.setFixedHeight(50)
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.setStyleSheet(
            "QPushButton { background-color: white; color: rgba(26,122,52,0.5); "
            "border: 1px solid #1A7A34; border-radius: 25px; font-size: 18px; } "
            "QPushButton:hover { color: #1A7A34; } "
            "QPushButton:disabled { border-color: #ccc; color: #ccc; }"
        )

        self.btn_search = QPushButton("Cari & Tambahkan")
        self.btn_search.setFixedHeight(50)
        self.btn_search.setCursor(Qt.PointingHandCursor)
        self.btn_search.setStyleSheet(
            "QPushButton { background-color: #1A7A34; color: white; "
            "border-radius: 25px; font-weight: bold; font-size: 16px; } "
            "QPushButton:hover { background-color: #155e29; } "
            "QPushButton:disabled { background-color: #a0c8a8; }"
        )

        self.btn_back.clicked.connect(self.back_callback)
        self.btn_search.clicked.connect(self._start_search)

        btns.addWidget(self.btn_back)
        btns.addWidget(self.btn_search)
        card_layout.addLayout(btns)

        main_layout.addWidget(self.card)

    # ── Mulai proses AI ──────────────────────────────────────────────────
    def _start_search(self):
        nama = self.input_nama.text().strip()
        if not nama:
            self._set_status("⚠️  Masukkan nama makanan terlebih dahulu.", "orange")
            return

        if not AI_AVAILABLE:
            self._set_status("❌  Modul AI tidak tersedia. Periksa instalasi.", "red")
            return

        # Kunci tombol & tampilkan loading
        self.btn_search.setEnabled(False)
        self.btn_back.setEnabled(False)
        self.input_nama.setEnabled(False)
        self._set_status("🤖  AI sedang menganalisis resep... Mohon tunggu.", "#1A7A34")

        self.worker = AIWorkerThread(nama)
        self.worker.finished.connect(self._on_ai_done)
        self.worker.start()

    def _on_ai_done(self, nama_makanan, sukses, status, detail):
        self.btn_search.setEnabled(True)
        self.btn_back.setEnabled(True)
        self.input_nama.setEnabled(True)

        if sukses:
            if status == "EXISTS":
                self._set_status(
                    f"💡  '{nama_makanan}' sudah terdaftar di database utama\n"
                    f"sebagai '{detail.title()}'. Silakan cari langsung.",
                    "orange"
                )
            elif status == "EMPTY":
                self._set_status(
                    f"⚠️  '{nama_makanan}' tidak dapat diuraikan oleh AI.\n"
                    "Coba masukkan nama makanan yang wajar.",
                    "orange"
                )
            else:
                self._set_status(
                    f"✅  '{nama_makanan}' berhasil dianalisis & di-request!\n"
                    "Silakan menunggu persetujuan admin.",
                    "#1A7A34"
                )
                self.success_callback(nama_makanan)
        else:
            self._set_status(
                "❌  Gagal menganalisis makanan. Periksa koneksi/API Key.",
                "red"
            )

    def _set_status(self, text, color):
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"color: {color}; border: none;")


# ==================  TAMBAH POPUP (ORIGINAL + MODIFIKASI)  ==================
class TambahPopup(QWidget):
    def __init__(self, parent, db, save_callback, cancel_callback, edit_data=None):
        super().__init__(parent)
        self.db              = db
        self.save_callback   = save_callback
        self.cancel_callback = cancel_callback
        self.edit_data       = edit_data
        self.btn_save        = QPushButton("Simpan" if self.edit_data else "Tambah")
        self.ai_popup        = None

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignCenter)

        self.card = QFrame()
        self.card.setFixedSize(380, 490)          # +40px dari ukuran asli untuk tombol AI
        self.card.setStyleSheet("""
            QFrame { background: white; border-radius: 25px; border: none; }
            QLabel { border: none; background: transparent; color: #555555; font-family: 'Poppins'; }
            #FoodInput { padding: 5px 15px; border: none; border-radius: 20px; background: rgba(26, 122, 52, 0.25); color: #1A7A34; }
            #FoodInput:disabled { background: #E0E0E0; color: #555555; }
            #FoodInput::drop-down { width: 0px; border: none; }
        """)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(10)

        # --- NAMA MAKANAN ---
        card_layout.addWidget(QLabel("Nama Makanan"))
        self.nama = QComboBox()
        self.nama.setObjectName("FoodInput")
        self.nama.setEditable(True)
        self.nama.setInsertPolicy(QComboBox.NoInsert)
        self.nama.setFixedHeight(45)
        self.nama.lineEdit().setPlaceholderText("Type Here")
        self.nama.lineEdit().setStyleSheet(
            "background: transparent; border: none; color: #1A7A34; padding-left: 5px;"
        )

        self.nama.setView(QListView())
        self.nama.view().window().setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.nama.view().window().setAttribute(Qt.WA_TranslucentBackground)

        self._populate_food_list()
        card_layout.addWidget(self.nama)

        # ── [BARU] Tombol "Makanan tidak terdaftar? Tambahkan" ──────────────
        self.btn_ai_tambah = QPushButton("🔍  Makanan tidak terdaftar? Tambahkan request pada kami")
        self.btn_ai_tambah.setFixedHeight(28)
        self.btn_ai_tambah.setCursor(Qt.PointingHandCursor)
        self.btn_ai_tambah.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #1A7A34;
                border: none;
                text-align: left;
                font-size: 11px;
                text-decoration: underline;
                padding-left: 4px;
            }
            QPushButton:hover  { color: #0d5c28; }
            QPushButton:disabled { color: #aaa; }
        """)
        self.btn_ai_tambah.clicked.connect(self._open_ai_popup)
        # Sembunyikan tombol jika AI tidak tersedia atau sedang mode edit
        if not AI_AVAILABLE or self.edit_data:
            self.btn_ai_tambah.setVisible(False)
        card_layout.addWidget(self.btn_ai_tambah)
        # ────────────────────────────────────────────────────────────────────

        # --- ROW: PORSI & WAKTU ---
        row = QHBoxLayout()
        col1 = QVBoxLayout()
        col1.addWidget(QLabel("Porsi (gram/ml)"))
        self.porsi = QLineEdit()
        self.porsi.setPlaceholderText("0")
        self.porsi.setFixedHeight(45)
        self.porsi.setStyleSheet(
            "QLineEdit { border: none; border-radius: 20px; padding-left: 15px; "
            "background: rgba(26, 122, 52, 0.25); color: #1A7A34; }"
        )
        validator = QDoubleValidator(0.0, 10000.0, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.porsi.setValidator(validator)
        col1.addWidget(self.porsi)

        col2 = QVBoxLayout()
        col2.addWidget(QLabel("Waktu Makan"))
        self.waktu = QComboBox()
        self.waktu.setFixedHeight(45)
        self.waktu.setView(QListView())
        self.waktu.setStyleSheet("""
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
            QComboBox::down-arrow {
                image: url(./assets/down_arrow.png);
                width: 14px;
                height: 14px;
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
        """)
        self.waktu.addItems(["Sarapan", "Makan Siang", "Makan Malam", "Snack", "Minuman"])
        col2.addWidget(self.waktu)

        row.addLayout(col1)
        row.addLayout(col2)
        card_layout.addLayout(row)

        # --- PREVIEW NUTRISI BOX ---
        card_layout.addWidget(QLabel("Preview Nutrisi"))
        self.preview_box = QFrame()
        self.preview_box.setFixedHeight(110)
        self.preview_box.setStyleSheet("background-color: #CDE2D4; border-radius: 20px;")
        preview_layout = QHBoxLayout(self.preview_box)

        def create_nut_col(label_text):
            container = QVBoxLayout()
            val_lbl = QLabel("--")
            val_lbl.setAlignment(Qt.AlignCenter)
            val_lbl.setFont(QFont('Poppins', 14, QFont.Bold))
            val_lbl.setStyleSheet("color: #1A7A34; border: none;")
            txt_lbl = QLabel(label_text)
            txt_lbl.setAlignment(Qt.AlignCenter)
            txt_lbl.setFont(QFont('Poppins', 9))
            txt_lbl.setStyleSheet("color: #555555; font-weight: normal; border: none;")
            container.addWidget(val_lbl)
            container.addWidget(txt_lbl)
            return container, val_lbl

        self.lay_cal, self.val_cal = create_nut_col("kalori")
        self.lay_pro, self.val_pro = create_nut_col("protein")
        self.lay_kar, self.val_kar = create_nut_col("Karbo")
        self.lay_lem, self.val_lem = create_nut_col("Lemak")

        preview_layout.addLayout(self.lay_cal)
        preview_layout.addLayout(self.lay_pro)
        preview_layout.addLayout(self.lay_kar)
        preview_layout.addLayout(self.lay_lem)
        card_layout.addWidget(self.preview_box)

        # --- BUTTONS ---
        btns = QHBoxLayout()
        btn_cancel = QPushButton("Batal")
        btn_cancel.setFixedHeight(50)
        btn_cancel.setStyleSheet(
            "QPushButton { background-color: white; color: rgba(26, 122, 52, 0.5); "
            "border: 1px solid #1A7A34; border-radius: 25px; font-size: 20px; } "
            "QPushButton:hover { color: #1A7A34; }"
        )

        btn_save = QPushButton("Simpan" if self.edit_data else "Tambah")
        btn_save.setFixedHeight(50)
        btn_save.setStyleSheet(
            "QPushButton { background-color: #1A7A34; color: white; "
            "border-radius: 25px; font-weight: bold; font-size: 20px; }"
        )

        btn_save.clicked.connect(self.on_save)
        btn_cancel.clicked.connect(self.cancel_callback)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        card_layout.addLayout(btns)
        main_layout.addWidget(self.card)

        self.nama.currentIndexChanged.connect(self.update_preview)
        self.porsi.textChanged.connect(self.update_preview)

        # --- APPLY EDIT DATA ---
        if self.edit_data:
            idx = self.nama.findText(self.edit_data['food_name'])
            if idx >= 0:
                self.nama.setCurrentIndex(idx)
            self.nama.setEnabled(False)
            self.porsi.setText(str(self.edit_data['portion']))
            self.waktu.setCurrentText(self.edit_data['meal_time'])
        else:
            self.nama.setCurrentIndex(-1)

        self.update_preview()

    # ── Mengisi dropdown makanan dari DB ─────────────────────────────────
    def _populate_food_list(self):
        self.nama.clear()
        food_names = []
        for food in self.db.GetAllFoods():
            self.nama.addItem(food["food_name"], food["code"])
            food_names.append(food["food_name"])

        completer = QCompleter(food_names, self.nama)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.nama.setCompleter(completer)

    # ── Buka AI popup ─────────────────────────────────────────────────────
    def _open_ai_popup(self):
        main_window = self.parent()
        self.ai_popup = AITambahPopup(
            main_window,
            back_callback    = self._close_ai_popup,
            success_callback = self._on_ai_success
        )
        self.ai_popup.setGeometry(0, 0, main_window.width(), main_window.height())
        self.hide()
        self.ai_popup.show()
        self.ai_popup.raise_()

    def _close_ai_popup(self):
        if self.ai_popup:
            self.ai_popup.hide()
            self.ai_popup = None
        self.show()
        self.raise_()

    def _on_ai_success(self, nama_makanan):
        """Dipanggil setelah AI selesai menyimpan makanan baru ke DB."""
        # Refresh dropdown supaya makanan baru langsung muncul
        self._populate_food_list()

        # Coba pilih otomatis makanan yang baru ditambahkan
        idx = self.nama.findText(nama_makanan.title(), Qt.MatchContains)
        if idx >= 0:
            self.nama.setCurrentIndex(idx)

    # ── Preview nutrisi ───────────────────────────────────────────────────
    def update_preview(self):
        try:
            porsi = float(self.porsi.text()) if self.porsi.text() else 0
        except:
            porsi = 0

        idx  = self.nama.findText(self.nama.currentText(), Qt.MatchExactly)
        code = self.nama.itemData(idx) if idx >= 0 else None

        self.btn_save.setEnabled(code is not None and porsi > 0)

        if code:
            data = self.db.kalkulator_nutrisi(code, porsi)
            if data:
                self.val_cal.setText(str(int(data['cal'])))
                self.val_pro.setText(str(data['protein']))
                self.val_kar.setText(str(data['carb']))
                self.val_lem.setText(str(data['fat']))
        else:
            for lbl in [self.val_cal, self.val_pro, self.val_kar, self.val_lem]:
                lbl.setText("--")

    # ── Validasi kategori ─────────────────────────────────────────────────
    _KATEGORI_KEYWORDS = {
        "Minuman": ["minuman", "teh", "kopi", "susu", "jus", "air", "soda",
                    "sirup", "drink", "juice", "milk", "tea", "coffee", "squash"],
        "Snack"  : ["snack", "keripik", "kue", "biskuit", "coklat", "permen",
                    "wafer", "chip", "cracker", "cookie", "candy", "jajanan"],
    }

    def _validate_kategori(self, food_name: str, kategori: str) -> bool:
        """Return True jika food_name cocok dengan kategori, atau kategori tidak perlu validasi."""
        keywords = self._KATEGORI_KEYWORDS.get(kategori)
        if not keywords:
            return True   # Sarapan/Makan Siang/Makan Malam tidak divalidasi
        name_lower = food_name.lower()
        return any(kw in name_lower for kw in keywords)

    def _konfirmasi_kategori_popup(self, food_name: str, kategori: str) -> bool:
        """Tampilkan styled overlay popup untuk konfirmasi kategori tidak sesuai.
        Return True jika user memilih Lanjutkan, False jika Batal."""
        from PyQt5.QtWidgets import QDialog
        main_window = self.window()

        dlg = QDialog(main_window)
        dlg.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dlg.setAttribute(Qt.WA_TranslucentBackground)
        dlg.setModal(True)
        dlg.setFixedSize(main_window.width(), main_window.height())

        outer = QVBoxLayout(dlg)
        outer.setContentsMargins(0, 0, 0, 0)

        overlay = QWidget(dlg)
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 120);")
        overlay.setAttribute(Qt.WA_StyledBackground, True)
        inner = QVBoxLayout(overlay)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setAlignment(Qt.AlignCenter)


        card = QFrame()
        card.setFixedSize(400, 280)
        card.setStyleSheet("""
            QFrame  { background: white; border-radius: 25px; border: none; }
            QLabel  { border: none; background: transparent; color: #555555; font-family: 'Poppins'; }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(12)

        lbl_title = QLabel("⚠️  Kategori Tidak Sesuai")
        lbl_title.setFont(QFont('Poppins', 14, QFont.Bold))
        lbl_title.setStyleSheet("color: #E29E21;")
        card_layout.addWidget(lbl_title)

        lbl_msg = QLabel(
            f"<b>'{food_name}'</b> tampaknya bukan termasuk kategori "
            f"<b>{kategori}</b>.<br><br>"
            "Apakah kamu yakin ingin menyimpannya di kategori ini?"
        )
        lbl_msg.setFont(QFont('Poppins', 10))
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("color: #555555;")
        card_layout.addWidget(lbl_msg)

        card_layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_batal = QPushButton("Batal")
        btn_batal.setFixedHeight(50)
        btn_batal.setCursor(Qt.PointingHandCursor)
        btn_batal.setStyleSheet(
            "QPushButton { background-color: white; color: rgba(26,122,52,0.7); "
            "border: 1.5px solid #1A7A34; border-radius: 25px; font-size: 16px; } "
            "QPushButton:hover { color: #1A7A34; }"
        )
        btn_batal.clicked.connect(dlg.reject)

        btn_lanjut = QPushButton("Ya, Lanjutkan")
        btn_lanjut.setFixedHeight(50)
        btn_lanjut.setCursor(Qt.PointingHandCursor)
        btn_lanjut.setFont(QFont('Poppins', 10, QFont.Bold))
        btn_lanjut.setStyleSheet(
            "QPushButton { background-color: #E29E21; color: white; "
            "border-radius: 25px; font-size: 15px; border: none; } "
            "QPushButton:hover { background-color: #c47f10; }"
        )
        btn_lanjut.clicked.connect(dlg.accept)

        btn_row.addWidget(btn_batal)
        btn_row.addWidget(btn_lanjut)
        card_layout.addLayout(btn_row)

        inner.addWidget(card)
        outer.addWidget(overlay)

        return dlg.exec_() == QDialog.Accepted

    # ── Simpan log ────────────────────────────────────────────────────────
    def on_save(self):
        idx  = self.nama.findText(self.nama.currentText(), Qt.MatchExactly)
        code = self.nama.itemData(idx)

        if idx == -1 or code is None:
            return

        try:
            porsi_val = float(self.porsi.text() or 0)
        except ValueError:
            return

        if porsi_val <= 0:
            return

        food_name = self.nama.currentText()
        kategori  = self.waktu.currentText()

        # ── Validasi kategori Snack / Minuman — styled overlay popup ────
        if not self._validate_kategori(food_name, kategori):
            if not self._konfirmasi_kategori_popup(food_name, kategori):
                return
        # ────────────────────────────────────────────────────────────────

        res = {
            "code" : code,
            "porsi": porsi_val,
            "waktu": kategori
        }

        if self.edit_data:
            res["id_log"] = self.edit_data["id_log"]

        self.save_callback(res)
        self.hide()


# ==================  MAIN PAGE  ==================
class LogPage(QWidget):
    log_updated = pyqtSignal()

    def __init__(self, sistem_profil=None, parent=None):
        super().__init__(parent)
        self.sistem_profil = sistem_profil
        self.db            = LogSystem()
        self.popup         = None
        self.current_page  = 0
        self.items_per_page = 8
        self.setStyleSheet("background-color: transparent;")
        self._build_content()

    def _build_content(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        # --- HEADER ---
        h_header_layout = QHBoxLayout()
        text_vbox = QVBoxLayout()
        lbl_title = QLabel("Log Makanan")
        lbl_title.setStyleSheet("color: #1C1C1C; background: transparent; border: none; font-family: 'Montserrat Alternates'; font-size: 32px; font-weight: bold;")
        lbl_sub = QLabel("Catat semua yang kamu makan hari ini")
        lbl_sub.setStyleSheet("color: #6c757d; background: transparent; border: none; font-family: 'Montserrat'; font-size: 14px;")
        text_vbox.addWidget(lbl_title)
        text_vbox.addWidget(lbl_sub)
        h_header_layout.addLayout(text_vbox)
        h_header_layout.addStretch()

        self.action_btn = QPushButton("+ Tambah Makanan")
        self.action_btn.setFixedSize(210, 50)
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setFont(QFont("Poppins", 10, QFont.Bold))
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A7A34;
                color: white;
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: white;
                color: #1A7A34;
                border: 1px solid #1A7A34;
            }
        """)
        self.action_btn.clicked.connect(lambda: self.open_popup())
        h_header_layout.addWidget(self.action_btn)
        root.addLayout(h_header_layout)

        # --- MAIN CARD ---
        self.card = QWidget()
        self.card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.card.setStyleSheet("""
            background: white;
            border-radius: 16px;
            border: 1px solid #1A7A34;
        """)
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setSpacing(0)

        # --- CARD HEADER ---
        card_header_layout = QHBoxLayout()
        card_header_layout.setContentsMargins(10, 10, 10, 5)
        card_header_layout.setSpacing(15)

        lbl_title = QLabel("Daftar Makanan Hari Ini")
        lbl_title.setFont(QFont("Poppins", 20, QFont.Bold))
        lbl_title.setStyleSheet("color: black; border: none;")
        card_header_layout.addWidget(lbl_title)

        card_header_layout.addStretch()

        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Cari Makanan ...")
        self.search_bar.setFixedSize(200, 40)

        search_icon = QIcon(r"./assets/search_icon.png")
        self.search_bar.addAction(search_icon, QLineEdit.LeadingPosition)

        self.search_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #1A7A34;
                border-radius: 20px;
                padding-left: 5px;
                background-color: white;
                color: #555555;
            }
        """)
        self.search_bar.textChanged.connect(self.reset_and_load)
        card_header_layout.addWidget(self.search_bar)

        # Filter Dropdown
        self.filter_waktu = QComboBox()
        self.filter_waktu.setFixedSize(140, 40)
        self.filter_waktu.setView(QListView())
        self.filter_waktu.addItems(["Semua Waktu", "Sarapan", "Makan Siang", "Makan Malam", "Snack", "Minuman"])
        self.filter_waktu.setStyleSheet("""
            QComboBox {
                border: 1px solid #1A7A34;
                border-radius: 20px;
                padding-left: 10px;
                background-color: white;
                color: #666;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border: none;
            }
            QComboBox::down-arrow {
                image: url(./assets/down_arrow.png);
                width: 14px;
                height: 14px;
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
        """)
        self.filter_waktu.currentIndexChanged.connect(self.reset_and_load)
        card_header_layout.addWidget(self.filter_waktu)

        self.card_layout.addLayout(card_header_layout)

        # --- DATA ROWS ---
        self.rows_container = QWidget()
        self.rows_container.setStyleSheet("border: none;")
        self.rows_layout = QGridLayout(self.rows_container)
        self.rows_layout.setContentsMargins(10, 30, 10, 10)
        self.rows_layout.setSpacing(8)

        self.card_layout.addWidget(self.rows_container)
        self.card_layout.addStretch(1)

        # --- FOOTER SECTION ---
        line_container = QWidget()
        line_container.setStyleSheet("border: none; background: transparent;")
        line_container_layout = QHBoxLayout(line_container)
        line_container_layout.setContentsMargins(10, 0, 10, 0)

        footer_line = QFrame()
        footer_line.setFrameShape(QFrame.HLine)
        footer_line.setStyleSheet("background-color: #1A7A34;")
        footer_line.setFixedHeight(1)

        line_container_layout.addWidget(footer_line)
        self.card_layout.addWidget(line_container)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(10, 20, 10, 10)

        self.lbl_count = QLabel("Showing 0 out of 0")
        self.lbl_count.setFont(QFont("Poppins", 10))
        self.lbl_count.setStyleSheet("color: #666; border: none;")

        self.btn_prev = QPushButton("<")
        self.btn_next = QPushButton(">")
        for btn in [self.btn_prev, self.btn_next]:
            btn.setFixedSize(40, 40)
            btn.setStyleSheet("""
                QPushButton { border: 1px solid #1A7A34; border-radius: 12px; color: #1A7A34; font-weight: bold; }
                QPushButton:disabled { border: 1px solid #ccc; color: #ccc; }
                QPushButton:hover { background-color: rgba(26, 122, 52, 0.25); }
            """)

        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)

        self.lbl_total_cal = QLabel("Total Kalori: 0 kcal")
        self.lbl_total_cal.setFont(QFont("Poppins", 12, QFont.Bold))
        self.lbl_total_cal.setStyleSheet("color: #1A7A34; border: none;")

        footer_layout.addWidget(self.lbl_count)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_prev)
        footer_layout.addSpacing(10)
        footer_layout.addWidget(self.btn_next)
        footer_layout.addSpacing(20)
        footer_layout.addWidget(self.lbl_total_cal)

        self.card_layout.addLayout(footer_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container_scroll = QWidget()
        container_scroll.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(container_scroll)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.card)
        main_layout.addStretch(1)

        scroll.setWidget(container_scroll)
        root.addWidget(scroll, stretch=1)
        self.installEventFilter(self)

        self.load_data()

    def reset_and_load(self):
        self.current_page = 0
        self.load_data()

    def next_page(self):
        self.current_page += 1
        self.load_data()

    def prev_page(self):
        self.current_page -= 1
        self.load_data()

    def load_data(self):
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        headers = ["Nama Makanan", "Waktu", "Porsi", "Kalori", "Protein", "Karbohidrat", "Lemak", " ", " "]
        for col, text in enumerate(headers):
            lbl = QLabel(text)
            lbl.setFont(QFont("Poppins", 12, QFont.Bold))  
            lbl.setStyleSheet("color: black; border: none;")
            self.rows_layout.addWidget(lbl, 0, col)

        # Ambil id_user dari session aktif agar log hanya milik user yang login
        _id_user = None
        try:
            if self.sistem_profil and self.sistem_profil.current_profil:
                _id_user = self.sistem_profil.current_profil.get('id_user')
        except Exception:
            pass
        logs = self.db.ReadLog(id_user=_id_user) or []

        search_query  = self.search_bar.text().lower()
        selected_waktu = self.filter_waktu.currentText()
        
        from datetime import date
        today_str = date.today().strftime("%Y-%m-%d")

        filtered_logs = []
        for entry in logs:
            # Hanya ambil log hari ini
            if not str(entry.get('meal_time', '')).startswith(today_str):
                continue
                
            match_search = search_query in entry['food_name'].lower()
            match_waktu  = (selected_waktu == "Semua Waktu" or entry.get('category', '') == selected_waktu)
            if match_search and match_waktu:
                filtered_logs.append(entry)

        total_calories = sum(e.get('cal', 0) for e in filtered_logs)

        # --- PAGINATION ---
        total_items = len(filtered_logs)
        max_pages   = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)

        if self.current_page >= max_pages:
            self.current_page = max_pages - 1
        if self.current_page < 0:
            self.current_page = 0

        start_idx  = self.current_page * self.items_per_page
        end_idx    = start_idx + self.items_per_page
        page_items = filtered_logs[start_idx:end_idx]

        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(end_idx < total_items)

        if not page_items:
            empty_lbl = QLabel("Tidak ada data makanan yang sesuai.")
            empty_lbl.setStyleSheet("color: gray; border: none; padding: 20px;")
            self.rows_layout.addWidget(empty_lbl, 1, 0, 1, 9, Qt.AlignCenter)
            self.lbl_count.setText("Showing 0 out of 0")
            self.lbl_total_cal.setText("Total Kalori: 0.0 kcal")
            return

        for i, entry in enumerate(page_items, start=1):
            line_idx = (i * 2) + 1
            row_idx  = line_idx + 1

            data = [
                entry['food_name'],
                entry.get('category', ''),
                f"{entry['portion']}g",
                f"{entry['cal']} kcal",
                f"{entry['protein']}g",
                f"{entry['carb']}g",
                f"{entry['fat']}g"
            ]

            for col_idx, widget_text in enumerate(data):
                lbl = QLabel(str(widget_text))
                if col_idx == 0:
                    lbl.setFont(QFont("Poppins", 12, QFont.Bold))
                    lbl.setStyleSheet("border: none;")
                else:
                    lbl.setFont(QFont("Poppins", 12))  
                    lbl.setStyleSheet("border: none; color: #555555;")
                self.rows_layout.addWidget(lbl, row_idx, col_idx)

            # Edit Button
            btn_edit = QPushButton()
            btn_edit.setFixedSize(30, 30)
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border-radius: 6px;
                    image: url("assets/icons/State=Default.png");
                }
                QPushButton:hover {
                    background-color: none;
                    border: none;
                    image: url("assets/icons/State=Hover-Edit.png");
                }
            """)
            btn_edit.clicked.connect(lambda _, e=entry: self.open_popup(e))
            self.rows_layout.addWidget(btn_edit, row_idx, 7)

            # Delete Button
            btn_delete = QPushButton()
            btn_delete.setFixedSize(30, 30)
            btn_delete.setCursor(Qt.PointingHandCursor)
            btn_delete.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border-radius: 6px;
                    image: url("assets/icons/State=Default (1).png");
                }
                QPushButton:hover {
                    background-color: #E03030;
                    border: none;
                    image: url("assets/icons/State=Hover-delete.png");
                }
            """)
            btn_delete.clicked.connect(lambda _, e=entry: self.delete_entry(e['id_log'], e['food_name']))
            self.rows_layout.addWidget(btn_delete, row_idx, 8)

            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("background-color: #1A7A34;")
            line.setFixedHeight(1)
            self.rows_layout.addWidget(line, line_idx, 0, 1, 9)

        current_showing = len(page_items)
        self.lbl_count.setText(f"Showing {current_showing} of {total_items} (Page {self.current_page + 1}/{max_pages})")
        self.lbl_total_cal.setText(f"Total Kalori: {total_calories:.1f} kcal")

    def _konfirmasi_hapus_popup(self, food_name: str) -> bool:
        from PyQt5.QtWidgets import QDialog

        main_window = self.window()

        dlg = QDialog(main_window)
        dlg.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dlg.setAttribute(Qt.WA_TranslucentBackground)
        dlg.setModal(True)
        dlg.setFixedSize(main_window.width(), main_window.height())

        outer = QVBoxLayout(dlg)
        outer.setContentsMargins(0, 0, 0, 0)

        overlay = QWidget(dlg)
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 120);")
        overlay.setAttribute(Qt.WA_StyledBackground, True)

        inner = QVBoxLayout(overlay)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setFixedSize(400, 260)
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 25px;
                border: none;
            }
            QLabel {
                border: none;
                background: transparent;
                color: #555555;
                font-family: 'Poppins';
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(12)

        lbl_title = QLabel("🗑️ Hapus Makanan")
        lbl_title.setFont(QFont('Poppins', 14, QFont.Bold))
        lbl_title.setStyleSheet("color: #E03030;")
        card_layout.addWidget(lbl_title)

        lbl_msg = QLabel(
            f"Apakah kamu yakin ingin menghapus\n"
            f"<b>{food_name}</b> dari log makanan?"
        )
        lbl_msg.setFont(QFont('Poppins', 10))
        lbl_msg.setWordWrap(True)
        card_layout.addWidget(lbl_msg)

        card_layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_batal = QPushButton("Batal")
        btn_batal.setFixedHeight(50)
        btn_batal.setCursor(Qt.PointingHandCursor)
        btn_batal.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: rgba(26,122,52,0.7);
                border: 1.5px solid #1A7A34;
                border-radius: 25px;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #1A7A34;
            }
        """)
        btn_batal.clicked.connect(dlg.reject)

        btn_hapus = QPushButton("Ya, Hapus")
        btn_hapus.setFixedHeight(50)
        btn_hapus.setCursor(Qt.PointingHandCursor)
        btn_hapus.setFont(QFont('Poppins', 10, QFont.Bold))
        btn_hapus.setStyleSheet("""
            QPushButton {
                background-color: #E03030;
                color: white;
                border-radius: 25px;
                font-size: 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #C62828;
            }
        """)
        btn_hapus.clicked.connect(dlg.accept)

        btn_row.addWidget(btn_batal)
        btn_row.addWidget(btn_hapus)

        card_layout.addLayout(btn_row)

        inner.addWidget(card)
        outer.addWidget(overlay)

        return dlg.exec_() == QDialog.Accepted

    def open_popup(self, entry_data=None):
        main_window = self.window()
        self.popup = TambahPopup(main_window, self.db, self.save_popup_data, self.close_popup, edit_data=entry_data)
        main_window.installEventFilter(self)

        self.popup.setGeometry(0, 0, main_window.width(), main_window.height())
        self.popup.show()
        self.popup.raise_()

    def save_popup_data(self, res):
        nutrisi = self.db.kalkulator_nutrisi(res['code'], res['porsi'])
        id_user = 1
        try:
            if self.sistem_profil and self.sistem_profil.current_profil:
                id_user = self.sistem_profil.current_profil.get('id_user', 1)
        except Exception:
            pass

        if nutrisi:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if "id_log" in res:
                self.db.UpdateLog(res['id_log'], id_user, res['code'], current_time, res['porsi'],
                    nutrisi['cal'], nutrisi['protein'], nutrisi['carb'], nutrisi['fat'],
                    res['waktu']
                )
            else:
                self.db.CreateLog(
                    id_user, res['code'], current_time, res['porsi'],
                    nutrisi['cal'], nutrisi['protein'], nutrisi['carb'], nutrisi['fat'],
                    res['waktu']
                )

        self.close_popup()
        self.load_data()
        self.log_updated.emit()

    def close_popup(self):
        if self.popup:
            self.popup.hide()

    def delete_entry(self, id_log, food_name):
        if not self._konfirmasi_hapus_popup(food_name):
            return

        self.db.DeleteLog(id_log)
        self.load_data()
        self.log_updated.emit()

    def eventFilter(self, source, event):
        if source == self.window() and event.type() == QEvent.Resize:
            if self.popup and self.popup.isVisible():
                self.popup.resize(event.size())
        return super().eventFilter(source, event)
    
    def show_tambah_makan(self, makanan: dict):
        """Buka popup tambah makanan (mode baru, bukan edit) dengan nama makanan pre-filled."""
        # Buka popup kosong dulu (mode tambah, bukan edit)
        self.open_popup(entry_data=None)
        # Setelah popup terbuka, cari nama makanan di dropdown dan pilih otomatis
        if self.popup and isinstance(self.popup, TambahPopup):
            food_name = makanan.get('food_name', '')
            idx = self.popup.nama.findText(food_name, Qt.MatchExactly)
            if idx < 0:
                # coba partial match
                idx = self.popup.nama.findText(food_name, Qt.MatchContains)
            if idx >= 0:
                self.popup.nama.setCurrentIndex(idx)
            else:
                # Isi teks di QLineEdit dropdown meskipun tidak ada exact match
                self.popup.nama.setEditText(food_name)
            self.popup.update_preview()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LogPage()
    window.show()
    sys.exit(app.exec_())