# AI MikroTik Telegram Bot (Multi-Router & Multi-Provider)

Asisten cerdas berbasis Telegram untuk memantau dan mengelola perangkat MikroTik (RouterOS) secara remote, aman, dan efisien dengan mekanisme **Human-in-the-Loop Approval Engine**.

---

## ✨ Fitur Utama

- 🤖 **Universal AI Integration (OpenAI-Compatible)**:
  - Kompatibel dengan semua AI provider berbasis OpenAI API standard: **OpenAI (GPT-4o, GPT-4o-mini)**, **DeepSeek**, **Groq**, **Ollama (Local/Self-hosted)**, **OpenRouter**, hingga **Google Gemini**.
- 🌐 **Multi-Router Management**:
  - Mendukung banyak router MikroTik sekaligus dalam satu bot.
  - Setiap pengguna Telegram memiliki sesi mandiri untuk memilih router aktif (`/use <router>` atau melalui menu interaktif `/routers`).
- 🛡️ **Human-in-the-Loop Approval Engine (Critical Security)**:
  - Setiap perintah yang bersifat mengubah konfigurasi jaringan (WRITE / Mutating) **TIDAK** langsung dieksekusi oleh AI.
  - Bot akan mengirimkan kartu pratinjau perintah lengkap dengan tombol **[ ✅ Setujui & Terapkan ]** dan **[ ❌ Tolak ]** dengan batas waktu (*TTL*).
- 📊 **Visual Grapher**:
  - Mengirimkan grafik visual langsung ke chat Telegram untuk pemantauan beban CPU, penggunaan RAM, dan grafik bandwidth RX/TX.
- 📱 **Fitur Monitoring Real-time**:
  - Status performa sistem (CPU, RAM, Uptime, Board Name).
  - Status interface jaringan (Running/Down/Disabled).
  - Monitor bandwidth trafik interface secara live (`/traffic ether1`).
  - Daftar perangkat terhubung (*DHCP Server Leases*).
  - Aturan *Firewall Filter Rules*.
  - Log sistem terkini router.
- 🔒 **Keamanan Berlapis**:
  - Pembatasan akses berbasis **Whitelist User ID Telegram**.
  - Enkripsi kredensial/password router menggunakan algoritma Fernet (AES-128-CBC).
  - Audit logging lengkap untuk pencatatan riwayat perintah dan kepatuhan sistem.

---

## 🛠️ Panduan Konfigurasi (.env)

Salin template konfigurasi:
```bash
cp .env.example .env
```

Edit file `.env` sesuai kebutuhan:

### 1. Telegram
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
ALLOWED_TELEGRAM_USER_IDS=123456789,987654321
```
> **Tip:** Dapatkan token dari [@BotFather](https://t.me/BotFather) dan cek ID Telegram Anda melalui [@userinfobot](https://t.me/userinfobot).

### 2. Pilihan Provider AI (OpenAI-Compatible)

#### Opsi A: OpenAI (Default)
```env
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=sk-...
AI_MODEL=gpt-4o-mini
```

#### Opsi B: Groq (Kecepatan Sangat Tinggi)
```env
AI_BASE_URL=https://api.groq.com/openai/v1
AI_API_KEY=gsk_...
AI_MODEL=llama-3.1-70b-versatile
```

#### Opsi C: DeepSeek
```env
AI_BASE_URL=https://api.deepseek.com/v1
AI_API_KEY=sk-...
AI_MODEL=deepseek-chat
```

#### Opsi D: Ollama (Lokal / Gratis / Tanpa Internet)
```env
AI_BASE_URL=http://localhost:11434/v1
AI_API_KEY=ollama
AI_MODEL=llama3
```

#### Opsi E: OpenRouter
```env
AI_BASE_URL=https://openrouter.ai/api/v1
AI_API_KEY=sk-or-...
AI_MODEL=openai/gpt-4o-mini
```

---

## 🔗 Integrasi dengan Hermes (REST API Mode)

Jika Anda menggunakan Hermes sebagai bot utama, aplikasi ini berjalan sebagai **Microservice / REST API Backend** di port `8000`. Dokumentasi interaktif Swagger UI tersedia di `http://localhost:8000/docs`.

