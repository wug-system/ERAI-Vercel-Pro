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
        user_name = "Kakak"
        user_mode = data.get("mode", "belajar")
        history = data.get("history", [])

        now = datetime.now()
        current_date = now.strftime("%d %B %Y") 

        search_info = ""
        # --- LOGIKA SMART SEARCH (VERSI HEMAT KUOTA) ---
        search_info = ""
        
        # 1. Daftar kata kunci yang WAJIB cari internet (berita/real-time)
        real_time_keywords = [
            "berita", "terbaru", "hari ini", "kabar", "update", 
            "banjir", "skor", "cuaca", "harga", "stok", "kejadian"
        ]
        
        # 2. Daftar kata kunci pendidikan (PASTI hemat kuota, gak usah search)
        edu_keywords = ["hitung", "rumus", "jelaskan materi", "reaksi", "apa itu", "soal"]

        # Cek apakah ada permintaan berita/kejadian terkini
        should_search = any(word in user_input.lower() for word in real_time_keywords)
        # Pastikan bukan soal pendidikan yang murni teori
        is_pure_edu = any(word in user_input.lower() for word in edu_keywords)
        
        if tavily_client and should_search and not is_pure_edu:
            try:
                # Tambahkan lokasi "Aceh" atau konteks agar hasil lebih akurat
                search_res = tavily_client.search(
                    query=user_input, 
                    search_depth="advanced", 
                    max_results=3 
                )
                context_list = [f"SUMBER: {res.get('url')} - INFO: {res.get('content')}" for res in search_res.get('results', [])]
                search_info = " ".join(context_list)
            except Exception as e:
                search_info = f"Internet sibuk, gunakan data internal. (Error: {str(e)})"

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
        
        return jsonify({"response": completion.choices[0].message.content})
    
    except Exception as e:
        return jsonify({"response": f"Waduh Kak, ada kendala: {str(e)}"}), 200

if __name__ == '__main__':
    app.run(debug=True)
