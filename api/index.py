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
        user_mode = data.get("mode", "belajar")
        history = data.get("history", []) # Ini sudah terfilter dari frontend

        # --- LOGIKA MODE PENCARIAN (STRICT SEARCH) ---
        search_info = ""
        if user_mode == "pencarian":
            # Di mode ini, AI WAJIB cari internet dulu
            if tavily_client:
                search_res = tavily_client.search(query=user_input, search_depth="advanced")
                search_info = " ".join([r.get('content') for r in search_res.get('results', [])])
            
            mode_instruction = r"MODE PENCARIAN AKTIF: Gunakan DATA INTERNET untuk menjawab sedetail mungkin."
        
        elif user_mode == "latihan":
            mode_instruction = r"MODE LATIHAN: Buat kuis 4 pilihan. DILARANG kasih jawaban langsung."
        else:
            mode_instruction = r"MODE BELAJAR: Jelaskan materi step-by-step dengan rapi."

        # ... (Sisa logika prompt & Groq sama seperti sebelumnya) ...

        # --- REVISI LOGIKA BEHAVIOR (KETAT) ---
        if user_mode == "latihan":
            mode_instruction = r"""
WAJIB: AKTIFKAN AUTO-QUIZ MODE.
1. Jika Kakak memberikan soal atau pertanyaan materi, JANGAN BERIKAN JAWABAN LANGSUNG.
2. Ubah soal tersebut menjadi kuis interaktif dengan 4 pilihan (A, B, C, D).
3. Salah satu dari pilihan TERSEBUT HARUS JAWABAN YANG BENAR.
4. Berikan petunjuk (clue) singkat saja.
5. Gunakan format \ce{...} untuk kimia dan $...$ untuk matematika.
6. Tunggu Kakak menjawab. Jika benar, baru berikan selamat dan penjelasan step-by-step yang rapi.
7. Jika ada rumus per (fraction), taruh di baris baru sendiri, jangan digabung di tengah kalimat.
8. Jika Kakak kasih soal/materi, kamu WAJIB buat kuis 4 pilihan (A, B, C, D).
9. Salah satu pilihan HARUS jawaban yang benar.
10. Berikan tantangan, bukan jawaban.
11. Gunakan \ce{...} dan $...$.
12. HANYA berikan jawaban jika Kakak sudah memilih opsi A/B/C/D.
"""
        else:
            mode_instruction = r"""
WAJIB: MODE BELAJAR AKTIF.
1. Berikan penjelasan yang sangat rapi, terstruktur, dan mendalam.
2. Gunakan "Pemisah Garis" (---) antar bagian agar tidak menumpuk.
3. Selesaikan soal secara step-by-step menggunakan LaTeX ($...$).
4. Gunakan format \ce{...} untuk setiap simbol kimia (Contoh: \ce{H2O}).
5. Gunakan Bullet Points untuk poin-poin penting.
6. Jika ada rumus per (fraction), taruh di baris baru sendiri, jangan digabung di tengah kalimat.
"""

        system_prompt = rf"""
Nama kamu ERAI, Tutor Sebaya WUG untuk {user_name}.
{mode_instruction}
Hari ini: {current_date}.
DATA INTERNET: {search_info if search_info else 'Gunakan internal knowledge'}.

ATURAN FORMATTING WAJIB:
- Gunakan --- untuk membuat garis pemisah antar sub-bab agar rapi.
- Gunakan **Bold** untuk judul langkah atau poin penting.
- Semua rumus matematika WAJIB diapit $...$.
- Semua rumus kimia WAJIB diapit \ce{{...}}.
- Gunakan bahasa teman sebaya yang suportif dan cerdas.
- Jika DATA INTERNET tersedia, kamu HARUS merangkumnya menjadi berita yang jelas untuk {user_name}. Jangan bilang "saya tidak tahu".
"""

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
        
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.4 # Suhu lebih rendah agar lebih patuh pada format
        )

# GANTI BAGIAN INI UNTUK TESTING
try:
    completion = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant", # Pakai yang ringan dulu
        messages=messages,
        temperature=0.5
    )
    return jsonify({"response": completion.choices[0].message.content})

except Exception as e:
    # SEMENTARA: Biar kita tahu error aslinya apa, jangan disamarkan dulu
    return jsonify({"response": f"DEBUG ERROR: {str(e)}"}), 200

    
        
       

if __name__ == '__main__':
    app.run(debug=True)
