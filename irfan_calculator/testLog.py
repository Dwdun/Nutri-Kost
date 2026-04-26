import sys
from datetime import date
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from LogSystem import LogSystem


# ================== DIALOG ==================
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
        layout.addWidget(self.preview)

        # buttons
        btns = QHBoxLayout()
        btn_save = QPushButton("Simpan")
        btn_cancel = QPushButton("Batal")

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
            porsi = float(self.porsi.text())
        except:
            porsi = 100

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

# ================== DIALOG EDIT ==================
class EditDialog(TambahDialog):
    def __init__(self, db, current_data):
        super().__init__(db)
        self.setWindowTitle("Edit Log Makanan")
        
        # Set the current values
        index = self.nama.findData(current_data['food_code'])
        self.nama.setCurrentIndex(index)
        self.nama.setEnabled(False)  # <--- User cannot change the food
        
        self.porsi.setText(str(current_data['porsi']))
        self.waktu.setCurrentText(current_data['waktu_makan'])
        
        self.update_preview()

    def get_updated_data(self):
        return {
            "porsi": float(self.porsi.text()),
            "waktu": self.waktu.currentText()
        }
    
# ================== MAIN WINDOW ==================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db = LogSystem()

        self.setWindowTitle("Log Makanan")
        self.setFixedSize(800, 400)

        layout = QVBoxLayout()

        # table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Nama", "Waktu", "Porsi", "Kalori",
            "Protein", "Karbo", "Lemak", "Aksi"
        ])

        layout.addWidget(self.table)

        # button
        btn_add = QPushButton("Tambah Data")
        btn_add.clicked.connect(self.open_dialog)
        layout.addWidget(btn_add)

        self.setLayout(layout)

        self.load_data()

    def load_data(self):
        self.table.setRowCount(0)
        data = self.db.ReadLog()

        for row_data in data:
            row = self.table.rowCount()
            self.table.insertRow(row)

            values = [
                row_data["food_name"],
                row_data["waktu_makan"],
                str(row_data["porsi"]),
                str(row_data["cal"]),
                str(row_data["protein"]),
                str(row_data["carb"]),
                str(row_data["fat"])
            ]

            for col, val in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(val))

            # 1. Create a container widget and a horizontal layout
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(5)

            # 2. Create the Edit button
            btn_edit = QPushButton("Edit")
            btn_edit.setStyleSheet("background-color: #1A7A34; color: white;") # Optional: make it orange
            btn_edit.clicked.connect(
                lambda _, d=row_data: self.open_edit_dialog(d)
            )

            # 3. Create the Delete button
            btn_delete = QPushButton("Hapus")
            btn_delete.setStyleSheet("background-color: #d9534f; color: white;") # Optional: make it red
            btn_delete.clicked.connect(
                lambda _, id=row_data["log_id"]: self.delete_data(id)
            )

            # 4. Add buttons to layout, then set the container to the table cell
            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            
            self.table.setCellWidget(row, 7, action_widget)

    def delete_data(self, log_id):
        self.db.DeleteLog(log_id)
        self.load_data()

    def open_dialog(self):
        dialog = TambahDialog(self.db)

        if dialog.exec_():
            data = dialog.get_data()

            self.db.CreateLog(
                data["code"],
                data["porsi"],
                data["waktu"],
                str(date.today())
            )

            self.load_data()

    def open_edit_dialog(self, current_data):
        dialog = EditDialog(self.db, current_data)

        if dialog.exec_():
            new_data = dialog.get_updated_data()
            
            self.db.UpdateLog(
                log_id=current_data["log_id"],
                food_code=current_data["food_code"],
                porsi=new_data["porsi"],
                waktu_makan=new_data["waktu"],
                tanggal=str(date.today())
            )
            self.load_data()


# ================== RUN ==================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())