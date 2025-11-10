#!/bin/bash
# Solution de contournement : Proxy IPv4 -> IPv6 pour Ollama
# À utiliser si Ollama refuse d'écouter en IPv4

echo "🔀 Installation du proxy IPv4 -> IPv6 pour Ollama"
echo "=================================================="

# 1. Installer socat si nécessaire
if ! command -v socat &> /dev/null; then
    echo "📦 Installation de socat..."
    sudo apt-get update -qq
    sudo apt-get install -y socat
fi

# 2. Créer un service systemd pour le proxy
echo "📝 Création du service proxy..."

sudo tee /etc/systemd/system/ollama-ipv4-proxy.service > /dev/null <<'EOF'
[Unit]
Description=Ollama IPv4 Proxy (IPv4 -> IPv6)
After=ollama.service
Requires=ollama.service

[Service]
Type=simple
ExecStart=/usr/bin/socat TCP4-LISTEN:11435,fork,reuseaddr TCP6:[::1]:11434
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 3. Activer et démarrer le proxy
echo "▶️  Démarrage du proxy..."
sudo systemctl daemon-reload
sudo systemctl enable ollama-ipv4-proxy
sudo systemctl start ollama-ipv4-proxy

# 4. Vérifier
sleep 2
echo ""
echo "🔍 Vérification..."
sudo netstat -tulpn | grep -E '11434|11435'
echo ""

# 5. Test
echo "🧪 Test du proxy..."
if curl -s http://127.0.0.1:11435/api/tags > /dev/null 2>&1; then
    echo "✅ Proxy fonctionnel sur le port 11435 (IPv4)"
    echo ""
    echo "📋 Configuration Docker :"
    echo "  environment:"
    echo "    - OLLAMA_HOST=http://172.17.0.1:11435"
    echo ""
else
    echo "❌ Proxy non fonctionnel"
fi

echo "=================================================="
echo "PORTS DISPONIBLES :"
echo "  - 11434 : Ollama IPv6 (original)"
echo "  - 11435 : Proxy IPv4 (pour Docker)"
echo "=================================================="