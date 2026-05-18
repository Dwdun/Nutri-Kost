import os
import json
import random
import string
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Path file konfigurasi email di folder yang sama
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_config.json")

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Reset Password Nutri-Kost</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f7f6;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 30px auto;
            background-color: #ffffff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            border: 1px solid #e0e0e0;
        }}
        .header {{
            background-color: #1A7A34;
            color: #ffffff;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
            letter-spacing: 1px;
        }}
        .content {{
            padding: 40px 30px;
            color: #333333;
            line-height: 1.6;
        }}
        .content p {{
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 16px;
        }}
        .password-box {{
            background-color: #f0fdf4;
            border: 2px dashed #1A7A34;
            border-radius: 12px;
            padding: 15px 25px;
            text-align: center;
            margin: 30px 0;
        }}
        .password-text {{
            font-family: 'Courier New', Courier, monospace;
            font-size: 32px;
            font-weight: bold;
            letter-spacing: 3px;
            color: #1A7A34;
            margin: 0;
        }}
        .instructions {{
            font-size: 14px;
            color: #555555;
            margin-bottom: 25px;
        }}
        .footer {{
            background-color: #fafafa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #777777;
            border-top: 1px solid #eeeeee;
        }}
        .warning {{
            font-size: 13px;
            color: #b71c1c;
            background-color: #ffebee;
            padding: 12px 18px;
            border-radius: 8px;
            margin-top: 25px;
            border-left: 4px solid #b71c1c;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Nutri-Kost</h1>
        </div>
        <div class="content">
            <p>Halo,</p>
            <p>Kami menerima permintaan untuk melakukan riset password pada akun Nutri-Kost Anda. Kami telah membuatkan password sementara yang aman agar Anda dapat kembali mengakses akun Anda:</p>
            
            <div class="password-box">
                <p class="password-text">{temp_password}</p>
            </div>
            
            <p class="instructions">
                Silakan masuk kembali ke aplikasi Nutri-Kost menggunakan password sementara di atas. 
                Untuk alasan keamanan, kami sangat menyarankan Anda untuk segera memperbarui password Anda melalui menu <strong>Edit Profile</strong> setelah berhasil login.
            </p>
            
            <div class="warning">
                <strong>PENTING:</strong> Jika Anda tidak merasa melakukan permintaan ini, silakan abaikan email ini atau hubungi tim bantuan Nutri-Kost jika Anda mencurigai adanya aktivitas mencurigakan.
            </div>
        </div>
        <div class="footer">
            &copy; 2026 Tim Nutri-Kost. Hak Cipta Dilindungi.<br>
            Aplikasi Manajemen Nutrisi Terintegrasi
        </div>
    </div>
</body>
</html>
"""

def generate_temp_password(length=8):
    """
    Menghasilkan password sementara acak sepanjang 8 karakter.
    Menghindari karakter-karakter yang mirip seperti '0', 'O', '1', 'l' agar mudah diketik.
    """
    pool = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(pool) for _ in range(length))

def load_config():
    """
    Membaca email_config.json. 
    Jika belum ada, buat file baru dengan konfigurasi placeholder/dummy.
    """
    if not os.path.exists(CONFIG_PATH):
        default_config = {
            "sender_email": "username_gmail_anda@gmail.com",
            "app_password": "masukkan_16_karakter_app_password_anda"
        }
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4)
        except Exception as e:
            print(f"Gagal membuat file konfigurasi email: {e}")
        return default_config
    
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Gagal membaca file konfigurasi email: {e}")
        return {}

def is_config_dummy(config):
    """
    Memeriksa apakah konfigurasi email masih menggunakan nilai default/dummy.
    """
    email = config.get("sender_email", "")
    pwd = config.get("app_password", "")
    return (
        not email 
        or "username_gmail_anda" in email 
        or not pwd 
        or "masukkan_16_karakter" in pwd 
        or "app_password" in pwd
    )

def send_reset_email(recipient_email, temp_password):
    """
    Mengirimkan email berisi password sementara secara sinkron.
    Jika masih dummy, raise ValueError("SMTP_NOT_CONFIGURED").
    """
    config = load_config()
    if is_config_dummy(config):
        raise ValueError("SMTP_NOT_CONFIGURED")

    sender_email = config.get("sender_email", "").strip()
    app_password = config.get("app_password", "").strip()

    # Siapkan email
    msg = MIMEMultipart()
    msg['From'] = f"Nutri-Kost <{sender_email}>"
    msg['To'] = recipient_email
    msg['Subject'] = "Nutri-Kost: Reset Password Anda"

    # Masukkan template HTML
    body_html = HTML_TEMPLATE.format(temp_password=temp_password)
    msg.attach(MIMEText(body_html, 'html'))

    # Koneksi SMTP (menggunakan Gmail TLS di port 587)
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, app_password)
    server.sendmail(sender_email, recipient_email, msg.as_string())
    server.quit()
