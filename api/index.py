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

        # Definisi Waktu Akurat
        now = datetime.now()
        current_date = now.strftime("%d %B %Y") 

        search_info = ""
        
        # Logika Pencarian Tavily - Diperdalam untuk Detail Kecil
        if tavily_client:
            try:
                # max_results dinaikkan ke 8 agar mencakup info spesifik/niche
                search_res = tavily_client.search(
                    query=user_input, 
                    search_depth="advanced", 
                    max_results=8
                )
                # Mengambil konten dan judul untuk akurasi lebih baik
                context_list = [f"Judul: {res.get('title')}\nIsi: {res.get('content')}" for res in search_res.get('results', [])]
                search_info = "\n\n".join(context_list)
            except Exception as e:
                search_info = f"Pencarian terbatas: {str(e)}"

        # System Prompt yang Dipertajam
        system_prompt = (
            f"Nama kamu ERAI, Tutor Sebaya standar WUG untuk {user_name}. "
            f"Konteks Waktu: {current_date}, Tahun 2026. "
            f"REFERENSI INTERNET TERBARU: {search_info}. "
            "\nKETERAMPILAN KHUSUS: "
            "1. ANALISIS DETAIL: Jangan hanya memberikan info yang populer. Jika ditanya (contoh: anime/berita/materi), "
            "berikan detail spesifik dari referensi internet yang ada, termasuk yang kurang dikenal (niche). "
            "2. ANTI-HALUSINASI: Jika data internet tidak menyebutkan sesuatu secara eksplisit, katakan 'berdasarkan info terbatas yang aku temukan' daripada mengarang. "
            "3. METODE TUTOR WUG: Jangan langsung memberi jawaban akhir soal pendidikan. Jelaskan alur berpikirnya, "
            "berikan langkah pertama, dan ajak {user_name} berdiskusi untuk langkah selanjutnya. "
            "4. GAYA BAHASA: Teman sebaya yang cerdas, santai (aku-kamu), dan sangat suportif. "
            "5. FORMAT: Rumus wajib menggunakan LaTeX ($...$). "
        )

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
        
        # Temperature 0.6 untuk keseimbangan antara kreativitas dan akurasi
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.6 
        )
        
        return jsonify({"response": completion.choices[0].message.content})
    
    except Exception as e:
        return jsonify({"response": f"Waduh Admin, ada kendala teknis: {str(e)}"}), 200
