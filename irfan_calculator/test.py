import sys
import os
from datetime import date
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QFont, QDoubleValidator

# Ensure the system can find LogSystem and templates
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from LogSystem import LogSystem
from fatih_GUI.template_halaman import *

class TambahPopup(QWidget):
    def __init__(self, parent, db, save_callback, cancel_callback, edit_data=None):
        super().__init__(parent)
        self.db = db
        self.save_callback = save_callback
        self.cancel_callback = cancel_callback
        self.edit_data = edit_data 
        
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignCenter)

        self.card = QFrame()
        self.card.setFixedSize(380, 450)
        self.card.setStyleSheet("""
            QFrame { background: white; border-radius: 25px; border: none; }
            QLabel { border: none; background: transparent; color: #333; font-family: 'Poppins'; }
            #FoodInput { padding: 5px 15px; border: none; border-radius: 20px; background: #CDE2D4; color: #1A7A34; }
            #FoodInput:disabled { background: #E0E0E0; color: #888; }
            #FoodInput::drop-down { width: 0px; border: none; }
            QComboBox QAbstractItemView {
                background-color: white; border: 1px solid #1A7A34; border-radius: 12px;
                selection-background-color: #CDE2D4; selection-color: #1A7A34; outline: none;
            }
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
        self.nama.lineEdit().setStyleSheet("background: transparent; border: none; color: #1A7A34; padding-left: 5px;")
        
        self.nama.setView(QListView())
        self.nama.view().window().setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.nama.view().window().setAttribute(Qt.WA_TranslucentBackground)

        food_names = []
        for food in self.db.GetAllFoods():
            self.nama.addItem(food["food_name"], food["code"])
            food_names.append(food["food_name"])

        completer = QCompleter(food_names, self.nama)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.nama.setCompleter(completer)
        card_layout.addWidget(self.nama)

        # --- ROW: PORSI & WAKTU ---
        row = QHBoxLayout()
        col1 = QVBoxLayout()
        col1.addWidget(QLabel("Porsi (gram/ml)"))
        self.porsi = QLineEdit()
        self.porsi.setPlaceholderText("0")
        self.porsi.setFixedHeight(45)
        self.porsi.setStyleSheet("QLineEdit { border: none; border-radius: 20px; padding-left: 15px; background: #CDE2D4; color: #1A7A34; }")
        self.porsi.setValidator(QDoubleValidator(0.0, 10000.0, 2))
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
                background: none;
                
            }
            QComboBox QAbstractItemView {
                border: none;
                border-radius: 0px;
                outline: none;
                background-color: white;
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
            txt_lbl.setStyleSheet("color: #333; font-weight: normal; border: none;")
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
        btn_cancel.setStyleSheet("QPushButton { background-color: white; color: rgba(26, 122, 52, 0.5); border: 1px solid #1A7A34; border-radius: 25px; font-size: 20px; } QPushButton:hover { color: #1A7A34 ; }")
        
        btn_save = QPushButton("Simpan" if self.edit_data else "Tambah")
        btn_save.setFixedHeight(50)
        btn_save.setStyleSheet("QPushButton { background-color: #1A7A34; color: white; border-radius: 25px; font-weight: bold; font-size: 20px; }")

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
            self.update_preview()

    def update_preview(self):
        try:
            porsi = float(self.porsi.text()) if self.porsi.text() else 0
        except: porsi = 0

        idx = self.nama.currentIndex()
        code = self.nama.itemData(idx) if idx >= 0 else None
        
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

    def on_save(self):
        idx = self.nama.currentIndex()
        code = self.nama.itemData(idx)
        if idx == -1 or code is None: return

        res = {
            "code": code,
            "porsi": float(self.porsi.text() or 0),
            "waktu": self.waktu.currentText()
        }

        if self.edit_data:
            res["id_log"] = self.edit_data["id_log"]

        self.save_callback(res)
        self.hide()
    
# ================== MAIN PAGE ==================
class DashboardPage(PageTemplate):
    PAGE_NAME = "Log Makanan"
    PAGE_DESC = "Catat semua yang kamu makan hari ini"
    NAV_INDEX = 2 

    def __init__(self):
        self.db = LogSystem()
        self.popup = None
        super().__init__()

    def build_content(self, container):
        self.container = container
        main_layout = self._scroll.widget().layout()

        # --- HEADER ---
        h_header_layout = QHBoxLayout()
        text_vbox = QVBoxLayout()
        text_vbox.addWidget(self._page_title)
        text_vbox.addWidget(self._page_desc)
        h_header_layout.addLayout(text_vbox)
        h_header_layout.addStretch()

        self.action_btn = QPushButton("+ Tambah Makanan")
        self.action_btn.setFixedSize(210, 56)
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setFont(self.font_label(12, bold=True))
        self.action_btn.setStyleSheet("""
            QPushButton { 
                background-color: #1A7A34; 
                color: white; 
                border-radius: 12px; 
            }
            QPushButton:hover { 
                background-color: white; 
                color: #1A7A34; 
                border: 1px solid #1A7A34; 
            }
        """)
        self.action_btn.clicked.connect(lambda: self.open_popup())
        h_header_layout.addWidget(self.action_btn)
        main_layout.insertLayout(0, h_header_layout)

        # --- MAIN CARD ---
        self.card = QWidget()
        self.card.setStyleSheet("""
                background: white;
                border-radius: 16px; 
                border: 1px solid #1A7A34;
            """)
        self.card_layout = QVBoxLayout(self.card)
        
        lbl_title = QLabel("Daftar Makanan Hari Ini")
        lbl_title.setFont(self.font_title(16))
        lbl_title.setContentsMargins(10, 10, 10, 10)
        lbl_title.setStyleSheet("color: black; border: none;")
        self.card_layout.addWidget(lbl_title)

        self.rows_container = QWidget()
        self.rows_container.setStyleSheet("border: none;")
        self.rows_layout = QGridLayout(self.rows_container)
        self.rows_layout.setContentsMargins(10, 10, 10, 10)
        self.rows_layout.setSpacing(8)

        self.card_layout.addWidget(self.rows_container)
        self.card_layout.addStretch(1)

        # --- FOOTER SECTION ---
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(10, 20, 10, 10)

        self.lbl_count = QLabel("Showing 0 out of 0")
        self.lbl_count.setFont(self.font_body(10))
        self.lbl_count.setStyleSheet("color: #666; border: none;")

        self.lbl_total_cal = QLabel("Total Kalori: 0 kcal")
        self.lbl_total_cal.setFont(self.font_label(12, bold=True))
        self.lbl_total_cal.setStyleSheet("color: #1A7A34; border: none;")

        footer_layout.addWidget(self.lbl_count)
        footer_layout.addStretch() 
        footer_layout.addWidget(self.lbl_total_cal)

        self.card_layout.addLayout(footer_layout)
        self.card_layout.addStretch()

        container.layout().addWidget(self.card)
        self.container.installEventFilter(self)

        self.load_data()
        
    def load_data(self):
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        headers = ["Nama Makanan", "Waktu", "Porsi", "Kalori", "Protein", "Karbo", "Lemak", " ", " "]
        for col, text in enumerate(headers):
            lbl = QLabel(text)
            lbl.setFont(self.font_label(12, bold=True))
            lbl.setStyleSheet("color: black; border: none;")
            self.rows_layout.addWidget(lbl, 0, col)

        logs = self.db.ReadLog()
        total_calories = 0

        if not logs:
            empty_lbl = QLabel("Belum ada data makan hari ini.")
            empty_lbl.setStyleSheet("color: gray; border: none; padding: 20px;")
            self.rows_layout.addWidget(empty_lbl, 1, 0, 1, 9, Qt.AlignCenter)
            return

        for i, entry in enumerate(logs, start=1):
            line_idx = (i * 2) + 1  
            row_idx = line_idx + 1 

            total_calories += entry.get('cal') or 0
            
            data = [
                entry['food_name'], 
                entry['meal_time'], 
                f"{entry['portion']}g",  
                f"{entry['cal']} kcal",
                f"{entry['protein']}g", 
                f"{entry['carb']}g", 
                f"{entry['fat']}g"
            ]

            for col_idx, widget_text in enumerate(data):
                lbl = QLabel(str(widget_text))
                lbl.setFont(self.font_body(12))
                lbl.setStyleSheet("border: none; color: #333;")
                self.rows_layout.addWidget(lbl, row_idx, col_idx)

            # Edit Button
            btn_edit = QPushButton("Edit")
            btn_edit.setFixedSize(30, 30)
            btn_edit.setStyleSheet("""
                QPushButton { background-color: #1A7A34; color: white; border-radius: 6px;}
                QPushButton:hover { background-color: white; color: #1A7A34; border: 1px solid #1A7A34; }
            """)
            btn_edit.clicked.connect(lambda _, e=entry: self.open_popup(e))
            self.rows_layout.addWidget(btn_edit, row_idx, 7)

            # Delete Button
            btn_delete = QPushButton("Del")
            btn_delete.setFixedSize(30, 30)
            btn_delete.setStyleSheet("""
                QPushButton { background-color: #E03030; color: white; border-radius: 6px;}
                QPushButton:hover { background-color: white; color: #E03030; border: 1px solid #E03030; }
            """)
            btn_delete.clicked.connect(lambda _, id=entry['id_log']: self.delete_entry(id))
            self.rows_layout.addWidget(btn_delete, row_idx, 8)

            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("background-color: #1A7A34;")
            line.setFixedHeight(1)
            self.rows_layout.addWidget(line, line_idx, 0, 1, 9)

        current_count = len(logs)
        self.lbl_count.setText(f"Showing {current_count} out of {current_count}")
        self.lbl_total_cal.setText(f"Total Kalori: {total_calories:.1f} kcal")

    def open_popup(self, entry_data=None):
        main_window = self.window()
        # Initialize popup with optional entry_data
        self.popup = TambahPopup(main_window, self.db, self.save_popup_data, self.close_popup, edit_data=entry_data)
        main_window.installEventFilter(self) 
        
        self.popup.setGeometry(0, 0, main_window.width(), main_window.height())
        self.popup.show()
        self.popup.raise_()

    def save_popup_data(self, res):
        nutrisi = self.db.kalkulator_nutrisi(res['code'], res['porsi'])

        if nutrisi:
            if "id_log" in res:
                self.db.UpdateLog(
                    res['id_log'],
                    1,
                    res['code'],
                    res['waktu'],
                    res['porsi'],
                    nutrisi['cal'],
                    nutrisi['protein'],
                    nutrisi['carb'],
                    nutrisi['fat'],
                    res['waktu'] 
                )
            else:
                # Create new log
                self.db.CreateLog(
                    1, # Default user_id
                    res['code'],
                    res['waktu'],
                    res['porsi'],
                    nutrisi['cal'],
                    nutrisi['protein'],
                    nutrisi['carb'],
                    nutrisi['fat'],
                    res['waktu']
                )

        self.close_popup()
        self.load_data()

    def close_popup(self):
        if self.popup:
            self.popup.hide()

    def delete_entry(self, id_log):
        self.db.DeleteLog(id_log)
        self.load_data()

    def eventFilter(self, source, event):
        if source == self.window() and event.type() == QEvent.Resize:
            if self.popup and self.popup.isVisible():
                self.popup.resize(event.size())
        return super().eventFilter(source, event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DashboardPage()
    window.show()
    sys.exit(app.exec_())