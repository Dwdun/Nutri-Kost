import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()
# Masukkan API Key Anda
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("Daftar model yang bisa digunakan:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)