"""
Toast Notification System — Nutri-Kost
=======================================
Menampilkan notifikasi toast di pojok kanan bawah window,
menggantikan QMessageBox bawaan Qt.

Cara pakai:
    from fatih_GUI.toast_notification import show_toast, TOAST_ERROR, TOAST_SUCCESS, TOAST_NORMAL

    show_toast(self, "Data berhasil disimpan!", TOAST_SUCCESS)
    show_toast(self, "Terjadi kesalahan!", TOAST_ERROR)
    show_toast(self, "Waktunya makan siang!", TOAST_NORMAL)
"""

import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy, QApplication, QGraphicsOpacityEffect
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QObject, QEvent, QRect,
)
from PyQt5.QtGui import (
    QColor, QPainter, QPainterPath, QFont,
    QBrush, QPen, QPixmap,
)

# ── Tipe Toast ──────────────────────────────────────────────
TOAST_ERROR   = 'error'
TOAST_SUCCESS = 'success'
TOAST_NORMAL  = 'normal'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_CONFIG = {
    TOAST_ERROR: {
        'bg':   QColor('#E53935'),
        'icon': os.path.join(BASE_DIR, 'assets', 'icons', 'wordpress_error (1).png'),
    },
    TOAST_SUCCESS: {
        'bg':   QColor('#1A7A34'),
        'icon': os.path.join(BASE_DIR, 'assets', 'icons', 'Component (1).png'),
    },
    TOAST_NORMAL: {
        'bg':   QColor('#0D2B1A'),
        'icon': os.path.join(BASE_DIR, 'assets', 'icons', 'boxicons_message-filled (1).png'),
    },
}

# ── Dimensi & Margin ─────────────────────────────────────────
TOAST_W       = 360
TOAST_H       = 64
TOAST_RADIUS  = 18
MARGIN_RIGHT  = 24
MARGIN_BOTTOM = 24
TOAST_GAP     = 10


# ── Icon Widget ──────────────────────────────────────────────
class _IconWidget(QLabel):
    """Menampilkan ikon dari file png."""

    def __init__(self, icon_path: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAlignment(Qt.AlignCenter)
        
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            self.setPixmap(pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation))


# ── Toast Widget ─────────────────────────────────────────────
class ToastWidget(QWidget):
    """Satu buah toast notification."""

    def __init__(self, parent: QWidget, message: str, toast_type: str):
        super().__init__(parent)
        cfg            = _CONFIG.get(toast_type, _CONFIG[TOAST_NORMAL])
        self._bg_color = cfg['bg']
        self._icon_type = cfg['icon']

        self.setFixedSize(TOAST_W, TOAST_H)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.raise_()  # selalu di atas widget lain

        # ── Layout ──
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 20, 0)
        lay.setSpacing(14)

        icon = _IconWidget(self._icon_type, self)
        lay.addWidget(icon, 0, Qt.AlignVCenter)

        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: white; background: transparent;")
        lbl.setFont(QFont('Poppins', 9))
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        lay.addWidget(lbl, 1, Qt.AlignVCenter)

        # ── Opacity effect untuk animasi fade ──
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._effect.setOpacity(0.0)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(self._bg_color))
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), TOAST_RADIUS, TOAST_RADIUS)
        p.drawPath(path)
        p.end()

    def show_animated(self, duration_ms: int, on_done):
        self.show()

        # Fade in
        self._anim_in = QPropertyAnimation(self._effect, b'opacity', self)
        self._anim_in.setDuration(220)
        self._anim_in.setStartValue(0.0)
        self._anim_in.setEndValue(1.0)
        self._anim_in.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_in.start()

        # Tunda fade out
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(lambda: self._fade_out(on_done))
        self._timer.start(duration_ms)

    def _fade_out(self, on_done):
        self._anim_out = QPropertyAnimation(self._effect, b'opacity', self)
        self._anim_out.setDuration(280)
        self._anim_out.setStartValue(1.0)
        self._anim_out.setEndValue(0.0)
        self._anim_out.setEasingCurve(QEasingCurve.InCubic)
        self._anim_out.finished.connect(on_done)
        self._anim_out.start()


# ── Toast Manager ─────────────────────────────────────────────
class _ToastManager(QObject):
    """
    Mengelola antrean dan posisi semua toast.
    Toast ditumpuk dari bawah ke atas di pojok kanan bawah window.
    """

    def __init__(self):
        super().__init__()
        self._toasts: list[tuple[ToastWidget, QWidget]] = []
        self._watched: set[int] = set()

    def show(self, parent_window: QWidget, message: str,
             toast_type: str = TOAST_NORMAL, duration: int = 3500):
        # parent_window = top-level window (QMainWindow)
        root = parent_window.window()

        # Pasang event filter sekali per window agar bisa reposition saat resize
        if id(root) not in self._watched:
            root.installEventFilter(self)
            self._watched.add(id(root))

        toast = ToastWidget(root, message, toast_type)
        self._toasts.append((toast, root))
        self._reposition(root)
        toast.show_animated(duration, on_done=lambda: self._remove(toast, root))

    def _remove(self, toast: ToastWidget, root: QWidget):
        self._toasts = [(t, r) for (t, r) in self._toasts if t is not toast]
        toast.hide()
        toast.deleteLater()
        self._reposition(root)

    def _reposition(self, root: QWidget):
        pw = root.width()
        ph = root.height()
        y_cursor = ph - MARGIN_BOTTOM

        for (toast, r) in reversed(self._toasts):
            if r is not root:
                continue
            y_cursor -= TOAST_H
            toast.move(pw - TOAST_W - MARGIN_RIGHT, y_cursor)
            toast.raise_()
            y_cursor -= TOAST_GAP

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Resize:
            self._reposition(obj)
        return False


# ── Singleton & Public API ────────────────────────────────────
_manager = _ToastManager()


def show_toast(
    parent_window: QWidget,
    message: str,
    toast_type: str = TOAST_NORMAL,
    duration: int = 3500,
):
    """
    Tampilkan toast notification di pojok kanan bawah window.

    Parameters
    ----------
    parent_window : QWidget
        Widget induk — bisa QMainWindow maupun QWidget biasa.
        Toast akan muncul di pojok kanan bawah top-level window-nya.
    message : str
        Teks pesan yang ditampilkan.
    toast_type : str
        TOAST_ERROR   → merah, ikon peringatan
        TOAST_SUCCESS → hijau, ikon centang
        TOAST_NORMAL  → hijau tua, ikon chat
    duration : int
        Berapa ms toast tampil sebelum fade-out (default 3500 ms).
    """
    _manager.show(parent_window, message, toast_type, duration)
