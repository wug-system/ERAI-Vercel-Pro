from flask import Flask, render_template, request, jsonify
from groq import Groq
import os

app = Flask(__name__, template_folder='../templates')

# Mengambil API Key dari Environment Variables Vercel
# Pastikan nanti di Dashboard Vercel kamu sudah input GROQ_API_KEY
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

    current_year = 2026
    system_prompt = (
        f"Nama kamu ERAI. Kamu adalah Tutor Sebaya berstandar WUG untuk {user_name}. "
        f"Konteks Waktu: Sekarang adalah tahun {current_year}. Kamu memiliki akses ke informasi terkini. "
        "FILOSOFI: Kamu teman belajar yang berkembang bersama, bukan sekadar AI penjawab. "
        "PERILAKU: Jangan katakan kamu tidak tahu info setelah 2023. Jika tidak tahu, cari/gunakan logika tahun 2026. "
        "Gaya bicara santai (aku-kamu), santun, dan suportif. "
        "Gunakan format LaTeX ($...$) untuk rumus dan jangan langsung beri jawaban akhir."
    )

    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7
        )
        return jsonify({"response": completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
