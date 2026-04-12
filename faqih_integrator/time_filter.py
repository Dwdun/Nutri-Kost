from __future__ import annotations
from typing import List

class TimeFilter:
    """
    Mengelola semua operasi filter waktu untuk log harian.

    Sebelumnya fungsi-fungsi ini standalone — dibungkus jadi class
    agar bisa di-instantiate sekali dan dipakai di mana saja tanpa
    harus passing 'db' dan 'logs' berulang-ulang.

    Cara pakai:
        from time_filter import TimeFilter
        tf = TimeFilter(db)
        tf.load()                            # ambil semua log dari DB
        tf.filter_waktu("Sarapan")           # filter berdasarkan waktu
        tf.filter_tanggal("2026-04-12")      # filter berdasarkan tanggal
        tf.label_status()                    # teks untuk ditampilkan di UI
    """

    # Format: (label tampil di UI, nilai yang disimpan di DB)
    # None = semua waktu (tidak difilter)
    WAKTU_OPTIONS = [
        ("Semua Waktu", None),
        ("Sarapan",     "Sarapan"),
        ("Makan Siang", "Makan Siang"),
        ("Makan Malam", "Makan Malam"),
        ("Snack",       "Snack"),
        ("Minuman",     "Minuman"),
    ]

    def __init__(self, db):
        """
        Parameter:
            db : instance DBHelper dari bima_scrapper/models.py
        """
        self._db            = db
        self._all_logs      = []       # cache semua log dari DB
        self._active_waktu  = None     # filter waktu aktif (None = semua)
        self._active_tanggal = None    # filter tanggal aktif (None = semua)

    # ── Load ──────────────────────────────────────────────────────────────────

    def load(self) -> None:
        """
        Ambil semua log dari DB dan simpan ke cache internal.
        Panggil ini sekali saat halaman dibuka, atau setelah ada perubahan log.
        """
        self._all_logs = self._db.get_all_logs()

    # ── Filter ────────────────────────────────────────────────────────────────

    def filter_waktu(self, waktu: str | None) -> List[dict]:
        """
        Set filter waktu aktif lalu kembalikan log yang cocok.

        Parameter:
            waktu : "Sarapan", "Makan Siang", "Makan Malam", "Snack",
                    "Minuman", atau None untuk semua waktu.
        """
        self._active_waktu = waktu
        return self._terapkan_filter()

    def filter_tanggal(self, tanggal: str | None) -> List[dict]:
        """
        Set filter tanggal aktif lalu kembalikan log yang cocok.

        Parameter:
            tanggal : string format "YYYY-MM-DD", atau None untuk semua tanggal.
        """
        self._active_tanggal = tanggal
        return self._terapkan_filter()

    def get_filtered(self) -> List[dict]:
        """Kembalikan hasil filter saat ini tanpa mengubah state."""
        return self._terapkan_filter()

    def _terapkan_filter(self) -> List[dict]:
        """
        Terapkan semua filter aktif (waktu + tanggal) ke _all_logs.
        Filter bisa dikombinasikan — misalnya Sarapan pada tanggal tertentu.
        """
        hasil = list(self._all_logs)

        # Filter waktu
        if self._active_waktu is not None:
            hasil = [
                log for log in hasil
                if log.get("category", "").lower() == self._active_waktu.lower()
            ]

        # Filter tanggal — cukup cek apakah meal_time diawali tanggal yang diminta
        if self._active_tanggal is not None:
            hasil = [
                log for log in hasil
                if log.get("meal_time", "").startswith(self._active_tanggal)
            ]

        return hasil

    # ── Info UI ───────────────────────────────────────────────────────────────

    def label_status(self) -> str:
        """
        Teks siap tampil di UI yang menunjukkan jumlah log dan filter aktif.

        Contoh output:
            "Belum ada log hari ini"
            "5 log harian tersimpan"
            "2 dari 5 log · waktu: Sarapan"
        """
        filtered = self._terapkan_filter()
        total    = len(self._all_logs)
        shown    = len(filtered)

        if total == 0:
            return "Belum ada log hari ini"
        elif self._active_waktu is None and self._active_tanggal is None:
            return f"{total} log harian tersimpan"
        else:
            parts = []
            if self._active_waktu:
                parts.append(f"waktu: {self._active_waktu}")
            if self._active_tanggal:
                parts.append(f"tanggal: {self._active_tanggal}")
            return f"{shown} dari {total} log · {' · '.join(parts)}"

    def reset(self) -> List[dict]:
        """Reset semua filter ke kondisi awal (tampilkan semua log)."""
        self._active_waktu   = None
        self._active_tanggal = None
        return list(self._all_logs)