from flask import Flask, render_template, request, jsonify
from groq import Groq
from tavily import TavilyClient
import os
from datetime import datetime

app = Flask(__name__, template_folder='../templates')

# Gunakan proteksi agar tidak crash jika API Key kosong
GROQ_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_KEY = os.environ.get("TAVILY_API_KEY")

groq_client = Groq(api_key=GROQ_KEY)
# Inisialisasi Tavily hanya jika key tersedia
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

        search_info = ""
        
        # Logika Pencarian yang lebih kuat
        # Kita perlu menghapus filter kata kunci agar dia bisa mencari APAPUN yang Admin tanya
        if tavily_client:
            try:
                # Gunakan search_depth="advanced" agar hasilnya lebih mendalam
                search_res = tavily_client.search(query=user_input, search_depth="advanced", max_results=5)
                
                # Menggabungkan konten hasil pencarian menjadi satu teks utuh
                context_list = [res.get('content', '') for res in search_res.get('results', [])]
                search_info = " ".join(context_list)
                
            except Exception as e:
                search_info = f"Gagal akses internet: {str(e)}"

        
        system_prompt = (
        f"Nama kamu ERAI. Kamu Tutor Sebaya WUG untuk {user_name}. "
        f"STATUS: INTERNET AKTIF. TAHUN: 2026. DATA TERBARU: {search_info}. "
        "ATURAN KERJA: "
        "1. Jika ada data di 'DATA TERBARU', kamu WAJIB menggunakannya untuk menjawab. "
        "2. Jangan pernah memberikan saran umum (seperti 'cek MyAnimeList') jika ada data spesifik yang bisa kamu berikan. "
        "3. Jika data internet kosong, baru kamu boleh jujur bahwa kuota search sedang habis. "
        "4. Tetap santai (aku-kamu), gunakan LaTeX ($...$) untuk rumus, dan jangan manjakan user dengan jawaban instan jika itu soal pelajaran."
    )

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
        
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )
        
        return jsonify({"response": completion.choices[0].message.content})
    
    except Exception as e:
        # Menampilkan pesan error di chat agar Admin tahu rusaknya di mana
        return jsonify({"response": f"Waduh Admin, ada kendala teknis: {str(e)}"}), 200
