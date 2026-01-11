from flask import Flask, render_template, request, jsonify
from groq import Groq
from tavily import TavilyClient
import os
from datetime import datetime

app = Flask(__name__, template_folder='../templates')

# --- API PROTECTION ---
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
        user_name = "Kakak / Kak" 
        current_date = datetime.now().strftime("%d %B %Y")
        data = request.json
        user_input = data.get("message", "")
        user_mode = data.get("mode", "belajar")
        # Batasi history 5 pesan terakhir agar tidak overload (TPM limit)
        history = data.get("history", [])[-5:] 

        search_info = ""
        if user_mode == "pencarian" and tavily_client:
            try:
                search_res = tavily_client.search(query=f"{user_input} {current_date}", search_depth="advanced")
                search_info = " ".join([r.get('content') for r in search_res.get('results', [])])
            except: search_info = "Internet akses terbatas."

        system_prompt = f"Nama: ERAI. User: {user_name}. Hari ini: {current_date}. Mode: {user_mode}. Gunakan LaTeX $...$ dan pemisah ---."
        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
        
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.4
        )
        return jsonify({"response": completion.choices[0].message.content})

    except Exception as e:
        error_msg = str(e).lower()
        if any(code in error_msg for code in ["429", "413", "rate_limit"]):
            return jsonify({"response": "**[WUG SECURE - NOTIFIKASI]**\n\nKuota harian/token habis. Silakan coba lagi nanti, Admin. 🚀"}), 200
        return jsonify({"response": f"**[SYSTEM ERROR]** {str(e)}"}), 200

if __name__ == '__main__':
    app.run(debug=True)
