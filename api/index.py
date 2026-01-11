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

        # --- BUG FIX: PENANGANAN GAMBAR ---
        is_image = "[USER_IMAGE_DATA:" in user_input
        if is_image:
            extracted_msg = user_input.split("] ")[-1]
            user_input = f"[ANALISIS FOTO] {extracted_msg}. Instruksi: Identifikasi semua teks, rumus matematika, dan senyawa kimia. Respon sesuai mode {user_mode}."

        # --- BUG FIX: LOGIKA MEMORY KUIS ---
        if 'quiz_active' not in session: session['quiz_active'] = False
        if 'last_soal' not in session: session['last_soal'] = ""

        is_answering_quiz = len(user_input.strip()) == 1 and user_input.strip().upper() in ['A', 'B', 'C', 'D']
        
        # --- REVISI MODE LATIHAN: SEKALI JAWAB LANGSUNG FINISH ---
        if user_mode == "latihan":
            if is_answering_quiz and session.get('quiz_active'):
                soal_ref = session.get('last_soal', '')
                user_input = f"SAYA MEMILIH {user_input.upper()}. Berdasarkan kuis ini: '{soal_ref}', SEGERA berikan penilaian BENAR atau SALAH, lalu berikan penjelasan lengkapnya menggunakan format LaTeX/Kimia. Jangan memberikan kesempatan menjawab lagi."
                session['quiz_active'] = False 
            elif not is_answering_quiz:
                user_input = f"BUATKAN KUIS PILIHAN GANDA (A, B, C, D) dari materi ini. Gunakan format LaTeX/Kimia pada soal jika perlu. JANGAN DIJELASKAN SEKARANG: {user_input}"

        # --- LOGIKA SEARCH (FITUR PATEN TIDAK BERUBAH) ---
        search_info = ""
        if user_mode == "pencarian" and tavily_client:
            try:
                search_res = tavily_client.search(query=f"{user_input} {current_date}", search_depth="advanced")
                search_info = " ".join([r.get('content') for r in search_res.get('results', [])])
            except: 
                search_info = "Internet akses terbatas."

        # --- LOGIKA INSTRUKSI PER MODE DENGAN FORMAT TEKS ASING ---
        # Menambahkan aturan deteksi teks asing ke setiap mode
        format_asing_rule = r"""
PENTING (IDENTIFIKASI TEKS ASING):
- MATEMATIKA: Gunakan $...$ untuk simbol/rumus inline (misal: $E=mc^2$) dan $$...$$ untuk rumus blok.
- KIMIA: Gunakan \ce{...} untuk semua senyawa kimia dan reaksi (misal: \ce{H2SO4}).
- FISIKA: Gunakan satuan internasional dan format pangkat LaTeX.
"""

        if user_mode == "latihan":
            mode_instruction = f"""
WAJIB: MODE KUIS SEKALI JAWAB.
{format_asing_rule}
1. Jika Kakak memberi materi/soal, buatkan kuis A, B, C, D tanpa penjelasan.
2. Jika Kakak menjawab A/B/C/D, berikan penilaian (BENAR/SALAH) dan LANGSUNG berikan penjelasan lengkap materi tersebut.
3. Setelah penjelasan diberikan, kuis dianggap selesai.
"""
        elif user_mode == "pencarian":
            mode_instruction = f"""
WAJIB: MODE PENCARIAN AKTIF.
{format_asing_rule}
1. Gunakan DATA INTERNET terbaru untuk menjawab.
2. Berikan informasi relevan dan sumber data.
"""
        else: # Default: Mode Belajar
            mode_instruction = f"""
WAJIB: MODE BELAJAR AKTIF.
{format_asing_rule}
1. Berikan penjelasan terstruktur dengan pemisah '---'.
2. Gunakan DATA INTERNET yang tersedia untuk menjawab.
3. Berikan informasi yang paling relevan dan terbaru.
4. Sebutkan sumber jika perlu.
"""

        # --- INTEGRASI SYSTEM PROMPT ---
        system_prompt = f"""
Nama kamu ERAI, Tutor Sebaya WUG untuk {user_name}. 
Sistem Keamanan: WUG Secure Active.
{mode_instruction}
Hari ini: {current_date}.
DATA INTERNET: {search_info if search_info else 'Gunakan internal knowledge'}.

ATURAN FORMATTING:
- Gunakan --- untuk pemisah.
- Selalu panggil 'Kakak'.
"""

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
        
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.1 
        )

        response_text = completion.choices[0].message.content

        # UPDATE SESSION: Aktifkan kuis hanya saat soal baru muncul
        if user_mode == "latihan" and ("A." in response_text or "A)" in response_text) and not is_answering_quiz:
            session['quiz_active'] = True
            session['last_soal'] = response_text 

        return jsonify({
            "response": response_text,
            "is_quiz_active": session.get('quiz_active', False)
        })

    except Exception as e:
        error_msg = str(e).lower()
        if any(code in error_msg for code in ["429", "413", "rate_limit"]):
            return jsonify({"response": "**[WUG SECURE - NOTIFIKASI]**\n\nKuota habis atau file terlalu besar, Kak. 🚀"}), 200
        return jsonify({"response": f"**[SYSTEM ERROR]** {str(e)}"}), 200

if __name__ == '__main__':
    app.run(debug=True)
