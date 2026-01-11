from flask import Flask, render_template, request, jsonify
from groq import Groq
from tavily import TavilyClient
import os
from datetime import datetime

app = Flask(__name__, template_folder='../templates')

# --- API PROTECTION ---
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
        # IDENTITAS DIKUNCI KE ADMIN (Bukan Kakak/Kak)
        user_name = "Kakak / Kak" 
        current_date = datetime.now().strftime("%d %B %Y")
        
        data = request.json
        user_input = data.get("message", "")
        user_mode = data.get("mode", "belajar")
        history = data.get("history", [])[-5:] 

        # --- LOGIKA SEARCH (MODE PENCARIAN) ---
        search_info = ""
        if user_mode == "pencarian" and tavily_client:
            try:
                search_res = tavily_client.search(query=f"{user_input} {current_date}", search_depth="advanced")
                search_info = " ".join([r.get('content') for r in search_res.get('results', [])])
            except: 
                search_info = "Internet akses terbatas."

        # --- LOGIKA INSTRUKSI PER MODE ---
        if user_mode == "latihan":
            mode_instruction = r"""
WAJIB: AKTIFKAN AUTO-QUIZ MODE.
1. Jika Kakak memberikan soal, JANGAN BERIKAN JAWABAN LANGSUNG.
2. Ubah menjadi kuis interaktif 4 pilihan (A, B, C, D).
3. Gunakan \ce{...} untuk kimia dan $...$ untuk matematika.
4. HANYA berikan jawaban jika Kakak sudah memilih opsi A/B/C/D.
5. Jika Kakak memberikan soal atau pertanyaan materi, JANGAN BERIKAN JAWABAN LANGSUNG.
6. Salah satu dari pilihan TERSEBUT HARUS JAWABAN YANG BENAR.
7. Berikan petunjuk (clue) singkat saja.
8. Tunggu Kakak menjawab. Jika benar, baru berikan selamat dan penjelasan step-by-step yang rapi.
9. User ingin kuis. Buatkan soal pilihan ganda sesuai materi.
10. Anda di mode latihan, siap membuatkan soal jika diminta.
11. Setelah di pilih (A/B/C/D) dari soal yang di buat, lanjut ke pemeriksaan jawban benar/salah, jika benar berikan penjelasan lengkap, jika slah berikan clue dan jika masih salah berikan penjelasan lengkap.
"""
        elif user_mode == "pencarian":
            mode_instruction = f"""
WAJIB: MODE PENCARIAN AKTIF.
1. Gunakan DATA INTERNET yang tersedia untuk menjawab.
2. Berikan informasi yang paling relevan dan terbaru.
3. Sebutkan sumber jika perlu.
4. Tetap gunakan format pemisah '---' dan LaTeX jika ada data teknis.
"""
        else: # Default: Mode Belajar
            mode_instruction = r"""
WAJIB: MODE BELAJAR AKTIF.
1. Berikan penjelasan terstruktur menggunakan "---" antar bagian.
2. Selesaikan soal step-by-step menggunakan LaTeX ($...$).
3. Gunakan \ce{...} untuk simbol kimia.
4. Berikan penjelasan yang sangat rapi, terstruktur, dan mendalam.
5. Gunakan "Pemisah Garis" (---) antar bagian agar tidak menumpuk.
6. Gunakan Bullet Points untuk poin-poin penting.
7. Jika ada rumus per (fraction), taruh di baris baru sendiri, jangan digabung di tengah kalimat.
"""

        # --- INTEGRASI SYSTEM PROMPT ---
        system_prompt = f"""
Nama kamu ERAI, Tutor Sebaya WUG untuk {user_name}.
{mode_instruction}
Hari ini: {current_date}.
DATA INTERNET: {search_info if search_info else 'Gunakan internal knowledge'}.

ATURAN FORMATTING:
- Gunakan --- untuk garis pemisah.
- Rumus matematika diapit $...$.
- Rumus kimia diapit \\ce{{...}}.
- Gunakan bahasa teman sebaya yang suportif (TAPI TETAP PANGGIL 'Kakak').
"""

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
        
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.4
        )
        return jsonify({"response": completion.choices[0].message.content})

    except Exception as e:
        error_msg = str(e).lower()
        if any(code in error_msg for code in ["429", "413", "rate_limit"]):
            return jsonify({"response": "**[WUG SECURE - NOTIFIKASI]**\n\nKuota harian atau memori token habis. Silakan coba lagi nanti, Kakak. 🚀"}), 200
        return jsonify({"response": f"**[SYSTEM ERROR]** {str(e)}"}), 200

if __name__ == '__main__':
    app.run(debug=True)
