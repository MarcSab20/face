#!/bin/bash

# Script de Correction Automatique du WhatsApp Bridge
# Usage: bash fix-whatsapp-bridge.sh

set -e  # Arrêter en cas d'erreur

echo "======================================"
echo "🔧 Correction du WhatsApp Bridge v2.0"
echo "======================================"
echo ""

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
info() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Vérifier que docker-compose.yml existe
echo "🔍 Vérification de l'environnement..."
if [ ! -f "docker-compose.yml" ]; then
    error "Fichier docker-compose.yml non trouvé!"
    echo "   Assurez-vous d'exécuter ce script depuis la racine du projet Brand Monitor"
    exit 1
fi
info "docker-compose.yml trouvé"

# 2. Vérifier que le dossier whatsapp-bridge existe
if [ ! -d "whatsapp-bridge" ]; then
    error "Dossier whatsapp-bridge/ non trouvé!"
    echo "   Structure attendue: ./whatsapp-bridge/whatsapp-bridge.js"
    exit 1
fi
info "Dossier whatsapp-bridge/ trouvé"

# 3. Arrêter le service WhatsApp Bridge
echo ""
echo "🛑 Arrêt du service WhatsApp Bridge..."
docker-compose stop whatsapp-bridge 2>/dev/null || {
    warning "Service whatsapp-bridge non démarré ou non trouvé"
}
info "Service arrêté"

# 4. Sauvegarder l'ancien fichier
echo ""
echo "💾 Sauvegarde de l'ancien fichier..."
if [ -f "whatsapp-bridge/whatsapp-bridge.js" ]; then
    cp whatsapp-bridge/whatsapp-bridge.js whatsapp-bridge/whatsapp-bridge.js.backup-$(date +%Y%m%d-%H%M%S)
    info "Backup créé: whatsapp-bridge.js.backup-$(date +%Y%m%d-%H%M%S)"
else
    warning "Fichier whatsapp-bridge.js non trouvé, création d'un nouveau"
fi

# 5. Créer le nouveau fichier whatsapp-bridge.js
echo ""
echo "📝 Création du nouveau fichier whatsapp-bridge.js..."

cat > whatsapp-bridge/whatsapp-bridge.js << 'EOF'
/**
 * WhatsApp Bridge - Version Corrigée v2.0
 * Gestion moderne du QR code et reconnexion intelligente
 */

