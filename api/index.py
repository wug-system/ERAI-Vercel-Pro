from flask import Flask, render_template, request, jsonify, session
from groq import Groq
from tavily import TavilyClient
import os
from datetime import datetime

app = Flask(__name__, template_folder='../templates')
app.secret_key = "WUG_SECURE_V4_SECRET" # WAJIB: Kunci untuk memory kuis

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
        history = data.get("history", [])[-8:] 

        # --- BUG FIX: PENANGANAN GAMBAR (Hanya modifikasi tipis agar tidak crash) ---
        is_image = "[USER_IMAGE_DATA:" in user_input
        if is_image:
            extracted_msg = user_input.split("] ")[-1]
            user_input = f"[MODE ANALISIS FOTO] Kakak mengirimkan gambar. Analisis teks/soal di dalamnya dan jawab sesuai mode {user_mode}: {extracted_msg}"

        # --- BUG FIX: LOGIKA MEMORY KUIS (Hanya penambahan state tanpa ubah fitur) ---
        if 'quiz_active' not in session: session['quiz_active'] = False
        if 'last_soal' not in session: session['last_soal'] = ""

        is_answering_quiz = len(user_input.strip()) == 1 and user_input.strip().upper() in ['A', 'B', 'C', 'D']
        
        # Penanganan khusus jika sedang kuis di mode latihan
        if user_mode == "latihan" and session.get('quiz_active') and is_answering_quiz:
            soal_sebelumnya = session.get('last_soal', 'materi latihan')
            user_input = f"SAYA MEMILIH JAWABAN {user_input.upper()} untuk soal: '{soal_sebelumnya}'. Berikan penilaian BENAR/SALAH dan penjelasan lengkapnya!"
            session['quiz_active'] = False 

        # --- LOGIKA SEARCH (FITUR PATEN TIDAK BERUBAH) ---
        search_info = ""
        if user_mode == "pencarian" and tavily_client:
            try:
                search_res = tavily_client.search(query=f"{user_input} {current_date}", search_depth="advanced")
                search_info = " ".join([r.get('content') for r in search_res.get('results', [])])
            except: 
                search_info = "Internet akses terbatas."

        # --- LOGIKA INSTRUKSI PER MODE (DIKEMBALIKAN KE STRUKTUR ASLI KAKAK) ---
        if user_mode == "latihan":
            mode_instruction = r"""
WAJIB: AKTIFKAN AUTO-QUIZ MODE.
1. Jika Kakak memberikan soal/materi, JANGAN BERIKAN JAWABAN LANGSUNG.
2. Ubah menjadi kuis interaktif 4 pilihan (A, B, C, D).
3. HANYA berikan penilaian/jawaban jika Kakak sudah memilih opsi A/B/C/D.
4. Jika Kakak memberikan soal atau pertanyaan materi, JANGAN BERIKAN JAWABAN LANGSUNG.
5. Salah satu dari pilihan TERSEBUT HARUS JAWABAN YANG BENAR.
6. Gunakan \ce{...} untuk kimia dan $...$ untuk matematika.
7. Jika Kakak menjawab salah, berikan clue. Jika benar, berikan selamat dan penjelasan step-by-step.
"""
        elif user_mode == "pencarian":
            mode_instruction = f"""
WAJIB: MODE PENCARIAN AKTIF.
1. Gunakan DATA INTERNET terbaru untuk menjawab.
2. Berikan informasi relevan dan sumber data.
"""
        else: # Default: Mode Belajar (LOGIKA ASLI KAKAK)
            mode_instruction = r"""
WAJIB: MODE BELAJAR AKTIF.
1. Berikan penjelasan terstruktur dengan pemisah '---'.
2. Gunakan LaTeX ($...$) untuk rumus.
3. Gunakan DATA INTERNET yang tersedia untuk menjawab.
4. Berikan informasi yang paling relevan dan terbaru.
5. Sebutkan sumber jika perlu.
6. Gunakan \ce{...} untuk simbol kimia.
"""

        # --- INTEGRASI SYSTEM PROMPT (LOGIKA ASLI KAKAK) ---
        system_prompt = f"""
Nama kamu ERAI, Tutor Sebaya WUG untuk {user_name}. 
Sistem Keamanan: WUG Secure Active.
{mode_instruction}
Hari ini: {current_date}.
DATA INTERNET: {search_info if search_info else 'Gunakan internal knowledge'}.

ATURAN FORMATTING:
- Gunakan --- untuk pemisah.
- Rumus matematika $...$, kimia \\ce{{...}}.
- Selalu panggil 'Kakak'.
"""

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
        
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.3 
        )

        response_text = completion.choices[0].message.content

        # UPDATE SESSION UNTUK KUIS (PENTING)
        if user_mode == "latihan" and ("A." in response_text or "A)" in response_text):
            session['quiz_active'] = True
            session['last_soal'] = response_text 

        return jsonify({
            "response": response_text,
            "is_quiz_active": session.get('quiz_active', False)
        })

    except Exception as e:
        error_msg = str(e).lower()
        if any(code in error_msg for code in ["429", "413", "rate_limit"]):
            return jsonify({"response": "**[WUG SECURE - NOTIFIKASI]**\n\nKuota harian habis atau file terlalu besar. Silakan coba lagi nanti, Kakak. 🚀"}), 200
        return jsonify({"response": f"**[SYSTEM ERROR]** {str(e)}"}), 200

if __name__ == '__main__':
    app.run(debug=True)
