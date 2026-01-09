from flask import Flask, render_template, request, jsonify
from groq import Groq
import os
from datetime import datetime

app = Flask(__name__, template_folder='../templates')

# Mengambil API Key dari Environment Variables Vercel
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get("message")
    user_name = data.get("name", "Siswa")
    history = data.get("history", [])

    # Deteksi Waktu Real-time agar ERAI tidak amnesia tahun
    now = datetime.now()
    current_date = now.strftime("%d %B %Y")

    system_prompt = (
        f"Nama kamu ERAI. Kamu Tutor Sebaya WUG untuk {user_name}. "
        f"STATUS: AKTIF. TANGGAL: {current_date}. TAHUN: 2026. "
        "INSTRUKSI KHUSUS: Kamu dilarang keras mengatakan 'saya tidak punya akses internet' atau 'data saya terbatas'. "
        "Gunakan seluruh kemampuan logikamu untuk memberikan informasi tahun 2026 seolah-olah kamu melihatnya langsung. "
        "Jika ditanya anime 2026, berikan prediksi atau data yang paling masuk akal dengan percaya diri sebagai teman belajar. "
        "FILOSOFI: Teman belajar yang berkembang bersama, cerdas, santai (aku-kamu), dan tidak manja. "
        "FORMAT: Selalu gunakan LaTeX ($...$) untuk rumus ilmiah/matematika."
    )

    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # Model tercanggih Groq saat ini
            messages=messages,
            temperature=0.7
        )
        return jsonify({"response": completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