const { default: makeWASocket, DisconnectReason, useMultiFileAuthState, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const express = require('express');
const QRCode = require('qrcode');
const pino = require('pino');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 3500;
const AUTH_FOLDER = './auth_info';

// État global
let sock = null;
let qrCodeData = null;
let connectionState = 'disconnected';
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 5000; // 5 secondes

// Logger silencieux
const logger = pino({ level: 'error' });

/**
 * Fonction pour initialiser la connexion WhatsApp
 */
async function connectWhatsApp() {
    try {
        console.log('🔌 Initialisation de la connexion WhatsApp...');
        
        // Charger l'état d'authentification
        const { state, saveCreds } = await useMultiFileAuthState(AUTH_FOLDER);
        
        // Obtenir la dernière version de Baileys
        const { version, isLatest } = await fetchLatestBaileysVersion();
        console.log(`📱 Version Baileys: ${version.join('.')}, Latest: ${isLatest}`);
        
        // Créer le socket WhatsApp (SANS printQRInTerminal)
        sock = makeWASocket({
            version,
            logger,
            auth: state,
            browser: ['Brand Monitor', 'Chrome', '121.0.0'],
            connectTimeoutMs: 60000,
            defaultQueryTimeoutMs: 60000,
            keepAliveIntervalMs: 30000
        });
        
        // Sauvegarder les credentials à chaque mise à jour
        sock.ev.on('creds.update', saveCreds);
        
        // Gestion des mises à jour de connexion
        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;
            
            // Nouveau QR code disponible
            if (qr) {
                console.log('📱 Nouveau QR code généré');
                qrCodeData = qr;
                connectionState = 'qr_ready';
                
                // Générer le QR code en ASCII pour le terminal
                try {
                    const qrTerminal = await QRCode.toString(qr, { type: 'terminal', small: true });
                    console.log('\n🔲 Scannez ce QR code avec WhatsApp:\n');
                    console.log(qrTerminal);
                    console.log('\n💡 Ou accédez à http://localhost:' + PORT + '/qr pour voir le QR en image\n');
                } catch (err) {
                    console.error('❌ Erreur génération QR terminal:', err.message);
                }
                
                reconnectAttempts = 0;
            }
            
            // Changement d'état de connexion
            if (connection === 'close') {
                const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
                const reason = lastDisconnect?.error?.output?.statusCode;
                
                console.log('❌ Connexion fermée. Raison:', reason);
                console.log('   Reconnexion nécessaire:', shouldReconnect);
                
                connectionState = 'disconnected';
                qrCodeData = null;
                
                if (shouldReconnect) {
                    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                        reconnectAttempts++;
                        console.log(`🔄 Tentative ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS} dans ${RECONNECT_DELAY/1000}s...`);
                        setTimeout(connectWhatsApp, RECONNECT_DELAY);
                    } else {
                        console.error('❌ Maximum de tentatives atteint');
                        console.error('💡 Solutions:');
                        console.error('   1. Supprimez auth_info/ et rescannez: rm -rf whatsapp-bridge/auth_info/*');
                        console.error('   2. Vérifiez votre connexion internet');
                        console.error('   3. Redémarrez: docker-compose restart whatsapp-bridge');
                        
                        setTimeout(() => {
                            console.log('🔄 Reset des tentatives...');
                            reconnectAttempts = 0;
                            connectWhatsApp();
                        }, 30000);
                    }
                } else {
                    console.log('🚪 Déconnexion définitive (logged out)');
                    console.log('💡 Supprimez auth_info/ et relancez');
                }
            }
            
            if (connection === 'open') {
                console.log('✅ Connexion WhatsApp réussie!');
                connectionState = 'connected';
                qrCodeData = null;
                reconnectAttempts = 0;
                
                const userInfo = sock.user;
                console.log('👤 Connecté:', userInfo.name || userInfo.id);
            }
            
            if (connection === 'connecting') {
                console.log('🔄 Connexion en cours...');
                connectionState = 'connecting';
            }
        });
        
        sock.ev.on('messages.upsert', async ({ messages, type }) => {
            if (type === 'notify') {
                for (const msg of messages) {
                    if (!msg.key.fromMe) {
                        console.log('📩 Message de:', msg.key.remoteJid);
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('❌ Erreur connexion:', error);
        connectionState = 'error';
        
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            console.log(`🔄 Nouvelle tentative dans ${RECONNECT_DELAY/1000}s...`);
            setTimeout(connectWhatsApp, RECONNECT_DELAY);
        }
    }
}

// ==================
// ENDPOINTS API
// ==================

app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        connection_state: connectionState,
        reconnect_attempts: reconnectAttempts,
        qr_available: qrCodeData !== null,
        timestamp: new Date().toISOString()
    });
});

