#!/usr/bin/env bash
# ==============================================================================
# Script Instalasi MikroTik Service & Skill untuk Hermes Agent di Ubuntu
# ==============================================================================
set -e

if [ ! -f .env ]; then
    echo "⚙️ [0/3] Menyiapkan .env dari .env.example..."
    cp .env.example .env
fi

echo "🚀 [1/3] Menyiapkan Skill MikroTik untuk Hermes Agent..."
HERMES_SKILLS_DIR="$HOME/.hermes/skills/mikrotik"
mkdir -p "$HERMES_SKILLS_DIR"
cp skills/mikrotik/SKILL.md "$HERMES_SKILLS_DIR/SKILL.md"
echo "✅ Skill berhasil disalin ke: $HERMES_SKILLS_DIR/SKILL.md"

# Jika dijalankan sebagai root dan ada user 'app' (Hermes berjalan di user app)
if [ -d "/home/app/.hermes" ] || id "app" &>/dev/null; then
    mkdir -p "/home/app/.hermes/skills/mikrotik"
    cp skills/mikrotik/SKILL.md "/home/app/.hermes/skills/mikrotik/SKILL.md"
    chown -R app:app "/home/app/.hermes/skills/mikrotik" 2>/dev/null || true
    echo "✅ Skill juga disalin untuk user 'app' ke: /home/app/.hermes/skills/mikrotik/SKILL.md"
fi

echo "🐳 [2/3] Menjalankan MikroTik Backend Service di port 3010..."
docker compose up -d --build

echo "🔍 [3/3] Memeriksa status service (menunggu hingga 15 detik)..."
SUCCESS=0
for i in $(seq 1 15); do
    if curl -s http://localhost:3010/health | grep -q "ok"; then
        SUCCESS=1
        break
    fi
    sleep 1
done

if [ $SUCCESS -eq 1 ]; then
    echo "✅ MikroTik Service BERHASIL aktif di http://localhost:3010"
    echo "🎉 Hermes sekarang sudah memiliki skill MikroTik!"
    echo "💡 Anda bisa langsung chat ke bot Hermes di Telegram:"
    echo "   - 'Cek kondisi router MikroTik sekarang'"
    echo "   - 'Berapa trafik ether1?'"
    echo "   - 'Siapa saja yang terhubung di DHCP?'"
else
    echo "⚠️ Service belum merespons. Silakan cek status dan log dengan:"
    echo "   docker compose ps"
    echo "   docker compose logs -n 30"
fi
