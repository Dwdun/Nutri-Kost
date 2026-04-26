import google.generativeai as genai

# Masukkan API Key Anda
genai.configure(api_key="AIzaSyBu5Ce7b1inSfAUJQFEblWqUMRu9uUIhzs")

print("Daftar model yang bisa digunakan:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)