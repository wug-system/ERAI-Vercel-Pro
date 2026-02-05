import os
from flask import Flask, render_template, request, jsonify
from groq import Groq

# --- KONFIGURASI FLASK UNTUK VERCEL ---
# Menentukan path folder template secara eksplisit agar terbaca di environment server
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Flask(__name__, template_folder=template_dir)

# Inisialisasi Client Groq (Pastikan GROQ_API_KEY sudah ada di Environment Variables Vercel)
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route('/')
def index():
    # Mencari index.html di dalam folder api/templates/
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        # --- WUG SECURE SYSTEM & ERAI IDENTITY ---
        # Menggunakan 'r' sebelum tanda kutip untuk menghindari SyntaxWarning LaTeX
        base_instruction = r"Anda adalah ERAI, Tutor Sebaya WUG (WUG Standard). Jelaskan konsep dengan terstruktur, santai namun cerdas. Gunakan analogi jika perlu. Format rumus matematika dengan $...$ (inline) atau $$...$$ (blok), dan kimia dengan \ce{...}. Selalu sapa pengguna dengan 'Kakak' atau 'Kak'."

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": base_instruction},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False
        )

        response_text = completion.choices[0].message.content
        return jsonify({"reply": response_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Standar Vercel: App harus bisa diekspor
app.debug = False # Matikan debug untuk production
