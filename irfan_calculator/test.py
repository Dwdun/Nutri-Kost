import sys
import os
from datetime import date
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

# Ensure the system can find LogSystem and templates
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from LogSystem import LogSystem
from fatih_GUI.template_halaman import *

class TambahDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db

        self.setWindowTitle("Tambah Makanan")
        self.setFixedSize(300, 300)

        layout = QVBoxLayout()

        # dropdown makanan
        self.nama = QComboBox()
        for food in self.db.GetAllFoods():
            self.nama.addItem(food["food_name"], food["code"])

        layout.addWidget(QLabel("Nama Makanan"))
        layout.addWidget(self.nama)

        # row
        row = QHBoxLayout()

        self.porsi = QLineEdit()
        self.porsi.setPlaceholderText("gram")

        self.waktu = QComboBox()
        self.waktu.addItems(["Sarapan", "Makan Siang", "Makan Malam", "Snack", "Minuman"])

        col1 = QVBoxLayout()
        col1.addWidget(QLabel("Porsi"))
        col1.addWidget(self.porsi)

        col2 = QVBoxLayout()
        col2.addWidget(QLabel("Waktu"))
        col2.addWidget(self.waktu)

        row.addLayout(col1)
        row.addLayout(col2)
        layout.addLayout(row)

        # preview
        self.preview = QLabel("Kalori: 0\nProtein: 0\nKarbo: 0\nLemak: 0")
        self.preview.setStyleSheet("background: #f9f9f9; padding: 5px; border-radius: 5px;")
        layout.addWidget(self.preview)

        # buttons
        btns = QHBoxLayout()
        btn_save = QPushButton("Simpan")
        btn_save.setStyleSheet("background-color: #1A7A34; color: white; border-radius: 6px;")
        btn_cancel = QPushButton("Batal")
        btn_cancel.setStyleSheet("background-color: #d9534f; color: white; border-radius: 6px;")

        btn_save.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

        self.setLayout(layout)

        # events
        self.nama.currentIndexChanged.connect(self.update_preview)
        self.porsi.textChanged.connect(self.update_preview)

        self.update_preview()

    def update_preview(self):
        try:
            porsi = float(self.porsi.text()) if self.porsi.text() else 0
        except:
            porsi = 0

        code = self.nama.currentData()
        data = self.db.kalkulator_nutrisi(code, porsi)

        if data:
            self.preview.setText(
                f"Kalori: {data['cal']} kcal\n"
                f"Protein: {data['protein']} g\n"
                f"Karbo: {data['carb']} g\n"
                f"Lemak: {data['fat']} g"
            )

    def get_data(self):
        return {
            "code": self.nama.currentData(),
            "porsi": float(self.porsi.text()),
            "waktu": self.waktu.currentText()
        }

