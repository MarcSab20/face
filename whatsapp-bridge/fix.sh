#!/bin/bash

# Script de Résolution Complète - WhatsApp Bridge
# Résout le problème du module 'qrcode' manquant

set -e  # Arrêter en cas d'erreur

echo "======================================"
echo "🔧 RÉSOLUTION WHATSAPP BRIDGE"
echo "Module 'qrcode' manquant"
echo "======================================"
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Vérifier qu'on est dans le bon dossier
if [ ! -d "whatsapp-bridge" ]; then
    echo -e "${RED}❌ Erreur: Dossier whatsapp-bridge non trouvé${NC}"
    echo "   Exécutez ce script depuis la racine du projet"
    exit 1
fi

# Étape 1: Arrêter le conteneur
echo -e "${YELLOW}📦 Étape 1/6: Arrêt du conteneur...${NC}"
docker-compose stop whatsapp-bridge 2>/dev/null || true
sleep 2
echo -e "${GREEN}✅ Conteneur arrêté${NC}"
echo ""

# Étape 2: Sauvegarder les anciens fichiers
echo -e "${YELLOW}💾 Étape 2/6: Sauvegarde des fichiers existants...${NC}"
timestamp=$(date +%Y%m%d_%H%M%S)

if [ -f "whatsapp-bridge/whatsapp-bridge.js" ]; then
    cp whatsapp-bridge/whatsapp-bridge.js "whatsapp-bridge/whatsapp-bridge.js.bak_${timestamp}"
    echo -e "${GREEN}✅ whatsapp-bridge.js sauvegardé${NC}"
fi

if [ -f "whatsapp-bridge/package.json" ]; then
    cp whatsapp-bridge/package.json "whatsapp-bridge/package.json.bak_${timestamp}"
    echo -e "${GREEN}✅ package.json sauvegardé${NC}"
fi
echo ""

# Étape 3: Nettoyer l'authentification
echo -e "${YELLOW}🗑️  Étape 3/6: Nettoyage de l'authentification corrompue...${NC}"
if [ -d "whatsapp-bridge/auth_info" ]; then
    rm -rf whatsapp-bridge/auth_info
    echo -e "${GREEN}✅ Dossier auth_info supprimé${NC}"
else
    echo -e "${BLUE}ℹ️  Aucun dossier auth_info à nettoyer${NC}"
fi
echo ""

# Étape 4: Copier les nouveaux fichiers
echo -e "${YELLOW}📝 Étape 4/6: Installation des fichiers corrigés...${NC}"

# Vérifier que les fichiers corrigés existent
if [ ! -f "whatsapp-bridge-fixed.js" ]; then
    echo -e "${RED}❌ Fichier whatsapp-bridge-fixed.js non trouvé${NC}"
    echo "   Téléchargez-le depuis Claude"
    exit 1
fi

if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ Fichier package.json non trouvé${NC}"
    echo "   Téléchargez-le depuis Claude"
    exit 1
fi

# Copier les fichiers
cp whatsapp-bridge-fixed.js whatsapp-bridge/whatsapp-bridge.js
echo -e "${GREEN}✅ whatsapp-bridge.js mis à jour${NC}"

cp package.json whatsapp-bridge/package.json
echo -e "${GREEN}✅ package.json mis à jour${NC}"
echo ""

# Étape 5: Supprimer les anciens conteneurs et images
echo -e "${YELLOW}🧹 Étape 5/6: Nettoyage Docker...${NC}"
docker-compose rm -f whatsapp-bridge 2>/dev/null || true
echo -e "${GREEN}✅ Anciens conteneurs supprimés${NC}"
echo ""

# Étape 6: Rebuild et redémarrer
echo -e "${YELLOW}🔨 Étape 6/6: Reconstruction et démarrage...${NC}"
echo "   (Cela peut prendre 30-60 secondes)"
docker-compose build --no-cache whatsapp-bridge
echo -e "${GREEN}✅ Image reconstruite${NC}"

docker-compose up -d whatsapp-bridge
sleep 5
echo -e "${GREEN}✅ Conteneur démarré${NC}"
echo ""

# Vérification
echo "======================================"
echo -e "${GREEN}🎉 INSTALLATION TERMINÉE${NC}"
echo "======================================"
echo ""
echo -e "${BLUE}📊 Vérification de l'état...${NC}"
echo ""

# Attendre que le service démarre
sleep 3

# Afficher les logs
echo -e "${YELLOW}📋 Derniers logs (Ctrl+C pour quitter):${NC}"
echo ""
docker-compose logs --tail=50 -f whatsapp-bridge