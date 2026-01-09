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
        data = request.json
        user_input = data.get("message", "")
        # Nama paten sesuai request Admin
        user_name = "Kakak"  
        user_mode = data.get("mode", "belajar")
        history = data.get("history", [])

        # Ambil waktu sekarang untuk system prompt
        now = datetime.now()
        current_date = now.strftime("%d %B %Y") 

        search_info = ""
        
        # --- LOGIKA SMART SEARCH ---
        need_search_keywords = [
            "berita", "terbaru", "hari ini", "skor", "harga", 
            "2025", "2026", "rilis", "update", "kabar", "hot", "trending"
        ]
        
        should_search = any(word in user_input.lower() for word in need_search_keywords)
        
        if tavily_client and should_search:
            try:
                search_res = tavily_client.search(
                    query=user_input, 
                    search_depth="advanced", 
                    max_results=5 
                )
                context_list = [f"Info: {res.get('content')}" for res in search_res.get('results', [])]
                search_info = " ".join(context_list)
            except Exception:
                search_info = "Pencarian internet sedang limit."
        
        # --- LOGIKA BEHAVIOR MODE (RAW STRING) ---
        if user_mode == "latihan":
            mode_instruction = r"""
SISTEM LATIHAN AKTIF (AUTO-QUIZ MODE):
- JANGAN berikan jawaban langsung jika Kakak memberikan soal.
- Ubah soal jadi kuis interaktif dengan 4 pilihan jawaban (A, B, C, D).
- Pastikan salah satu pilihan adalah jawaban yang benar.
- Gunakan format \ce{...} untuk setiap rumus kimia (Contoh: \ce{NaCl}).
- Jika Kakak menjawab benar, beri selamat dan jelaskan penyelesaian lengkapnya menggunakan LaTeX ($...$).
"""
        else:
            mode_instruction = r"""
SISTEM BELAJAR AKTIF:
- Berikan penjelasan mendalam, rumus lengkap, dan konsep dasar.
- Selesaikan soal secara step-by-step menggunakan LaTeX ($...$).
- Gunakan format \ce{...} untuk kimia agar tidak error.
"""

        system_prompt = (
            f"Nama kamu ERAI, Tutor Sebaya WUG untuk {user_name}. "
            f"Panggil user dengan sebutan '{user_name}'. "
            f"Hari ini: {current_date}. \n"
            f"{mode_instruction} \n"
            f"DATA INTERNET: {search_info if search_info else 'Tidak perlu search'}. \n"
            "\nATURAN SISTEM: "
            "1. FORMAT: **Bold** untuk poin penting, *Italic* untuk penekanan. "
            "2. GAYA: Teman sebaya yang santai (aku-kamu), cerdas, dan sangat suportif. "
            "3. METODE TUTOR: Gunakan LaTeX ($...$) untuk matematika dan \\ce{...} untuk kimia."
        )

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
        
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.6 
        )
        
        return jsonify({"response": completion.choices[0].message.content})
    
    except Exception as e:
        return jsonify({"response": f"ERAI sedang kendala teknis: {str(e)}"}), 200

if __name__ == '__main__':
    app.run(debug=True)
