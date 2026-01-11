from flask import Flask, render_template, request, jsonify, session
from groq import Groq
from tavily import TavilyClient
import os
from datetime import datetime

app = Flask(__name__, template_folder='../templates')
app.secret_key = "WUG_SECURE_V4_SECRET" # WAJIB: Untuk mengaktifkan memory/session

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
        user_name = "Kakak / Kak" 
        current_date = datetime.now().strftime("%d %B %Y")
        
        data = request.json
        user_input = data.get("message", "")
        user_mode = data.get("mode", "belajar")
        # Ambil history, batasi agar tidak memakan kuota token berlebih
        history = data.get("history", [])[-6:] 

        # --- BUG FIX: PENANGANAN GAMBAR (Agar tidak Error 413/429) ---
        # Jika input mengandung data gambar Base64, kita bersihkan agar Groq tidak crash
        is_image = "[USER_IMAGE_DATA:" in user_input
        if is_image:
            # Karena Llama-3-8b via Groq tidak dukung Vision, kita beri instruksi khusus
            # Agar AI tahu dia sedang menganalisis file (Backend akan memproses teksnya saja)
            user_input = "Kakak mengirimkan file gambar/foto. Tolong fokus pada instruksi di dalam foto tersebut: " + user_input.split("] ")[-1]

        # --- BUG FIX: LOGIKA MEMORY KUIS (State Management) ---
        if 'quiz_active' not in session: session['quiz_active'] = False
        if 'last_soal' not in session: session['last_soal'] = ""

        # Cek apakah user menjawab A/B/C/D saat kuis aktif
        is_answering_quiz = len(user_input.strip()) == 1 and user_input.strip().upper() in ['A', 'B', 'C', 'D']
        
        if user_mode == "latihan" and session['quiz_active'] and is_answering_quiz:
            # Paksa AI untuk menilai jawaban, bukan buat soal baru
            user_input = f"SAYA MEMILIH JAWABAN {user_input.upper()} untuk soal sebelumnya. Berikan penilaian benar/salah dan penjelasan."
            session['quiz_active'] = False 

        # --- LOGIKA SEARCH (MODE PENCARIAN) ---
        search_info = ""
        if user_mode == "pencarian" and tavily_client:
            try:
                search_res = tavily_client.search(query=f"{user_input} {current_date}", search_depth="advanced")
                search_info = " ".join([r.get('content') for r in search_res.get('results', [])])
            except: 
                search_info = "Internet akses terbatas."

        # --- LOGIKA INSTRUKSI PER MODE (TIDAK BERUBAH) ---
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
9. Lanjut ke pemeriksaan jawaban benar/salah, jika benar berikan penjelasan lengkap, jika salah berikan clue.
"""
        elif user_mode == "pencarian":
            mode_instruction = f"""
WAJIB: MODE PENCARIAN AKTIF.
1. Gunakan DATA INTERNET yang tersedia untuk menjawab.
2. Berikan informasi terbaru dan sebutkan sumber jika perlu.
"""
        else: # Default: Mode Belajar
            mode_instruction = r"""
WAJIB: MODE BELAJAR AKTIF.
1. Berikan penjelasan terstruktur menggunakan "---".
2. Selesaikan soal step-by-step menggunakan LaTeX ($...$).
3. Gunakan DATA INTERNET yang tersedia untuk menjawab.
4. Berikan informasi yang paling relevan dan terbaru.
5. Sebutkan sumber jika perlu.
"""

        # --- INTEGRASI SYSTEM PROMPT ---
        system_prompt = f"""
Nama kamu ERAI, Tutor Sebaya WUG untuk {user_name}. 
Sistem Keamanan: WUG Secure Active.
{mode_instruction}
Hari ini: {current_date}.
DATA INTERNET: {search_info if search_info else 'Gunakan internal knowledge'}.

ATURAN FORMATTING:
- Gunakan --- untuk garis pemisah.
- Rumus matematika diapit $...$.
- Rumus kimia diapit \\ce{{...}}.
- Panggil 'Kakak'.
"""

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
        
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.4
        )

        response_text = completion.choices[0].message.content

        # Simpan status jika AI memberikan kuis baru
        if user_mode == "latihan" and ("A." in response_text or "A)" in response_text):
            session['quiz_active'] = True
            session['last_soal'] = response_text

        return jsonify({"response": response_text})

    except Exception as e:
        error_msg = str(e).lower()
        if any(code in error_msg for code in ["429", "413", "rate_limit", "request_too_large"]):
            return jsonify({"response": "**[WUG SECURE - NOTIFIKASI]**\n\nKuota harian habis atau file terlalu besar (413/429). Silakan coba kirim teksnya saja atau tunggu beberapa saat, Kakak. 🚀"}), 200
        return jsonify({"response": f"**[SYSTEM ERROR]** {str(e)}"}), 200

if __name__ == '__main__':
    app.run(debug=True)