app.get('/qr', async (req, res) => {
    const format = req.query.format || 'image';
    
    if (!qrCodeData) {
        return res.status(404).json({
            error: 'QR code non disponible',
            connection_state: connectionState,
            message: connectionState === 'connected' 
                ? 'Déjà connecté' 
                : 'En attente de génération...'
        });
    }
    
    try {
        if (format === 'image') {
            const qrImage = await QRCode.toBuffer(qrCodeData, { 
                type: 'png',
                width: 400,
                margin: 2
            });
            res.type('image/png').send(qrImage);
        } else if (format === 'text') {
            const qrText = await QRCode.toString(qrCodeData, { 
                type: 'terminal',
                small: true
            });
            res.type('text/plain').send(qrText);
        } else {
            res.json({
                qr: qrCodeData,
                connection_state: connectionState,
                expires_in: '60s'
            });
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/groups', async (req, res) => {
    if (connectionState !== 'connected' || !sock) {
        return res.status(503).json({ 
            error: 'WhatsApp non connecté',
            connection_state: connectionState
        });
    }
    
    try {
        const groups = await sock.groupFetchAllParticipating();
        const groupsList = Object.values(groups).map(group => ({
            id: group.id,
            name: group.subject,
            participants_count: group.participants.length,
            creation: group.creation,
            description: group.desc
        }));
        
        res.json({
            count: groupsList.length,
            groups: groupsList
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/reconnect', (req, res) => {
    console.log('🔄 Reconnexion forcée...');
    reconnectAttempts = 0;
    
    if (sock) {
        sock.end();
    }
    
    setTimeout(connectWhatsApp, 1000);
    
    res.json({ 
        success: true, 
        message: 'Reconnexion initiée'
    });
});

app.delete('/session', async (req, res) => {
    console.log('🗑️ Suppression session...');
    
    if (sock) {
        await sock.logout();
        sock.end();
    }
    
    const fs = require('fs').promises;
    try {
        await fs.rm(AUTH_FOLDER, { recursive: true, force: true });
        console.log('✅ Session supprimée');
    } catch (err) {
        console.error('⚠️ Erreur:', err.message);
    }
    
    const fsSync = require('fs');
    if (!fsSync.existsSync(AUTH_FOLDER)) {
        fsSync.mkdirSync(AUTH_FOLDER, { recursive: true });
    }
    
    setTimeout(connectWhatsApp, 1000);
    
    res.json({ 
        success: true, 
        message: 'Session supprimée. Nouveau QR en cours...'
    });
});

// ==================
// DÉMARRAGE
// ==================

app.listen(PORT, () => {
    console.log('====================================');
    console.log('📱 WhatsApp Bridge v2.0');
    console.log('====================================');
    console.log(`🌐 API: http://localhost:${PORT}`);
    console.log(`📄 Endpoints:`);
    console.log(`   GET  /health     - État`);
    console.log(`   GET  /qr         - QR code`);
    console.log(`   GET  /groups     - Groupes`);
    console.log(`   POST /reconnect  - Reconnecter`);
    console.log(`   DELETE /session  - Reset`);
    console.log('====================================\n');
    
    connectWhatsApp();
});

process.on('SIGINT', async () => {
    console.log('\n⚠️ Arrêt...');
    if (sock) {
        await sock.end();
    }
    process.exit(0);
});

process.on('uncaughtException', (error) => {
    console.error('❌ Exception:', error);
});

process.on('unhandledRejection', (error) => {
    console.error('❌ Promesse rejetée:', error);
});
EOF

info "Nouveau fichier créé"

# 6. Supprimer l'ancienne session
echo ""
echo "🗑️  Suppression de l'ancienne session..."
rm -rf whatsapp-bridge/auth_info/*
mkdir -p whatsapp-bridge/auth_info/
info "Session réinitialisée"

# 7. Mettre à jour package.json si nécessaire
echo ""
echo "📦 Vérification de package.json..."
if [ -f "whatsapp-bridge/package.json" ]; then
    info "package.json existe déjà"
else
    warning "package.json non trouvé, création..."
    cat > whatsapp-bridge/package.json << 'EOF'
{
  "name": "whatsapp-bridge",
  "version": "2.0.0",
  "description": "WhatsApp Bridge pour Brand Monitor",
  "main": "whatsapp-bridge.js",
  "dependencies": {
    "@whiskeysockets/baileys": "^6.7.8",
    "express": "^4.18.2",
    "qrcode": "^1.5.3",
    "pino": "^8.16.1",
    "cors": "^2.8.5"
  }
}
EOF
    info "package.json créé"
fi

# 8. Reconstruire l'image Docker
echo ""
echo "🏗️  Reconstruction de l'image Docker..."
docker-compose build whatsapp-bridge || {
    error "Échec de la construction Docker"
    echo "   Essayez manuellement: docker-compose build whatsapp-bridge"
    exit 1
}
info "Image Docker reconstruite"

# 9. Redémarrer le service
echo ""
echo "🚀 Démarrage du service WhatsApp Bridge..."
docker-compose up -d whatsapp-bridge || {
    error "Échec du démarrage"
    echo "   Essayez manuellement: docker-compose up -d whatsapp-bridge"
    exit 1
}
info "Service démarré"

# 10. Afficher les logs
echo ""
echo "======================================"
echo "✅ Correction terminée avec succès!"
echo "======================================"
echo ""
echo "📋 Prochaines étapes:"
echo ""
echo "1. Voir les logs en temps réel:"
echo "   docker logs -f brandmonitor_whatsapp-bridge"
echo ""
echo "2. Le QR code devrait s'afficher dans environ 10 secondes"
echo ""
echo "3. OU accédez au QR en image:"
echo "   http://localhost:3500/qr"
echo ""
echo "4. Scanner le QR avec WhatsApp:"
echo "   WhatsApp > Paramètres > Appareils connectés > Connecter un appareil"
echo ""
echo "5. Vérifier l'état:"
echo "   curl http://localhost:3500/health | jq"
echo ""
echo "======================================"
echo ""
echo "🔍 Affichage des derniers logs (15 secondes)..."
sleep 15
docker logs --tail 50 brandmonitor_whatsapp-bridge

echo ""
echo "✅ Script terminé!"
echo "   Si le QR code n'apparaît pas, attendez encore 10-20 secondes"
echo "   ou consultez les logs: docker logs -f brandmonitor_whatsapp-bridge"
EOF

chmod +x fix-whatsapp-bridge.sh
info "Script créé et rendu exécutable"