from __future__ import annotations
from typing import List

class TimeFilter:

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

    #parameter db nya dari DBHelper 
    def __init__(self, db):
        self._db            = db
        self._all_logs      = []       # cache semua log dari DB
        self._active_waktu  = None     # filter waktu aktif (None = semua)
        self._active_tanggal = None    # filter tanggal aktif (None = semua)

    # Load log DB
    # Ambil semua log dari DB dan simpan ke cache internal,panggil sekali saat page dibuka/saat ada changes
    def load(self) -> None:
        self._all_logs = self._db.get_all_logs()

    # Set Filter waktu
    def filter_waktu(self, waktu: str | None) -> List[dict]:
        self._active_waktu = waktu
        return self._terapkan_filter()

    #set filter tanggal format yyyy-mm-dd
    def filter_tanggal(self, tanggal: str | None) -> List[dict]:
        self._active_tanggal = tanggal
        return self._terapkan_filter()

    #baca hasil filtering
    def get_filtered(self) -> List[dict]:
        return self._terapkan_filter()

    #apply filter (tgl dan waktu) to all logs ini mesinnya
    def _terapkan_filter(self) -> List[dict]:
        hasil = list(self._all_logs)

        # Filter waktu
        if self._active_waktu is not None:
            hasil = [
                log for log in hasil
                if log.get("category", "").lower() == self._active_waktu.lower()
            ]

        # Filter tanggal
        if self._active_tanggal is not None:
            hasil = [
                log for log in hasil
                if log.get("meal_time", "").startswith(self._active_tanggal)
            ]

        return hasil

    # UI status utk jumlah log dan filter aktif
    def label_status(self) -> str:
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

    #reset default filter ke tampilkan semua
    def reset(self) -> List[dict]:
        self._active_waktu   = None
        self._active_tanggal = None
        return list(self._all_logs)