#!/usr/bin/env bash
# ==============================================================================
# Script Instalasi MikroTik Service & Skill untuk Hermes Agent di Ubuntu
# ==============================================================================
set -e

echo "🚀 [1/3] Menyiapkan Skill MikroTik untuk Hermes Agent..."
HERMES_SKILLS_DIR="$HOME/.hermes/skills/mikrotik"
mkdir -p "$HERMES_SKILLS_DIR"
cp skills/mikrotik/SKILL.md "$HERMES_SKILLS_DIR/SKILL.md"
echo "✅ Skill berhasil disalin ke: $HERMES_SKILLS_DIR/SKILL.md"

echo "🐳 [2/3] Menjalankan MikroTik Backend Service di port 3010..."
docker compose up -d --build

echo "🔍 [3/3] Memeriksa status service..."
sleep 2
if curl -s http://localhost:3010/health | grep -q "ok"; then
    echo "✅ MikroTik Service BERHASIL aktif di http://localhost:3010"
    echo "🎉 Hermes sekarang sudah memiliki skill MikroTik!"
    echo "💡 Anda bisa langsung chat ke bot Hermes di Telegram:"
    echo "   - 'Cek kondisi router MikroTik sekarang'"
    echo "   - 'Berapa trafik ether1?'"
    echo "   - 'Siapa saja yang terhubung di DHCP?'"
else
    echo "⚠️ Service belum merespons, silakan periksa log dengan: docker compose logs -f"
fi