### 1. Interaksi Percakapan AI (`POST /api/v1/chat`)
Kirim pertanyaan pengguna dari Hermes ke endpoint ini:
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Cek penggunaan CPU dan RAM router",
    "user_id": 123456,
    "send_to_telegram": true
  }'
```
**Respons JSON:**
```json
{
  "reply": "Beban CPU saat ini 5% dan penggunaan RAM 38%. Semua interface dalam kondisi normal.",
  "router_name": "kantor-pusat",
  "pending_approvals": []
}
```

### 2. Monitoring Langsung (Tool Endpoints untuk Hermes)
* **Status Beban & Resource:** `GET /api/v1/routers/{router_id}/monitoring/resource`
* **Bandwidth Trafik Real-time:** `GET /api/v1/routers/{router_id}/monitoring/traffic?interface=ether1`
* **Daftar Interface:** `GET /api/v1/routers/{router_id}/monitoring/interfaces`
* **DHCP Leases:** `GET /api/v1/routers/{router_id}/monitoring/dhcp-leases`
* **Firewall Filter:** `GET /api/v1/routers/{router_id}/monitoring/firewall-filters`
* **Log Router:** `GET /api/v1/routers/{router_id}/monitoring/logs`

### 3. Eksekusi Persetujuan (*Approval Engine*)
* **Lihat Permohonan Pending:** `GET /api/v1/approvals`
* **Setujui & Terapkan Perubahan:** `POST /api/v1/approvals/{approval_id}/approve`
* **Tolak Permohonan:** `POST /api/v1/approvals/{approval_id}/reject`


## 🚀 Menjalankan Aplikasi

### Metode 1: Menggunakan Docker & Docker Compose (Direkomendasikan)
```bash
docker compose up -d --build
```
Log bot dapat dipantau dengan:
```bash
docker compose logs -f mikrotik-bot
```

### Metode 2: Menjalankan Secara Lokal (Python 3.12+)
```bash
# Aktifkan virtual environment
source .venv/bin/activate  # Linux / macOS
.venv\Scripts\activate     # Windows

# Install dependensi
pip install -r requirements.txt

# Jalankan aplikasi
python -m app.main
```

---

## 📋 Daftar Perintah Bot Telegram

| Perintah | Deskripsi |
| :--- | :--- |
| `/start` | Menu pembuka dan status router aktif |
| `/help` | Panduan lengkap penggunaan bot |
| `/status` | Cek performa router (CPU, RAM, Uptime) + grafik visual |
| `/traffic <iface>` | Cek kecepatan download & upload real-time (+ grafik) |
| `/interfaces` | Daftar port / interface jaringan router |
| `/dhcp` | Daftar perangkat terhubung (DHCP Leases) |
| `/firewall` | Daftar aturan firewall filter yang aktif |
| `/logs` | Menampilkan log router terkini |
| `/audit` | Riwayat persetujuan & eksekusi perintah |
| `/routers` | Daftar semua router & tombol ganti router aktif |
| `/use <nama/id>` | Mengganti router aktif yang dikelola |
| `/addrouter <nama> <host> <port> <user> <pass>` | Mendaftarkan router MikroTik baru |
| `/delrouter <id>` | Menghapus router dari daftar |

---

## 💬 Contoh Penggunaan Bahasa Alami (AI)

Anda dapat langsung berinteraksi dalam bahasa santai:
- *"Berapa beban CPU router saat ini?"*
- *"Coba periksa apakah ada interface yang mati atau down."*
- *"Tolong blokir IP 192.168.88.50 dari akses keluar."* ➡️ *(Akan otomatis memunculkan tombol konfirmasi persetujuan)*
- *"Berapa banyak perangkat yang sedang terhubung ke DHCP?"*
- *"Cek log apakah ada peringatan atau login gagal."*
