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
        user_name = data.get("name", "Admin")
        user_mode = data.get("mode", "belajar")  # Menangkap mode dari UI
        history = data.get("history", [])

        now = datetime.now()
        current_date = now.strftime("%d %B %Y") 

        search_info = ""
        
        # --- LOGIKA SMART SEARCH (PENYELAMAT KUOTA) ---
        need_search_keywords = [
            "berita", "terbaru", "hari ini", "skor", "harga", 
            "2025", "2026", "rilis", "update", "kabar", "hot", "trending"
        ]
        
        should_search = any(word in user_input.lower() for word in need_search_keywords)
        
        if tavily_client and should_search:
            try:
                search_res = tavily_client.search(
                    query=user_input, 
                    search_depth="advanced", 
                    max_results=5 
                )
                context_list = [f"Info: {res.get('content')}" for res in search_res.get('results', [])]
                search_info = " ".join(context_list)
            except Exception:
                search_info = "Pencarian internet sedang istirahat (limit)."
        # ----------------------------------------------

        # --- LOGIKA BEHAVIOR MODE (BELAJAR vs LATIHAN) ---
        if user_mode == "latihan":
            mode_instruction = (
                "SISTEM LATIHAN AKTIF: \n"
                "SISTEM LATIHAN AKTIF (AUTO-QUIZ MODE): \n"
                "- Jika user memberikan soal/pertanyaan, JANGAN berikan jawaban atau penyelesaiannya. \n"
                "- Tugasmu adalah mengubah soal tersebut menjadi kuis interaktif. \n"
                "- Berikan panduan awal atau petunjuk kecil (clue), lalu berikan 4 pilihan jawaban (A, B, C, D). \n"
                "- Jika user bertanya 'apa jawabannya?', tetap jangan diberi. Tantang mereka untuk memilih dari pilihan yang kamu buat. \n"
                "- Gunakan kalimat penyemangat seperti 'Coba asah otak dulu, Admin! Kira-kira mana jawaban yang paling tepat?'"
                "- Jangan berikan materi panjang lebar. \n"
                "- Berikan **Kuis Singkat** atau **Soal Latihan** terkait topik yang dibahas. \n"
                "- Gunakan format Pilihan Ganda (A, B, C, D) jika memungkinkan. \n"
                "- Tunggu user menjawab, jangan langsung beri kunci jawaban. \n"
                "- Berikan tantangan kecil agar user aktif berpikir."
                "- Jika DATA INTERNET tersedia, gunakan untuk menjawab info terkini secara akurat. "
                "- Jika DATA INTERNET kosong, gunakan kemampuan logika internalmu (Sangat kuat untuk pelajaran & umum). "
                "- FORMAT: Gunakan **Bold** untuk poin penting dan LaTeX ($...$) untuk rumus. "
                "- GAYA: Teman sebaya yang santai (aku-kamu), cerdas, dan suportif."
                "- PENEKANAN: Gunakan *Italic* untuk istilah asing atau penekanan nada bicara. "
                "- STRUKTUR: Gunakan Bullet Points atau Penomoran untuk daftar agar mudah dibaca. "
                "- ANALISIS DETAIL: Jangan hanya info populer. Berikan detail spesifik dari data internet yang ada. "
                "- METODE TUTOR: Jangan langsung beri jawaban akhir soal pendidikan. Jelaskan alur berpikirnya menggunakan LaTeX ($...$). "
            )
        else:
            mode_instruction = (
                "SISTEM BELAJAR AKTIF: \n"
                "SISTEM BELAJAR AKTIF: \n"
                "- Berikan penjelasan materi secara mendalam dan rumus lengkap. \n"
                "- Selesaikan soal secara step-by-step menggunakan LaTeX ($...$). \n"
                "- Fokus pada pemahaman konsep dasar agar user mengerti alurnya."
                "- Fokus pada penjelasan mendalam, rumus lengkap, dan konsep dasar. \n"
                "- Jelaskan alur berpikir (step-by-step) menggunakan LaTeX ($...$). \n"
                "- Berikan contoh soal hanya sebagai ilustrasi materi, bukan kuis."
                "- Jika DATA INTERNET tersedia, gunakan untuk menjawab info terkini secara akurat. "
                "- Jika DATA INTERNET kosong, gunakan kemampuan logika internalmu (Sangat kuat untuk pelajaran & umum). "
                "- FORMAT: Gunakan **Bold** untuk poin penting dan LaTeX ($...$) untuk rumus. "
                "- GAYA: Teman sebaya yang santai (aku-kamu), cerdas, dan suportif."
                "- PENEKANAN: Gunakan *Italic* untuk istilah asing atau penekanan nada bicara. "
                "- STRUKTUR: Gunakan Bullet Points atau Penomoran untuk daftar agar mudah dibaca. "
                "- ANALISIS DETAIL: Jangan hanya info populer. Berikan detail spesifik dari data internet yang ada. "
                "- METODE TUTOR: Jangan langsung beri jawaban akhir soal pendidikan. Jelaskan alur berpikirnya menggunakan LaTeX ($...$). "
            )

        system_prompt = (
            f"Nama kamu ERAI, Tutor Sebaya WUG untuk {user_name}. "
            f"Hari ini: {current_date}. \n"
            f"{mode_instruction} \n"
            f"DATA INTERNET: {search_info if search_info else 'Tidak perlu search'}. \n"
            "\nATURAN SISTEM: "
            "1. FORMAT: Gunakan **Bold** untuk poin penting, *Italic* untuk penekanan, dan Bullet Points agar rapi. "
            "2. GAYA: Teman sebaya yang santai (aku-kamu), cerdas, dan sangat suportif. "
            "3. ANALISIS DETAIL: Berikan detail spesifik jika ada data internet. "
            "4. METODE TUTOR: Selalu gunakan LaTeX ($...$) untuk semua rumus ilmiah."
        )

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
        
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.6 
        )
        
        return jsonify({"response": completion.choices[0].message.content})
    
    except Exception as e:
        return jsonify({"response": f"Kendala teknis: {str(e)}"}), 200

if __name__ == '__main__':
    app.run(debug=True)
