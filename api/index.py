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

        # DEFINISIKAN variabel waktu di sini agar tidak error
        now = datetime.now()
        current_date = now.strftime("%d %B %Y") 

        search_info = ""
        
        # Logika Pencarian Tavily
        if tavily_client:
            try:
                # Kita buat pencarian lebih cerdas
                search_res = tavily_client.search(query=user_input, search_depth="advanced", max_results=5)
                context_list = [res.get('content', '') for res in search_res.get('results', [])]
                search_info = " ".join(context_list)
            except Exception as e:
                search_info = f"Pencarian sedang limit atau gangguan: {str(e)}"

        # Masukkan variabel current_date ke dalam prompt
        system_prompt = (
            f"Nama kamu ERAI. Kamu Tutor Sebaya WUG untuk {user_name}. "
            f"Hari ini: {current_date}. Tahun: 2026. "
            f"DATA TERBARU DARI INTERNET: {search_info}. "
            "ATURAN EMAS ERAI: "
            "1. Kamu adalah teman seumuran yang cerdas, santai (aku-kamu), dan santun. "
            "2. Gunakan DATA TERBARU untuk menjawab info terkini secara akurat. "
            "3. Jika membahas pelajaran, jelaskan konsepnya dulu (jangan langsung beri jawaban akhir). "
            "4. Gunakan LaTeX ($...$) untuk semua rumus matematika atau kimia."
        )

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
        
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7
        )
        
        return jsonify({"response": completion.choices[0].message.content})
    
    except Exception as e:
        # Menampilkan error spesifik agar kita mudah perbaiki
        return jsonify({"response": f"Waduh Admin, ada kendala teknis: {str(e)}"}), 200
