@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_input = data.get("message", "")
        # Kita patenkan nama panggilannya di sini
        user_name = "Kakak" 
        user_mode = data.get("mode", "belajar")
        history = data.get("history", [])

        # ... (Logika Smart Search tetap sama) ...

        # --- LOGIKA BEHAVIOR MODE (REVISI BERSIH) ---
        if user_mode == "latihan":
            mode_instruction = (
                "SISTEM LATIHAN AKTIF (AUTO-QUIZ MODE): \n"
                "- Jika user memberikan soal, JANGAN berikan jawaban langsung. \n"
                "- Ubah soal menjadi kuis interaktif dengan 4 pilihan jawaban (A, B, C, D). \n"
                "- Pastikan salah satu pilihan adalah jawaban yang benar. \n"
                "- Berikan clue kecil, jangan langsung solusi. \n"
                "- Jika jawaban user benar, beri selamat dan jelaskan penyelesaiannya. \n"
                "- Gunakan format $\\ce{...}$ untuk kimia dan LaTeX ($...$) untuk matematika."
            )
        else:
            mode_instruction = (
                "SISTEM BELAJAR AKTIF: \n"
                "- Berikan penjelasan mendalam, rumus lengkap, dan konsep dasar. \n"
                "- Selesaikan soal secara step-by-step menggunakan LaTeX ($...$). \n"
                "- Gunakan format $\\ce{...}$ untuk kimia agar tidak error."
            )

        system_prompt = (
            f"Nama kamu ERAI, Tutor Sebaya WUG untuk {user_name}. "
            f"Panggil user dengan sebutan '{user_name}'. "
            f"Hari ini: {current_date}. \n"
            f"{mode_instruction} \n"
            f"DATA INTERNET: {search_info if search_info else 'Tidak perlu search'}. \n"
            "\nATURAN SISTEM: "
            "1. FORMAT: **Bold** untuk poin penting, *Italic* untuk penekanan. "
            "2. GAYA: Teman sebaya yang santai (aku-kamu), cerdas, dan suportif. "
            "3. METODE TUTOR: Selalu gunakan LaTeX ($...$) untuk rumus ilmiah."
        )

        # ... (Proses Groq tetap sama) ...
