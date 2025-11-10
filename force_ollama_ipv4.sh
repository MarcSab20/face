#!/bin/bash

echo "🔍 Diagnostic de connexion Ollama..."

# Trouver l'adresse IP de la gateway Docker
GATEWAY_IP=$(docker network inspect bridge | grep Gateway | awk '{print $2}' | tr -d '",')
echo "Gateway Docker: $GATEWAY_IP"

# Tester la connexion Ollama sur différents ports
for PORT in 11434 11435; do
    echo "Test connexion http://${GATEWAY_IP}:${PORT}..."
    if curl -s "http://${GATEWAY_IP}:${PORT}/api/tags" > /dev/null 2>&1; then
        echo "✅ Ollama accessible sur http://${GATEWAY_IP}:${PORT}"
        echo "OLLAMA_HOST=http://${GATEWAY_IP}:${PORT}" > .env.ollama
        exit 0
    fi
done

# Tester localhost
for PORT in 11434 11435; do
    echo "Test connexion http://localhost:${PORT}..."
    if curl -s "http://localhost:${PORT}/api/tags" > /dev/null 2>&1; then
        echo "✅ Ollama accessible sur http://localhost:${PORT}"
        echo "OLLAMA_HOST=http://host.docker.internal:${PORT}" > .env.ollama
        exit 0
    fi
done

echo "❌ Ollama non accessible. Vérifiez qu'Ollama est démarré."
echo "Commande: ollama serve"
exit 1