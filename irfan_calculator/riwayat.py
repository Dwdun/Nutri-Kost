import sys
import os
import sqlite3
import csv
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontMetrics, QIcon

# Path Configuration
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bima_scrapper", "nutrikost.db"))

from fatih_GUI.toast_notification import show_toast, TOAST_SUCCESS, TOAST_ERROR

def font_body(size):
    return QFont("Poppins", size)

def font_label(bold=False):
    f = QFont("Poppins", 10)
    f.setBold(bold)
    return f

class RiwayatPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: transparent;")
        self._build_content()

    def _build_content(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        # --- HEADER ---
        h_header_layout = QHBoxLayout()
        text_vbox = QVBoxLayout()
        lbl_title = QLabel("Riwayat Nutrisi")
        lbl_title.setStyleSheet("color: #1C1C1C; background: transparent; border: none; font-family: 'Montserrat Alternates'; font-size: 32px; font-weight: bold;")
        lbl_sub = QLabel("Tinjau kembali pola makan harianmu")
        lbl_sub.setStyleSheet("color: #6c757d; background: transparent; border: none; font-family: 'Montserrat'; font-size: 14px;")
        text_vbox.addWidget(lbl_title)
        text_vbox.addWidget(lbl_sub)
        h_header_layout.addLayout(text_vbox)
        h_header_layout.addStretch()

        self.action_btn = QPushButton("Export CSV")
        self.action_btn.setFixedSize(145, 56)
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setFont(font_label(bold=True))
        self.action_btn.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #156329;
            }
        """)
        self.action_btn.clicked.connect(self.export_to_csv)
        h_header_layout.addWidget(self.action_btn)
        root.addLayout(h_header_layout)

        # --- Filter Bar Container ---
        filter_container = QFrame()
        filter_container.setFixedHeight(48) 
        filter_container.setMaximumWidth(400)
        filter_container.setStyleSheet('QFrame { background-color: #1A7A34; border-radius: 24px; }')

        filter_layout = QHBoxLayout(filter_container)
        filter_layout.setContentsMargins(2, 2, 2, 2)
        filter_layout.setSpacing(0)

        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(False) 

        filters = ["7 Hari", "14 Hari", "30 Hari", "Bulan ini"]
        for i, text in enumerate(filters):
            btn = QPushButton(text)
            btn.setCheckable(True) 
            btn.setFixedWidth(90)
            btn.setFont(font_body(12))
            btn.setStyleSheet('''
                QPushButton {
                    background-color: transparent;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 22px;
                    outline: none;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.2);
                    color: white;
                    border: none;
                    border-radius: 22px;
                }
                QPushButton:checked {
                    background-color: white;
                    color: #1A7A34;
                    border: none;
                    border-radius: 22px;
                }
            ''')
            btn.clicked.connect(lambda checked, b=btn: self.handle_filter_click(b))
            self.filter_group.addButton(btn, i)
            filter_layout.addWidget(btn, 1) 

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container_scroll = QWidget()
        container_scroll.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(container_scroll)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)

        main_layout.addWidget(filter_container)

        # --- DYNAMIC CONTENT AREA ---
        self.cards_layout = QVBoxLayout()
        main_layout.addLayout(self.cards_layout)
        main_layout.addStretch()

        scroll.setWidget(container_scroll)
        root.addWidget(scroll)
        self.refresh_data()

    def handle_filter_click(self, clicked_btn):
        if clicked_btn.isChecked():
            for btn in self.filter_group.buttons():
                if btn != clicked_btn:
                    btn.setChecked(False)
        
        self.refresh_data()

    def refresh_data(self):
        for i in reversed(range(self.cards_layout.count())): 
            widget = self.cards_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        condition = ""
        checked_btn = self.filter_group.checkedButton()
        if checked_btn:
            text = checked_btn.text()
            if text == "7 Hari":
                condition = "WHERE DATE(l.meal_time) >= DATE('now', '-7 days')"
            elif text == "14 Hari":
                condition = "WHERE DATE(l.meal_time) >= DATE('now', '-14 days')"
            elif text == "30 Hari":
                condition = "WHERE DATE(l.meal_time) >= DATE('now', '-30 days')"
            elif text == "Bulan ini":
                condition = "WHERE strftime('%Y-%m', l.meal_time) = strftime('%Y-%m', 'now')"

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT calory FROM ProfilUser LIMIT 1")
            res = cursor.fetchone()
            goal_cal = (res[0] if res and res[0] is not None else 2000)

            query = f"""
                SELECT 
                    DATE(l.meal_time) as date_val,
                    SUM(l.cal) as total_cal,
                    COUNT(l.id_log) as food_count,
                    GROUP_CONCAT(m.food_name, ', ') as food_list
                FROM LogHarian l
                JOIN Makanan m ON l.kode_makanan = m.code
                {condition}
                GROUP BY date_val
                ORDER BY date_val DESC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                date_str, current_cal, count, foods = row
                dt = datetime.strptime(date_str, '%Y-%m-%d')

                # Dictionary for translation
                DAYS_ID = {
                    "Sunday": "Minggu", "Monday": "Senin", "Tuesday": "Selasa",
                    "Wednesday": "Rabu", "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu"
                }

                day_en = dt.strftime('%A')
                day_id = DAYS_ID.get(day_en, day_en)

                title_label = QLabel(f"{day_id} - {count} Makanan")
                
                main_card = QFrame()
                main_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                main_card.setFixedHeight(120)
                main_card.setStyleSheet(
                    'QFrame { background: rgba(255,255,255,0.7); border: 1px solid #1A7A34; border-radius: 16px; }'
                    'QLabel { border: none; background: transparent; }'
                )
                main_card_layout = QHBoxLayout(main_card)
                main_card_layout.setSpacing(15)

                # Date Section
                date_holder = QLabel()
                date_holder.setFixedSize(72, 75)
                date_holder.setAlignment(Qt.AlignCenter)
                date_text = (
                    f'<div style="margin-top: -16px; line-height: 0.8;">'
                    f'  <span style="font-size: 32px; font-weight: bold;">{dt.strftime("%d")}</span><br>'
                    f'  <span style="font-size: 14px; letter-spacing: 1px;">{dt.strftime("%b").upper()}</span>'
                    f'</div>'
                )
                date_holder.setText(date_text)
                date_holder.setStyleSheet(
                    'color: #1A7A34; border: none; border-radius: 16px; padding-bottom: 12px; background: rgba(43, 188, 82, 0.25);'
                )
                main_card_layout.addWidget(date_holder)

                # Info Section
                text_stack = QVBoxLayout()
                text_stack.setSpacing(0)
                text_stack.setContentsMargins(0, 0, 0, 5) 

                title_label = QLabel(f"{day_id} - {count} Makanan")
                title_label.setFont(font_body(16))
                title_label.setStyleSheet("color: black; font-weight: bold; border: none; background: transparent;")
                
                metrics = QFontMetrics(font_body(12))
                elided_foods = metrics.elidedText(foods or "", Qt.ElideRight, 350)
                subtitle_label = QLabel(elided_foods)
                subtitle_label.setFont(font_body(12))
                subtitle_label.setStyleSheet("color: #868686; border: none; background: transparent;")

                progress_bar = QProgressBar()
                progress_bar.setFixedHeight(6)
                progress_bar.setTextVisible(False)

                bar_container = QWidget()
                bar_layout = QHBoxLayout(bar_container)
                bar_layout.setContentsMargins(-5, 0, 0, 0) 
                bar_layout.addWidget(progress_bar)
                
                text_stack.addWidget(title_label)
                text_stack.addSpacing(-4)
                text_stack.addWidget(subtitle_label)
                text_stack.addSpacing(2)
                text_stack.addWidget(bar_container)
                main_card_layout.addLayout(text_stack, 1)

                # Calories Section
                right_container = QWidget()
                right_layout = QVBoxLayout(right_container)
                right_layout.setSpacing(0)
                right_layout.setContentsMargins(0, 0, 0, 0)
                
                safe_current = current_cal or 0
                val_current = QLabel(str(int(safe_current)))
                val_current.setFont(font_body(16))
                val_current.setAlignment(Qt.AlignRight | Qt.AlignBottom)
                
                val_goal = QLabel(f"/{int(goal_cal)}")
                val_goal.setFont(font_body(10))
                val_goal.setStyleSheet("color: #868686;")
                val_goal.setAlignment(Qt.AlignRight | Qt.AlignTop)

                status_layout = QHBoxLayout()
                status_layout.setSpacing(4)
                status_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                status_icon = QLabel()
                status_icon.setFixedSize(12, 4) 
                status_text = QLabel("Status")
                status_text.setFont(font_body(10))
                status_layout.addWidget(status_icon)
                status_layout.addWidget(status_text)

                right_layout.addWidget(val_current)
                right_layout.addSpacing(-2)
                right_layout.addWidget(val_goal)
                right_layout.addSpacing(8) 
                right_layout.addLayout(status_layout)
                right_layout.addStretch()
                main_card_layout.addWidget(right_container, 0)

                # Coloring Logic
                percentage = (safe_current / goal_cal) * 100 if goal_cal > 0 else 0
                progress_bar.setValue(min(int(percentage), 100))
                
                if percentage > 100:
                    bar_color, status = "#E03030", "Lebih"
                elif percentage >= 60:
                    bar_color, status = "#1A7A34", "Normal"
                else:
                    bar_color, status = "#A0E2B2", "Kurang"

                val_current.setStyleSheet(f"color: {bar_color}; font-weight: bold; border: none; background: transparent;")
                status_text.setText(status)
                status_text.setStyleSheet(f"color: {bar_color}; font-weight: bold; border: none; background: transparent;")
                status_icon.setStyleSheet(f"background-color: {bar_color}; border-radius: 2px;")
                progress_bar.setStyleSheet(f'''
                    QProgressBar {{ background-color: #F0F0F0; border-radius: 8px; border: none; }}
                    QProgressBar::chunk {{ background-color: {bar_color}; border-radius: 8px; }}
                ''')

                self.cards_layout.addWidget(main_card)

            conn.close()
        except Exception as e:
            print(f"Error Database: {e}")

    def _clean_text(self, text):
        if not text:
            return ""
        import re
        cleaned = re.sub(r'[\r\n\t]+', ' ', str(text))
        cleaned = re.sub(r' {2,}', ' ', cleaned)
        return cleaned.strip()

    def export_to_csv(self):
        default_name = f"Riwayat_Nutrisi.csv"
        file_path, _ = QFileDialog.getSaveFileName(self, "Export CSV", default_name, "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DATE(l.meal_time), l.category, m.food_name, l.portion, l.cal, l.protein, l.carb, l.fat
                FROM LogHarian l 
                JOIN Makanan m ON l.kode_makanan = m.code
                ORDER BY l.meal_time DESC
            """)
            rows = cursor.fetchall()
            with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file, delimiter=';', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(["Tanggal", "Waktu", "Makanan", "Porsi", "Kalori", "Protein", "Karbohidrat", "Lemak"])
                for row in rows:
                    writer.writerow([row[0], str(row[1] or "Lainnya").capitalize(), self._clean_text(row[2]), 
                                     round(row[3], 1), round(row[4], 1), round(row[5], 1), round(row[6], 1), round(row[7], 1)])
            conn.close()
            show_toast(self, f"Data berhasil diekspor.", TOAST_SUCCESS)
        except Exception as e:
            show_toast(self, f"Gagal: {str(e)}", TOAST_ERROR)

if __name__ == '__main__':
    import os
    import ctypes
    # Agar taskbar icon di Windows berubah, set AppUserModelID
    try:
        myappid = 'nutrikost.app.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    
    # Set window icon untuk taskbar dan pojok kiri atas
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(BASE, "assets", "icons", "Logo.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        
    app.setStyle("Fusion")
    window = RiwayatPage()
    window.show()
    sys.exit(app.exec_())