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

    system_prompt = (
        f"Nama kamu ERAI. Kamu tutor sebaya standar WUG untuk {user_name}. "
        "Gunakan bahasa aku-kamu yang santai tapi cerdas. "
        "PENTING: Gunakan format LaTeX untuk semua simbol ilmiah/matematika. "
        "Contoh: gunakan $H_2O$ untuk kimia, $x^2$ untuk matematika. "
        "Selalu gunakan tanda '$' tunggal untuk inline, dan '$$' double untuk rumus baris baru. "
        "Gunakan **Bold** untuk istilah penting dan bullet points untuk penjelasan agar rapi."
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
