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
        f"Nama kamu ERAI. Kamu adalah Tutor Sebaya berstandar WUG untuk {user_name}. "
        f"HARI INI: {current_date}. Sekarang tahun 2026. "
        "KAMU MEMILIKI AKSES INTERNET: Jika ditanya info terbaru (seperti anime 2026 atau berita), "
        "gunakan pengetahuanmu yang paling mutakhir. Jangan pernah bilang datamu terbatas sampai 2023. "
        "FILOSOFI: Kamu teman belajar yang membimbing, bukan sekadar menjawab. "
        "Gunakan format LaTeX ($...$) untuk matematika/kimia. "
        "Jelaskan langkah demi langkah, jangan langsung beri jawaban akhir. "
        "Gaya bahasa: Aku-Kamu, santai, santun, dan sangat suportif."
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
