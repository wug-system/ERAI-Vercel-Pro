from flask import Flask, render_template, request, jsonify
from groq import Groq
from tavily import TavilyClient
import os
from datetime import datetime

app = Flask(__name__, template_folder='../templates')

# --- WUG SECURE SYSTEM - API PROTECTION ---
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
        user_name = "Admin / 082359161055" 
        current_date = datetime.now().strftime("%d %B %Y")
        
        data = request.json
        user_input = data.get("message", "")
        user_mode = data.get("mode", "belajar")
        # Batasi history agar tidak Request Too Large (413/TPM Limit)
        history = data.get("history", [])[-6:] 

        search_info = ""
        if user_mode == "pencarian":
            if tavily_client:
                try:
                    search_res = tavily_client.search(query=f"{user_input} {current_date}", search_depth="advanced")
                    search_info = " ".join([r.get('content') for r in search_res.get('results', [])])
                except: search_info = "Gagal akses internet."
            mode_instruction = "MODE PENCARIAN AKTIF: Gunakan data internet terbaru 2026."
        elif user_mode == "latihan":
            mode_instruction = "WAJIB: KUIS MODE. Berikan soal pilihan ganda (A-D). Jangan beri jawaban dulu."
        else:
            mode_instruction = "WAJIB: MODE BELAJAR. Penjelasan step-by-step dengan LaTeX $...$ dan garis pemisah ---."

        system_prompt = f"Nama: ERAI. User: {user_name}. Hari ini: {current_date}. {mode_instruction}"

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
        
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.4
        )
        
        return jsonify({"response": completion.choices[0].message.content})

    except Exception as e:
        error_msg = str(e).lower()
        # FIX: Pesan pengganti kuota habis sesuai permintaan
        if "429" in error_msg or "rate_limit" in error_msg or "413" in error_msg:
            return jsonify({"response": "**[WUG SECURE SYSTEM - NOTIFICATION]**\n\nMohon maaf, Admin. Kuota harian model (TPM/RPM) telah mencapai batas maksimal. 🚀\n\nSistem akan reset secara otomatis dalam beberapa jam. Silakan istirahat dulu, Admin!"}), 200
        return jsonify({"response": f"**[SYSTEM ERROR]** Terjadi gangguan: {str(e)}"}), 200

if __name__ == '__main__':
    app.run(debug=True)
