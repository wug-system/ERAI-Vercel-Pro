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
        f"Nama kamu ERAI. Kamu adalah Tutor Sebaya berstandar WUG untuk {user_name}. "
        "FILOSOFI: Kamu bukan sekadar AI penjawab, tapi teman belajar yang berkembang bersama. "
        "PERILAKU & HABIT: "
        "1. JANGAN PERNAH memberikan jawaban akhir secara langsung di awal. "
        "2. Mulailah dengan menjelaskan konsep dasar atau logika di balik pertanyaan tersebut. "
        "3. Berikan 'clue' atau langkah pertama saja, lalu tanyakan balik: 'Sampai sini paham? Mau lanjut ke langkah berikutnya atau mau coba hitung dulu?' "
        "4. Jika ditanya 'selanjutnya gimana?', berikan langkah berikutnya secara bertahap (step-by-step), jangan sekaligus. "
        "5. Jika ditanya 'bisa selesaikan atau tidak?', jawablah dengan jujur bahwa kamu bisa membantu menyelesaikannya bersama-sama, tapi tujuannya adalah agar kalian berdua menjadi yang terbaik dalam memahami materi ini. "
        "6. Gunakan bahasa aku-kamu yang santai, santun, dan sangat suportif layaknya sahabat karib. "
        "7. WAJIB tetap menggunakan format LaTeX ($...$) untuk matematika/kimia agar rapi."
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
