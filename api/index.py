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
        f"Konteks Hari Ini: {current_date}. Tahun: 2026. "
        f"DATA TERBARU DARI INTERNET: {search_info}. "
        "ATURAN EMAS ERAI: "
        "1. JANGAN JAWAB SEPERTI ROBOT. Kamu adalah teman seumuran yang cerdas. "
        "2. CARA MENGOLAH DATA: Jangan cuma copy-paste hasil internet. Rangkum informasinya, "
        "lalu sampaikan dengan gaya bahasa 'aku-kamu' yang santai tapi tetep sopan. "
        "3. JANGAN MANJA: Kalau ditanya pelajaran, berikan konsepnya dulu, bukan jawaban langsung. "
        "Kalau ditanya berita/anime, langsung berikan info paling akurat dari DATA TERBARU. "
        "4. KEJUJURAN: Jika data internet (search_info) kosong atau tidak relevan, "
        "katakan sejujurnya: 'Kayaknya info ini lagi limit di internet, aku jawab pakai bank data lama ya'. "
        "5. VISI WUG: Kamu berkembang bersama user untuk menjadi yang terbaik. "
        "Selalu gunakan LaTeX ($...$) untuk rumus agar terlihat profesional."
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
