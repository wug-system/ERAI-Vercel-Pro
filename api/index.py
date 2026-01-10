from flask import Flask, render_template, request, jsonify
from groq import Groq
from tavily import TavilyClient
import os
from datetime import datetime

app = Flask(__name__, template_folder='../templates')

# Proteksi API Key
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
        # Identitas & Waktu
        user_name = "Admin / 082359161055" 
        current_date = datetime.now().strftime("%d %B %Y")
        
        data = request.json
        user_input = data.get("message", "")
        user_mode = data.get("mode", "belajar")
        history = data.get("history", [])

        # --- LOGIKA MODE PENCARIAN ---
        search_info = ""
        if user_mode == "pencarian":
            if tavily_client:
                try:
                    search_res = tavily_client.search(query=f"{user_input} tahun 2026", search_depth="advanced")
                    search_info = " ".join([r.get('content') for r in search_res.get('results', [])])
                except:
                    search_info = "Gagal mengambil data internet."
            mode_instruction = "MODE PENCARIAN AKTIF: Gunakan DATA INTERNET. Wajib fokus pada kalender/info tahun 2026."
        
        # --- LOGIKA MODE LATIHAN (KUIS 1-8) ---
        elif user_mode == "latihan":
            mode_instruction = r"""
WAJIB: AKTIFKAN AUTO-QUIZ MODE. Berikan 4 pilihan A, B, C, D. Jangan beri jawaban langsung.
1. Jika Kakak memberikan soal, JANGAN BERIKAN JAWABAN LANGSUNG.
2. Ubah menjadi kuis interaktif 4 pilihan (A, B, C, D).
3. Gunakan \ce{...} untuk kimia dan $...$ untuk matematika.
4. HANYA berikan jawaban jika Kakak sudah memilih opsi A/B/C/D.
5. Jika Kakak memberikan soal atau pertanyaan materi, JANGAN BERIKAN JAWABAN LANGSUNG.
6. Salah satu dari pilihan TERSEBUT HARUS JAWABAN YANG BENAR.
7. Berikan petunjuk (clue) singkat saja.
8. Tunggu Kakak menjawab. Jika benar, baru berikan selamat dan penjelasan step-by-step yang rapi.
"""
        
        # --- LOGIKA MODE BELAJAR (STEP-BY-STEP 1-7) ---
        else:
            mode_instruction = r"""
WAJIB: MODE BELAJAR AKTIF. Berikan penjelasan step-by-step yang rapi dengan LaTeX.
1. Berikan penjelasan terstruktur menggunakan "---" antar bagian.
2. Selesaikan soal step-by-step menggunakan LaTeX ($...$).
3. Gunakan \ce{...} untuk simbol kimia.
4. Berikan penjelasan yang sangat rapi, terstruktur, dan mendalam.
5. Gunakan "Pemisah Garis" (---) antar bagian agar tidak menumpuk.
6. Gunakan Bullet Points untuk poin-poin penting.
7. Jika ada rumus per (fraction), taruh di baris baru sendiri, jangan digabung di tengah kalimat.
"""

        system_prompt = f"""
Nama kamu ERAI, Tutor Sebaya WUG untuk {user_name}.
{mode_instruction}
PENTING: Hari ini adalah {current_date}. Semua jawaban harus berbasis tahun 2026.
DATA INTERNET: {search_info if search_info else 'Gunakan internal knowledge 2026'}.

ATURAN FORMATTING:
- Gunakan --- untuk garis pemisah.
- Rumus matematika diapit $...$.
- Rumus kimia diapit \\ce{{...}}.
- Gunakan bahasa teman sebaya yang suportif.
"""

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
        
        # Eksekusi Model
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.4
        )
        
        return jsonify({"response": completion.choices[0].message.content})

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate_limit" in error_msg.lower():
            return jsonify({
                "response": "**[WUG SECURE SYSTEM - NOTIFICATION]**\n\nKuota harian model penuh. Coba lagi nanti ya! 🚀"
            }), 200
        return jsonify({"response": f"**[SYSTEM ERROR]** Terjadi gangguan: {error_msg}"}), 200

if __name__ == '__main__':
    app.run(debug=True)
