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
        
        # Logika Pencarian
        keywords = ["anime", "berita", "terbaru", "kabar", "2026"]
        if tavily_client and any(word in user_input.lower() for word in keywords):
            try:
                search_res = tavily_client.search(query=user_input, max_results=3)
                search_info = f"\n\nInfo Terkini: {search_res.get('results', [])}"
            except:
                search_info = "\n\n(Fitur pencarian sedang limit/gangguan)"

        system_prompt = (
            f"Nama kamu ERAI. Tutor Sebaya WUG untuk {user_name}. "
            f"Sekarang: {datetime.now().year}. Data terbaru: {search_info}. "
            "Gunakan format LaTeX $...$ dan jadilah teman belajar yang santun."
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