# ================== MAIN PAGE ==================
class DashboardPage(PageTemplate):
    PAGE_NAME = "Log Makanan"
    PAGE_DESC = "Catat semua yang kamu makan hari ini"
    NAV_INDEX = 2 

    def __init__(self):
        self.db = LogSystem()
        super().__init__()

    def build_content(self, container):
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
                border-radius: 
                12px; }
            QPushButton:hover { 
                background-color: white; 
                color: #1A7A34; 
                border: 1px solid #1A7A34; }
        """)
        self.action_btn.clicked.connect(self.open_tambah_dialog)
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
        lbl_title.setStyleSheet("""
                        color: black; 
                        border: none;
                    """)
        self.card_layout.addWidget(lbl_title)

        # Container for dynamic rows
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

        # Left: Showing X of Y
        self.lbl_count = QLabel("Showing 0 out of 0")
        self.lbl_count.setFont(self.font_body(10))
        self.lbl_count.setStyleSheet("color: #666; border: none;")

        # Right: Total Calories
        self.lbl_total_cal = QLabel("Total Kalori: 0 kcal")
        self.lbl_total_cal.setFont(self.font_label(12, bold=True))
        self.lbl_total_cal.setStyleSheet("color: #1A7A34; border: none;")

        footer_layout.addWidget(self.lbl_count)
        footer_layout.addStretch() # Pushes the next label to the far right
        footer_layout.addWidget(self.lbl_total_cal)

        self.card_layout.addLayout(footer_layout)
        self.card_layout.addStretch()

        container.layout().addWidget(self.card)
        self.load_data()
        
    def load_data(self):
        """Clears the current rows and reloads from LogSystem"""
        # 1. Clear existing rows
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 2. Add Header
        headers = ["Nama Makanan", "Waktu", "Porsi", "Kalori", "Protein", "Karbohidrat", "Lemak", " ", ""]
        for col, text in enumerate(headers):
            lbl = QLabel(text)
            lbl.setFont(self.font_label(12, bold=True))
            lbl.setStyleSheet("color: black; border: none; padding-bottom: 0px;")
            self.rows_layout.addWidget(lbl, 0, col)

        # 3. Fetch from DB
        logs = self.db.ReadLog()
        total_calories = 0

        if not logs:
            empty_lbl = QLabel("Belum ada data makan hari ini.")
            empty_lbl.setStyleSheet("color: gray; border: none; padding: 20px;")
            self.rows_layout.addWidget(empty_lbl, 1, 0, 1, 7, Qt.AlignCenter)
            return

        # 4. Create a row for each entry
        for i, entry in enumerate(logs, start=1):
            line_idx = (i * 2) + 1  # Data rows: 1, 3, 5, 7...
            row_idx = line_idx + 1 # Line rows: 2, 4, 6, 8...

            total_calories += entry.get('cal') or 0
            
            # Create data labels
            data = [
                entry['food_name'], 
                entry['meal_time'], 
                f"{entry['portion']}g",  
                f"{entry['cal']} kcal",
                f"{entry['protein']}g", 
                f"{entry['carb']}g", 
                f"{entry['fat']}g"
            ]

            # Style and Add to Grid
            for col_idx, widget_text in enumerate(data):
                lbl = QLabel(str(widget_text))
                lbl.setFont(self.font_body(12))
                lbl.setStyleSheet("border: none; color: #333;")
                self.rows_layout.addWidget(lbl, row_idx, col_idx)

            # Delete Button
            btn_edit = QPushButton("Edit")
            btn_edit.setFixedSize(30, 30)
            btn_edit.setStyleSheet("""
                QPushButton { background-color: #1A7A34; color: white; border-radius: 6px;}
                QPushButton:hover { background-color: white; color: #1A7A34; border: 1px solid #1A7A34; }
            """)
            btn_edit.clicked.connect(lambda _, id=entry['id_log']: self.delete_entry(id))
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

            # --- THE BORDER/SEPARATOR ---
            # Create a horizontal line widget
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Plain)
            line.setLineWidth(1)
            line.setStyleSheet("color: #1A7A34; border: none; background-color: #1A7A34;")
            line.setFixedHeight(1)
            
            # Add the line to the grid, spanning all 9 columns
            self.rows_layout.addWidget(line, line_idx, 0, 1, 9)

        current_count = len(logs)
        self.lbl_count.setText(f"Showing {current_count} out of {current_count}")
        self.lbl_total_cal.setText(f"Total Kalori: {total_calories:.1f} kcal")

    def open_tambah_dialog(self):
        dialog = TambahDialog(self.db)
        if dialog.exec_():
            res = dialog.get_data()

            # calculate nutrition
            nutrisi = self.db.kalkulator_nutrisi(res['code'], res['porsi'])

            if nutrisi:
                self.db.CreateLog(
                    1,  # TEMP id_user (replace if you have auth)
                    res['code'],
                    res['waktu'],
                    res['porsi'],
                    nutrisi['cal'],
                    nutrisi['protein'],
                    nutrisi['carb'],
                    nutrisi['fat'],
                    res['waktu']  # category (you were using same value anyway)
                )

            self.load_data()

    def delete_entry(self, id_log):
        self.db.DeleteLog(id_log)
        self.load_data()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DashboardPage()
    window.show()
    sys.exit(app.exec_())