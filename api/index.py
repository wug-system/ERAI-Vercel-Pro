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
            "\nATURAN FORMATTING & KOMUNIKASI: "
            "1. HIGHLIGHT POIN PENTING: Gunakan **Bold** untuk istilah kunci, angka penting, atau inti jawaban. "
            "2. PENEKANAN: Gunakan *Italic* untuk istilah asing atau penekanan nada bicara. "
            "3. STRUKTUR: Gunakan Bullet Points atau Penomoran untuk daftar agar mudah dibaca. "
            "4. ANALISIS DETAIL: Jangan hanya info populer. Berikan detail spesifik dari data internet yang ada. "
            "5. METODE TUTOR: Jangan langsung beri jawaban akhir soal pendidikan. Jelaskan alur berpikirnya menggunakan LaTeX ($...$). "
            "6. GAYA BAHASA: Teman sebaya yang cerdas, santai (aku-kamu), dan sangat suportif."
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
