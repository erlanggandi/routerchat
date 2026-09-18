# PRD: AI Mikrotik Telegram Bot
> Dibuat dengan ProdMap.

---

## 1. Executive Summary
AI Mikrotik Telegram Bot adalah solusi asisten cerdas yang memudahkan administrator jaringan dalam memonitor dan mengelola perangkat Mikrotik (RouterOS) secara remote melalui Telegram. Aplikasi ini menyediakan antarmuka percakapan untuk melihat status *real-time* dan melakukan konfigurasi dengan mekanisme *Human-in-the-loop* (persetujuan manual) untuk keamanan.

## 2. Problem Statement
Manajemen Mikrotik saat ini memerlukan akses manual ke aplikasi atau CLI, yang memakan waktu dan menyulitkan analisa performa jaringan secara cepat. Administrator seringkali membutuhkan solusi yang responsif saat berada di luar kantor tanpa harus membuka laptop atau koneksi VPN yang rumit.

## 3. Target Pengguna
*   Network Administrator
*   IT Support
*   Freelance Mikrotik Consultant

## 4. Goals & Indikator Sukses
*   **Goals:** Otomatisasi monitoring dan mempermudah konfigurasi router.
*   **Indikator Sukses:**
    *   Waktu respons (MTTR) untuk pengecekan status router turun drastis.
    *   100% konfigurasi AI tervalidasi melalui tombol persetujuan pengguna.
    *   Uptime bot mencapai 99.9%.

## 5. Fitur MVP
| Fitur | Deskripsi | Prioritas |
| :--- | :--- | :--- |
| **Telegram Integration** | Antarmuka chat untuk komunikasi pengguna ke router. | High |
| **Router Status Fetcher** | Mengambil data CPU, RAM, dan traffic interface. | High |
| **AI Config Generator** | Mengusulkan perubahan konfigurasi via AI. | High |
| **Approval Engine** | Tombol Approve/Reject untuk setiap eksekusi konfigurasi. | Critical |
| **Visual Grapher** | Menampilkan grafik statistik router sederhana di chat. | Medium |

## 6. Scope
*   **In Scope:** Bot Telegram, koneksi API Mikrotik, sistem persetujuan konfigurasi, visualisasi grafik dasar.
*   **Out of Scope:** Sistem pelaporan formal (PDF/Email), integrasi tiket pihak ketiga, fitur AI training lanjut.

## 7. User Stories Utama
1.  "Sebagai admin, saya ingin menanyakan status penggunaan CPU router melalui chat Telegram agar saya tahu jika terjadi overload."
2.  "Sebagai admin, saya ingin meninjau konfigurasi yang disarankan AI sebelum menekan 'Approve' agar tidak terjadi kesalahan fatal."
3.  "Sebagai admin, saya ingin melihat grafik trafik interface terbaru sebagai ringkasan visual."

## 8. Persyaratan Non-Fungsional
*   **Security:** Enkripsi API Key router dan token Telegram.
*   **Deployment:** Containerized menggunakan Docker.
*   **Usability:** Respons bot harus cepat (< 3 detik untuk query data).
*   **Reliability:** Bot harus melakukan *retry* otomatis jika koneksi ke router terputus.

## 9. Tech Stack
| Komponen | Teknologi |
| :--- | :--- |
| Backend | Python (FastAPI) |
| AI Integration | LangChain + OpenAI API |
| Mikrotik Library | `librouteros` |
| Containerization | Docker & Docker Compose |
| Database | SQLite (untuk log aksi/persetujuan) |

## 10. Estimasi Timeline
| Fase | Durasi |
| :--- | :--- |
| Setup Lingkungan & Koneksi Router | 1 Minggu |
| Pengembangan Fitur Monitoring & Grafik | 2 Minggu |
| Integrasi AI & Approval Workflow | 3 Minggu |
| Pengujian & Debugging | 2 Minggu |

## 11. Risiko & Asumsi
| Risiko | Mitigasi |
| :--- | :--- |
| AI memberikan konfigurasi salah | Wajib menggunakan mode persetujuan manual (Human-in-the-loop). |
| Koneksi ke Router terputus | Implementasi *error handling* dan notifikasi di chat. |
| Keamanan bot disalahgunakan | Batasi akses hanya untuk User ID Telegram yang terdaftar. |

## 12. Open Questions
1.  Apakah ingin menggunakan model AI spesifik (misal: GPT-4o, Claude 3.5, atau model lokal Llama)?
2.  Berapa banyak router yang akan di-manage dalam satu waktu?
3.  Apakah diperlukan sistem log historis yang tersimpan dalam jangka waktu lama?