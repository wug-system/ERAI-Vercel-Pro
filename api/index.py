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
        # --- FIX 1: Definisikan variabel yang dipanggil di prompt ---
        user_name = "nanas" 
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
                    search_res = tavily_client.search(query=user_input, search_depth="basic")
                    search_info = " ".join([r.get('content') for r in search_res.get('results', [])])
                except:
                    search_info = "Gagal mengambil data internet."
            
            mode_instruction = "MODE PENCARIAN AKTIF: Gunakan DATA INTERNET untuk menjawab sedetail mungkin."
        
        elif user_mode == "latihan":
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
"""
        else:
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

        system_prompt = f"""
Nama kamu ERAI, Tutor Sebaya WUG untuk {user_name}.
{mode_instruction}
Hari ini: {current_date}.
DATA INTERNET: {search_info if search_info else 'Gunakan internal knowledge'}.

ATURAN FORMATTING:
- Gunakan --- untuk garis pemisah.
- Rumus matematika diapit $...$.
- Rumus kimia diapit \\ce{{...}}.
- Gunakan bahasa teman sebaya yang suportif.
"""

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
        
        # --- FIX 2: Gunakan model yang lebih stabil untuk akun gratis ---
        # Llama-3.3-70b sering overload di jam sibuk, 8b-instant jauh lebih lancar
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=messages,
            temperature=0.4
        )
        
        # --- FIX 3: Perbaikan Indentasi Return ---
        return jsonify({"response": completion.choices[0].message.content})
   
    except Exception as e:
        error_msg = str(e)
        # Jika error karena API Key kosong
        if "api_key" in error_msg.lower():
            return jsonify({"response": "**[SYSTEM ERROR]** API Key belum terpasang di Vercel, Kak."}), 200
            
        # Menyamarkan error Rate Limit (429)
        if "429" in error_msg or "rate_limit" in error_msg.lower():
            return jsonify({
                "response": (
                    "**[WUG SECURE SYSTEM - NOTIFICATION]**\n\n"
                    "Mohon maaf, Kak / Kakak. Kuota harian model ini sedang penuh. "
                    "Reset otomatis terjadi setiap jam 00:00 UTC. Coba lagi sebentar lagi ya! 🚀"
                )
            }), 200
        
        # Error lainnya (Debug)
        return jsonify({"response": f"**[SYSTEM ERROR]** Terjadi gangguan: {error_msg}"}), 200

if __name__ == '__main__':
    app.run(debug=True)
