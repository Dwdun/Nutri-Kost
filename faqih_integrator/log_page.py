import sys
import os
from datetime import date
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QFont, QDoubleValidator, QIcon

# Agar bisa load module irfan_calculator
from irfan_calculator.LogSystem import LogSystem

class TambahPopup(QWidget):
    def __init__(self, parent, db, save_callback, cancel_callback, edit_data=None):
        super().__init__(parent)
        self.db = db
        self.save_callback = save_callback
        self.cancel_callback = cancel_callback
        self.edit_data = edit_data 
        
        # Check apakah ini "edit beneran" (punya id_log) atau "pre-fill dari search"
        self.is_real_edit = (self.edit_data is not None) and ('id_log' in self.edit_data)
        
        self.btn_save = QPushButton("Simpan" if self.is_real_edit else "Tambah")
        
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignCenter)

        self.card = QFrame()
        self.card.setFixedSize(380, 450)
        self.card.setStyleSheet("""
            QFrame { background: white; border-radius: 25px; border: none; }
            QLabel { border: none; background: transparent; color: #555555; font-family: 'Poppins'; }
            #FoodInput { padding: 5px 15px; border: none; border-radius: 20px; background: rgba(26, 122, 52, 0.25); color: #1A7A34; font-family: 'Poppins'; }
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
        self.nama.lineEdit().setPlaceholderText("Ketik di sini")
        self.nama.lineEdit().setStyleSheet("background: transparent; border: none; color: #1A7A34; padding-left: 5px; font-family: 'Poppins';")
        
        self.nama.setView(QListView())
        self.nama.view().window().setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.nama.view().window().setAttribute(Qt.WA_TranslucentBackground)

        food_names = []
        try:
            for food in self.db.GetAllFoods():
                self.nama.addItem(food["food_name"], food["code"])
                food_names.append(food["food_name"])
        except Exception as e:
            print(f"[TambahPopup] Mocking GetAllFoods due to DB error: {e}")

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
        self.porsi.setStyleSheet("QLineEdit { border: none; border-radius: 20px; padding-left: 15px; background: rgba(26, 122, 52, 0.25); color: #1A7A34; font-family: 'Poppins'; }")
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
                font-family: 'Poppins';
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
                font-family: 'Poppins';
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
            container.setAlignment(Qt.AlignCenter)
            container.setSpacing(2)
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

        self.lay_cal, self.val_cal = create_nut_col("Kalori")
        self.lay_pro, self.val_pro = create_nut_col("Protein")
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
        btn_cancel.setStyleSheet("QPushButton { background-color: white; color: rgba(26, 122, 52, 0.5); border: 1px solid #1A7A34; border-radius: 25px; font-size: 20px; font-family: 'Poppins'; } QPushButton:hover { color: #1A7A34 ; }")
        
        self.btn_save.setFixedHeight(50)
        self.btn_save.setStyleSheet("QPushButton { background-color: #1A7A34; color: white; border-radius: 25px; font-weight: bold; font-size: 20px; font-family: 'Poppins'; }")

        self.btn_save.clicked.connect(self.on_save)
        btn_cancel.clicked.connect(self.cancel_callback)
        btns.addWidget(btn_cancel)
        btns.addWidget(self.btn_save)
        card_layout.addLayout(btns)
        main_layout.addWidget(self.card)

        self.nama.currentIndexChanged.connect(self.update_preview)
        self.porsi.textChanged.connect(self.update_preview)

        # --- APPLY EDIT DATA ---
        if self.edit_data:
            idx = self.nama.findText(self.edit_data.get('food_name', ''))
            if idx >= 0:
                self.nama.setCurrentIndex(idx)
            
            if self.is_real_edit:
                self.nama.setEnabled(False) 
            
            if 'portion' in self.edit_data and self.edit_data['portion']:
                self.porsi.setText(str(self.edit_data['portion']))
            if 'meal_time' in self.edit_data and self.edit_data['meal_time']:
                self.waktu.setCurrentText(self.edit_data['meal_time'])

        self.update_preview()

    def update_preview(self):
        try:
            porsi = float(self.porsi.text()) if self.porsi.text() else 0
        except: 
            porsi = 0

        idx = self.nama.findText(self.nama.currentText(), Qt.MatchExactly)
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

    def on_save(self):
        idx = self.nama.findText(self.nama.currentText(), Qt.MatchExactly)
        code = self.nama.itemData(idx)
        
        if idx == -1 or code is None: 
            return

        try:
            porsi_val = float(self.porsi.text() or 0)
        except ValueError:
            return

        if porsi_val <= 0:
            return

        res = {
            "code": code,
            "porsi": porsi_val,
            "waktu": self.waktu.currentText()
        }

        if self.is_real_edit:
            res["id_log"] = self.edit_data["id_log"]

        self.save_callback(res)
        self.hide()


# ================== MAIN PAGE ==================
class LogPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = LogSystem()
        self.popup = None
        self.current_page = 0
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
        text_vbox.setSpacing(4)
        
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
        self.action_btn.setStyleSheet("""
            QPushButton { 
                background-color: #1A7A34; 
                color: white; 
                border-radius: 16px; 
                font-family: 'Poppins';
                font-size: 14px;
                font-weight: bold;
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

        # Area Scroll untuk konten log
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container_scroll = QWidget()
        container_scroll.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(container_scroll)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- MAIN CARD ---
        self.card = QWidget()
        self.card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.card.setStyleSheet("""
                QWidget {
                    background: white;
                    border-radius: 16px; 
                    border: 1px solid #1A7A34;
                }
            """)
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setSpacing(0)

        # --- CARD HEADER ---
        card_header_layout = QHBoxLayout()
        card_header_layout.setContentsMargins(10, 10, 10, 5)
        card_header_layout.setSpacing(15)

        lbl_title_card = QLabel("Daftar Makanan Hari Ini")
        lbl_title_card.setStyleSheet("color: black; border: none; font-family: 'Poppins'; font-size: 20px; font-weight: bold;")
        card_header_layout.addWidget(lbl_title_card)
        
        card_header_layout.addStretch()

        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Cari Makanan ...")
        self.search_bar.setFixedSize(200, 40)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #1A7A34;
                border-radius: 20px;
                padding-left: 15px;
                background-color: white;
                color: #555555;
                font-family: 'Poppins';
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
                font-family: 'Poppins';
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
                font-family: 'Poppins';
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
        self.lbl_count.setStyleSheet("color: #666; border: none; font-family: 'Poppins'; font-size: 11px;")

        self.btn_prev = QPushButton("<")
        self.btn_next = QPushButton(">")
        for btn in [self.btn_prev, self.btn_next]:
            btn.setFixedSize(40, 40)
            btn.setStyleSheet("""
                QPushButton { border: 1px solid #1A7A34; border-radius: 12px; color: #1A7A34; font-weight: bold; font-family: 'Poppins';}
                QPushButton:disabled { border: 1px solid #ccc; color: #ccc; }
                QPushButton:hover { background-color: rgba(26, 122, 52, 0.25); }
            """)
        
        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)

        self.lbl_total_cal = QLabel("Total Kalori: 0 kcal")
        self.lbl_total_cal.setStyleSheet("color: #1A7A34; border: none; font-family: 'Poppins'; font-size: 14px; font-weight: bold;")

        footer_layout.addWidget(self.lbl_count)
        footer_layout.addStretch() 
        footer_layout.addWidget(self.btn_prev)
        footer_layout.addSpacing(10)
        footer_layout.addWidget(self.btn_next)
        footer_layout.addSpacing(20)
        footer_layout.addWidget(self.lbl_total_cal)

        self.card_layout.addLayout(footer_layout)

        main_layout.addWidget(self.card)
        main_layout.addStretch(1)

        scroll.setWidget(container_scroll)
        root.addWidget(scroll, stretch=1)

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
            lbl.setStyleSheet("color: black; border: none; font-family: 'Poppins'; font-size: 14px; font-weight: bold;")
            self.rows_layout.addWidget(lbl, 0, col)

        # Fetch Raw Logs
        try:
            logs = self.db.ReadLog() or []
        except Exception as e:
            print(f"[LogPage] Mocking logs due to DB error: {e}")
            logs = []
        
        search_query = self.search_bar.text().lower()
        selected_waktu = self.filter_waktu.currentText()
        
        filtered_logs = []
        for entry in logs:
            match_search = search_query in entry['food_name'].lower()
            match_waktu = (selected_waktu == "Semua Waktu" or entry['meal_time'] == selected_waktu)
            
            if match_search and match_waktu:
                filtered_logs.append(entry)

        # Calculate total calories for the whole filtered list
        total_calories = sum(e.get('cal', 0) for e in filtered_logs)

        # --- PAGINATION LOGIC ---
        total_items = len(filtered_logs)
        max_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)

        if self.current_page >= max_pages:
            self.current_page = max_pages - 1
        if self.current_page < 0:
            self.current_page = 0

        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = filtered_logs[start_idx:end_idx]

        # Update button states
        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(end_idx < total_items)

        if not page_items:
            empty_lbl = QLabel("Tidak ada data makanan yang sesuai.")
            empty_lbl.setStyleSheet("color: gray; border: none; padding: 20px; font-family: 'Poppins';")
            self.rows_layout.addWidget(empty_lbl, 1, 0, 1, 9, Qt.AlignCenter)
            self.lbl_count.setText("Showing 0 out of 0")
            self.lbl_total_cal.setText("Total Kalori: 0.0 kcal")
            return

        for i, entry in enumerate(page_items, start=1):
            line_idx = (i * 2) + 1  
            row_idx = line_idx + 1 

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

                if col_idx == 0:
                    lbl.setStyleSheet("border: none; font-family: 'Poppins'; font-size: 13px; font-weight: bold; color: black;")
                else:
                    lbl.setStyleSheet("border: none; color: #555555; font-family: 'Poppins'; font-size: 13px;")
                
                self.rows_layout.addWidget(lbl, row_idx, col_idx)

            # --- Edit Button ---
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

            # --- Delete Button ---
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
            btn_delete.clicked.connect(lambda _, id=entry['id_log']: self.delete_entry(id))
            self.rows_layout.addWidget(btn_delete, row_idx, 8)

            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("background-color: #1A7A34;")
            line.setFixedHeight(1)
            self.rows_layout.addWidget(line, line_idx, 0, 1, 9)

        # Update labels
        current_showing = len(page_items)
        self.lbl_count.setText(f"Showing {current_showing} of {total_items} (Page {self.current_page + 1}/{max_pages})")
        self.lbl_total_cal.setText(f"Total Kalori: {total_calories:.1f} kcal")

    def open_popup(self, entry_data=None):
        main_window = self.window()
        self.popup = TambahPopup(main_window, self.db, self.save_popup_data, self.close_popup, edit_data=entry_data)
        main_window.installEventFilter(self) 
        
        self.popup.setGeometry(0, 0, main_window.width(), main_window.height())
        self.popup.show()
        self.popup.raise_()

    def show_tambah_makan(self, makanan: dict):
        # Dipanggil oleh main_window.py ketika makanan dipilih dari SearchPage
        entry_data = {
            'food_name': makanan.get('food_name'),
            'portion': 100,
            'meal_time': "Sarapan"
        }
        self.open_popup(entry_data=entry_data)

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
                self.db.CreateLog(
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
