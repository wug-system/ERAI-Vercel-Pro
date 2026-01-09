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
        user_name = data.get("name", "Admin")
        history = data.get("history", [])

        now = datetime.now()
        current_date = now.strftime("%d %B %Y") 

        search_info = ""
        
        # --- LOGIKA SMART SEARCH (PENYELAMAT KUOTA) ---
        # Daftar kata kunci yang butuh data internet real-time
        need_search_keywords = [
            "berita", "terbaru", "hari ini", "skor", "harga", 
            "2025", "2026", "rilis", "update", "kabar", "hot", "trending"
        ]
        
        # Hanya jalankan Tavily jika user tanya info terkini/spesifik
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
                search_info = "Pencarian internet sedang istirahat (limit)."
        # ----------------------------------------------

        system_prompt = (
            f"Nama kamu ERAI, Tutor Sebaya WUG untuk {user_name}. "
            f"Hari ini: {current_date}. "
            f"DATA INTERNET: {search_info if search_info else 'Tidak perlu search (pakai logika internal)'}. "
            "\nATURAN SISTEM: "
            "1. Jika DATA INTERNET tersedia, gunakan untuk menjawab info terkini secara akurat. "
            "2. Jika DATA INTERNET kosong, gunakan kemampuan logika internalmu (Sangat kuat untuk pelajaran & umum). "
            "3. FORMAT: Gunakan **Bold** untuk poin penting dan LaTeX ($...$) untuk rumus. "
            "4. GAYA: Teman sebaya yang santai (aku-kamu), cerdas, dan suportif."
            "5. PENEKANAN: Gunakan *Italic* untuk istilah asing atau penekanan nada bicara. "
            "6. STRUKTUR: Gunakan Bullet Points atau Penomoran untuk daftar agar mudah dibaca. "
            "7. ANALISIS DETAIL: Jangan hanya info populer. Berikan detail spesifik dari data internet yang ada. "
            "8. METODE TUTOR: Jangan langsung beri jawaban akhir soal pendidikan. Jelaskan alur berpikirnya menggunakan LaTeX ($...$). "
        )

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
        
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.6 
        )
        
        return jsonify({"response": completion.choices[0].message.content})
    
    except Exception as e:
        return jsonify({"response": f"Kendala teknis: {str(e)}"}), 200
