import sys
import os
import io
import sqlite3
from contextlib import redirect_stdout
from datetime import date, datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QEvent, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QDoubleValidator

# Ensure the system can find LogSystem and templates
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from LogSystem import LogSystem
from fatih_GUI.template_halaman import *

class RiwayatPage(PageTemplate):
    PAGE_NAME = 'Riwayat Nutrisi'
    PAGE_DESC = 'Tijau kembali pola makan harianmu'
    NAV_INDEX = 3

    def build_content(self, container: QWidget):
        # placeholder konten
        main_card = QFrame()
        main_card.setStyleSheet(
            'background: rgba(255,255,255,0.7);'
            'border: 1px solid #1A7A34;'
            'border-radius: 16px;'
            'padding: 4px;'
        )

        main_card_layout = QHBoxLayout(main_card)
        main_card_layout.setSpacing(15)

        date_holder = QLabel()
        date_holder.setFixedSize(72, 75)
        date_holder.setFont(font_title())
        date_holder.setAlignment(Qt.AlignCenter)

        date_text = (
            '<div style="margin-top: -16px; line-height: 0.8;">'
            '  <span style="font-size: 32px;">12</span><br>'
            '  <span style="font-size: 14px; letter-spacing: 1px;">MAY</span>'
            '</div>'
        )
        date_holder.setText(date_text)

        date_holder.setStyleSheet(
            'color: #1A7A34;'
            'border: none;'
            'border-radius: 16px;'
            'padding-bottom: 12px;'
            'background: rgba(43, 188, 82, 0.25);'
            )

        main_card_layout.addWidget(date_holder)
        
        # Text Stack
        text_stack = QVBoxLayout()
        text_stack.setSpacing(0)
        text_stack.setContentsMargins(0, 0, 0, 5) 

        title_label = QLabel("Placeholder Title")
        title_label.setFont(font_body(16))
        title_label.setStyleSheet("color: black; font-weight: bold; border: none; background: transparent;")
        
        subtitle_label = QLabel("Supporting description text goes here")
        subtitle_label.setFont(font_body(12))
        subtitle_label.setStyleSheet("color: #868686; border: none; background: transparent;")

        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.update_progress_style(90)

        bar_container = QWidget()
        bar_container.setStyleSheet("background: transparent; border: none;")
        bar_layout = QHBoxLayout(bar_container)
        bar_layout.setContentsMargins(-5, 0, 0, 0) 
        bar_layout.addWidget(self.progress)
        
        text_stack.addWidget(title_label)
        text_stack.addSpacing(-10)
        text_stack.addWidget(subtitle_label)
        text_stack.addSpacing(2)
        text_stack.addWidget(bar_container)
        
        main_card_layout.addLayout(text_stack, 1)

        main_card_layout.addStretch(0)

        container.layout().addWidget(main_card)

    def update_progress_style(self, value):
        self.progress.setValue(value)
        
        # Logic for colors:
        # < 60% -> #1A7A3440 (Low Opacity Green)
        # > 60% -> #1A7A34 (Solid Green)
        # High -> #E03030 (Red) - Note: Adjust threshold as needed
        
        color = "#C9EED3" 
        if value > 100:
            color = "#E03030"
        elif value >= 60:
            color = "#1A7A34"

        self.progress.setStyleSheet(f'''
            QProgressBar {{
                background-color: rgba(43, 188, 82, 0.40);
                border-radius: 3px;
                border: 0px solid transparent;
                padding: 0px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
                margin: 0px;
            }}
        ''')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RiwayatPage()
    window.show()
    sys.exit(app.exec_())