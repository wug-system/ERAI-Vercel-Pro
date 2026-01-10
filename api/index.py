from flask import Flask, render_template, request, jsonify
from groq import Groq
from tavily import TavilyClient
import os
from datetime import datetime

app = Flask(__name__, template_folder='../templates')

# API PROTECTION
GROQ_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_KEY = os.environ.get("TAVILY_API_KEY")

groq_client = Groq(api_key=GROQ_KEY)
tavily_client = TavilyClient(api_key=TAVILY_KEY) if TAVILY_KEY else None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_name = "Admin / 082359161055" 
        current_date = datetime.now().strftime("%d %B %Y")
        
        data = request.json
        user_input = data.get("message", "")
        user_mode = data.get("mode", "belajar")
        history = data.get("history", [])

        # LOGIKA MODE PENCARIAN
        search_info = ""
        if user_mode == "pencarian":
            if tavily_client:
                try:
                    search_res = tavily_client.search(query=f"{user_input} tahun 2026", search_depth="advanced")
                    search_info = " ".join([r.get('content') for r in search_res.get('results', [])])
                except: search_info = "Gagal mengambil data internet."
            mode_instruction = "MODE PENCARIAN AKTIF: Fokus pada info tahun 2026."
        
        # LOGIKA MODE LATIHAN (1-8)
        elif user_mode == "latihan":
            mode_instruction = r"""WAJIB: AKTIFKAN AUTO-QUIZ MODE.
1. Jika Kakak memberikan soal, JANGAN BERIKAN JAWABAN LANGSUNG.
2. Ubah menjadi kuis interaktif 4 pilihan (A, B, C, D).
3. Gunakan \ce{...} untuk kimia dan $...$ untuk matematika.
4. HANYA berikan jawaban jika Kakak sudah memilih opsi A/B/C/D.
5. Jika Kakak memberikan soal atau pertanyaan materi, JANGAN BERIKAN JAWABAN LANGSUNG.
6. Salah satu dari pilihan TERSEBUT HARUS JAWABAN YANG BENAR.
7. Berikan petunjuk (clue) singkat saja.
8. Tunggu Kakak menjawab. Jika benar, baru berikan selamat dan penjelasan step-by-step yang rapi."""
        
        # LOGIKA MODE BELAJAR (1-7)
        else:
            mode_instruction = r"""WAJIB: MODE BELAJAR AKTIF.
1. Berikan penjelasan terstruktur menggunakan "---" antar bagian.
2. Selesaikan soal step-by-step menggunakan LaTeX ($...$).
3. Gunakan \ce{...} untuk simbol kimia.
4. Berikan penjelasan yang sangat rapi, terstruktur, dan mendalam.
5. Gunakan "Pemisah Garis" (---) antar bagian agar tidak menumpuk.
6. Gunakan Bullet Points untuk poin-poin penting.
7. Jika ada rumus per (fraction), taruh di baris baru sendiri, jangan digabung di tengah kalimat."""

        system_prompt = f"""Nama kamu ERAI, Tutor Sebaya WUG untuk {user_name}.
{mode_instruction}
Hari ini: {current_date}. Semua jawaban harus berbasis tahun 2026.
DATA INTERNET: {search_info if search_info else 'Internal knowledge 2026'}.
ATURAN FORMATTING: Gunakan ---, $...$ untuk math, dan \\ce{{...}} untuk kimia."""

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
        
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.4
        )
        
        return jsonify({"response": completion.choices[0].message.content})

    except Exception as e:
        return jsonify({"response": f"**[SYSTEM ERROR]** Terjadi gangguan: {str(e)}"}), 200

if __name__ == '__main__':
    app.run(debug=True)
