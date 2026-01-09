from flask import Flask, render_template, request, jsonify
from groq import Groq
from tavily import TavilyClient
import os
from datetime import datetime

app = Flask(__name__, template_folder='../templates')

# Inisialisasi Client
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get("message")
    user_name = data.get("name", "Admin")
    history = data.get("history", [])

    search_result = ""
    search_failed_msg = ""

    # Logika: Hanya search jika Admin tanya tentang info terbaru/berita/anime
    keywords = ["anime", "berita", "terbaru", "kabar", "siapa", "kapan", "2026", "2025"]
    if any(word in user_input.lower() for word in keywords):
        try:
            # Melakukan pencarian real-time
            response = tavily_client.search(query=user_input, max_results=3)
            search_result = f"\n\n[INFO INTERNET TERKINI]: {response['results']}"
        except Exception as e:
            # Jika kuota habis atau error
            search_failed_msg = "\n\n(Catatan: Maaf Admin, fitur pencarian internet saya sedang mencapai batas kuota bulanan. Saya akan menjawab menggunakan bank data internal dulu ya!)"

    now = datetime.now()
    current_date = now.strftime("%d %B %Y")

    system_prompt = (
        f"Nama kamu ERAI. Kamu Tutor Sebaya WUG untuk {user_name}. "
        f"Hari ini: {current_date}. Tahun: 2026. "
        f"DATA SEARCH: {search_result} {search_failed_msg}"
        "Gunakan data di atas untuk menjawab jika relevan. Jika data kosong/kuota habis, jelaskan dengan jujur. "
        "Gaya bahasa: Aku-Kamu, santai, santun, dan membimbing (jangan langsung beri jawaban akhir)."
    )

    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7
        )
        return jsonify({"response": completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
