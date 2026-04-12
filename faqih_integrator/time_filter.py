from __future__ import annotations
from typing import List


# ── Konstanta: Pilihan Waktu Makan ────────────────────────────────────────────
# Format: (label yang tampil di UI, nilai yang disimpan di DB)
# None = semua waktu (tidak difilter)
LOG_WAKTU_OPTIONS = [
    ("Semua Waktu",  None),
    ("Sarapan",      "Sarapan"),
    ("Makan Siang",  "Makan Siang"),
    ("Makan Malam",  "Makan Malam"),
    ("Snack",        "Snack"),
    ("Minuman",      "Minuman"),
]


# ── Fungsi: Load Log dari DB ──────────────────────────────────────────────────

def load_logs(db) -> List[dict]:
    """
    Ambil semua log harian dari database.

    Parameter:
        db : instance DBHelper dari bima_scrapper/models.py

    Return:
        List dict log harian, setiap dict berisi kolom LogHarian
        + food_name dan full_name dari JOIN.
    """
    return db.get_all_logs()


# ── Fungsi: Filter Berdasarkan Waktu ─────────────────────────────────────────

def filter_log_berWaktu(logs: List[dict], waktu: str | None) -> List[dict]:
    """
    Filter log harian berdasarkan kategori waktu makan.

    Sesuai diagram class: filterLogBerWaktu(waktu: String) : List<LogHarian>

    Parameter:
        logs  : list semua log harian (dari load_logs atau DBHelper.get_all_logs())
        waktu : string kategori ("Sarapan", "Makan Siang", "Makan Malam",
                "Snack", "Minuman"), atau None untuk mengembalikan semua log.

    Return:
        List dict log harian yang cocok dengan waktu yang diminta.
    """
    if waktu is None:
        return list(logs)
    return [
        log for log in logs
        if log.get("category", "").lower() == waktu.lower()
    ]


# ── Fungsi: Teks Label untuk UI ───────────────────────────────────────────────

def hitung_log_display(logs: List[dict], waktu: str | None) -> str:
    """
    Hitung dan kembalikan teks label jumlah log untuk ditampilkan di UI.

    Parameter:
        logs  : list semua log harian
        waktu : filter waktu yang sedang aktif (None = semua)

    Return:
        String siap tampil, contoh:
        - "Belum ada log hari ini"
        - "5 log harian tersimpan"
        - "2 dari 5 log · waktu: Sarapan"
    """
    filtered = filter_log_berWaktu(logs, waktu)
    total    = len(logs)
    shown    = len(filtered)

    if total == 0:
        return "Belum ada log hari ini"
    elif waktu is None:
        return f"{total} log harian tersimpan"
    else:
        return f"{shown} dari {total} log · waktu: {waktu}"
    
def filter_log_berTanggal(logs: List[dict], tanggal: str) -> List[dict]:
    """
    Filter log berdasarkan tanggal tertentu.
    tanggal format: "YYYY-MM-DD"
    """
    return [
        log for log in logs
        if log.get("meal_time", "").startswith(tanggal)
    ]