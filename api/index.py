from flask import Flask, render_template, request, jsonify, session
from groq import Groq
from tavily import TavilyClient
import os
from datetime import datetime

app = Flask(__name__, template_folder='templates') # Pastikan folder template benar
app.secret_key = "ERAI_SECURE_KEY_2026"

# --- CONFIGURATION ---
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
        data = request.json
        user_input = data.get("message", "")
        user_mode = data.get("mode", "belajar") # belajar, latihan, pencarian
        history = data.get("history", [])[-10:] # Ambil 10 percakapan terakhir context window
        
        current_date = datetime.now().strftime("%d %B %Y")

        # --- SESSION MANAGEMENT UNTUK KUIS ---
        if 'quiz_active' not in session: session['quiz_active'] = False
        if 'last_soal' not in session: session['last_soal'] = ""

        # Deteksi jawaban A, B, C, D
        is_answering_quiz = len(user_input.strip()) == 1 and user_input.strip().upper() in ['A', 'B', 'C', 'D']

        # --- LOGIKA MODE LATIHAN (STRICT) ---
        if user_mode == "latihan":
            if is_answering_quiz and session.get('quiz_active'):
                # User menjawab
                soal_ref = session.get('last_soal', '')
                user_input = f"""
                [JAWABAN USER: {user_input.upper()}]
                Soal sebelumnya: '{soal_ref}'
                INSTRUKSI:
                1. Langsung nyatakan BENAR atau SALAH.
                2. Berikan penjelasan lengkap dan mendalam (gunakan format LaTeX/Kimia).
                3. Jangan tawarkan soal baru dulu.
                """
                session['quiz_active'] = False # Reset kuis
            elif not is_answering_quiz:
                # User minta soal / kirim materi
                user_input = f"""
                [PERMINTAAN SOAL/MATERI: {user_input}]
                INSTRUKSI:
                1. Buatkan 1 (SATU) soal pilihan ganda (A, B, C, D) yang berbobot.
                2. JANGAN berikan jawaban atau penjelasan sekarang.
                3. Tunggu user menjawab.
                """

        # --- LOGIKA PENCARIAN (WEB SEARCH) ---
        search_context = ""
        if user_mode == "pencarian" and tavily_client:
            try:
                # Search query optimization
                search_res = tavily_client.search(query=f"{user_input} {current_date}", search_depth="advanced")
                raw_results = search_res.get('results', [])
                search_context = "\n\nDATA INTERNET TERBARU:\n" + "\n".join([f"- {r['content']} (Sumber: {r['url']})" for r in raw_results])
            except:
                search_context = "\n(Koneksi internet untuk pencarian terbatas, gunakan pengetahuan internal)."

        # --- SYSTEM PROMPT (PERSONA & FORMATTING) ---
        # Anonim, Cerdas, Spesifik Mode
        
        base_instruction = ""
        if user_mode == "belajar":
            base_instruction = "Anda adalah asisten belajar yang cerdas. Jelaskan konsep dengan terstruktur, gunakan analogi jika perlu. Format rumus matematika dengan $...$ (inline) atau $$...$$ (blok), dan kimia dengan \ce{...}."
        elif user_mode == "latihan":
            base_instruction = "Anda adalah penguji yang tegas namun edukatif. Fokus pada format Soal Pilihan Ganda. Jika memberikan penjelasan, harus sangat mendetail."
        elif user_mode == "pencarian":
            base_instruction = "Anda adalah mesin pencari pintar. Jawab langsung pada intinya berdasarkan Data Internet yang disediakan. Sertakan sumber."

        system_prompt = f"""
        Role: ERAI (Educational Resource AI).
        User: Panggil "Kakak".
        Tanggal: {current_date}.
        Mode: {user_mode.upper()}.
        
        INSTRUKSI UTAMA:
        {base_instruction}

        FORMATTING WAJIB:
        - Matematika: Gunakan $...$ untuk inline, $$...$$ untuk block.
        - Kimia: Gunakan \ce{{...}}.
        - Layout: Gunakan Markdown rapi (Bold, List, Header).
        
        CONTEXT TAMBAHAN:
        {search_context}
        """

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]

        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.3 if user_mode == "latihan" else 0.6 # Lebih kreatif di mode belajar, strict di latihan
        )

        response_text = completion.choices[0].message.content

        # Update Session jika AI memberikan soal baru
        if user_mode == "latihan" and ("A." in response_text or "A)" in response_text) and not is_answering_quiz:
            session['quiz_active'] = True
            session['last_soal'] = response_text

        return jsonify({
            "response": response_text,
            "mode": user_mode,
            "is_quiz_active": session.get('quiz_active', False)
        })

    except Exception as e:
        return jsonify({"response": f"Maaf Kak, ada kesalahan sistem: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
