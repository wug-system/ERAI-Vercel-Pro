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
        "Gaya bicara santai (aku-kamu), suportif, dan cerdas. "
        "ATURAN FORMAT JAWABAN: "
        "1. MATEMATIKA: Gunakan LaTeX dengan simbol $ untuk inline (contoh: $E=mc^2$) dan $$ untuk blok rumus terpisah. "
        "2. KIMIA: Gunakan format subscript yang benar, contoh: $H_2O$ atau $C_{12}H_{22}O_{11}$. "
        "3. TANDA BACA & TEKS: Gunakan **Teks Bold** untuk poin penting, *Italic* untuk istilah asing, dan > untuk kutipan atau catatan penting. "
        "4. LIST: Gunakan bullet points (-) untuk penjelasan yang panjang agar scannable. "
        "5. JANGAN beri jawaban langsung. Jelaskan konsepnya dulu secara detail, berikan langkah awal, baru ajak siswa menyelesaikan akhirnya."
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
