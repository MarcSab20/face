/**
 * WhatsApp Bridge - Version Corrigée et Optimisée
 * Résout les problèmes de reconnexion en boucle et gestion moderne du QR code
 */

const { default: makeWASocket, DisconnectReason, useMultiFileAuthState, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const express = require('express');
const QRCode = require('qrcode');
const pino = require('pino');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

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
let isConnecting = false; // Prévenir les reconnexions multiples
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 5000; // 5 secondes

// Logger silencieux
const logger = pino({ level: 'silent' }); // Complètement silencieux

/**
 * Vérifier et créer le dossier d'authentification
 */
function ensureAuthFolder() {
    if (!fs.existsSync(AUTH_FOLDER)) {
        fs.mkdirSync(AUTH_FOLDER, { recursive: true });
        console.log('✅ Dossier d\'authentification créé:', AUTH_FOLDER);
    }
}

/**
 * Fonction pour initialiser la connexion WhatsApp
 */
async function connectWhatsApp() {
    // Éviter les connexions multiples simultanées
    if (isConnecting) {
        console.log('⚠️ Connexion déjà en cours, attente...');
        return;
    }
    
    isConnecting = true;
    
    try {
        console.log('====================================');
        console.log('🔌 Initialisation WhatsApp');
        console.log('====================================');
        
        // S'assurer que le dossier d'authentification existe
        ensureAuthFolder();
        
        // Charger l'état d'authentification
        console.log('📂 Chargement de l\'état d\'authentification...');
        const { state, saveCreds } = await useMultiFileAuthState(AUTH_FOLDER);
        
        // Obtenir la dernière version de Baileys
        const { version, isLatest } = await fetchLatestBaileysVersion();
        console.log(`📱 Version Baileys: ${version.join('.')}`);
        console.log(`✅ Dernière version: ${isLatest ? 'Oui' : 'Non'}`);
        
        // Créer le socket WhatsApp avec configuration optimale
        console.log('🔧 Création du socket WhatsApp...');
        sock = makeWASocket({
            version,
            logger,
            auth: state,
            browser: ['Brand Monitor', 'Chrome', '121.0.0'],
            connectTimeoutMs: 60000,
            defaultQueryTimeoutMs: 60000,
            keepAliveIntervalMs: 30000,
            getMessage: async () => undefined,
            // Pas de printQRInTerminal (déprécié)
            generateHighQualityLinkPreview: false,
            syncFullHistory: false,
            markOnlineOnConnect: true
        });
        
        console.log('✅ Socket créé avec succès');
        
        // Sauvegarder les credentials à chaque mise à jour
        sock.ev.on('creds.update', saveCreds);
        
        // Gestion des mises à jour de connexion
        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;
            
            // Nouveau QR code disponible
            if (qr) {
                console.log('\n====================================');
                console.log('📱 QR CODE GÉNÉRÉ');
                console.log('====================================');
                qrCodeData = qr;
                connectionState = 'qr_ready';
                
                // Afficher le QR dans le terminal
                try {
                    const qrTerminal = await QRCode.toString(qr, { 
                        type: 'terminal', 
                        small: true 
                    });
                    console.log('\n🔲 Scannez ce QR code avec WhatsApp:\n');
                    console.log(qrTerminal);
                    console.log('\n💡 Ou accédez à: http://localhost:' + PORT + '/qr\n');
                    console.log('====================================\n');
                } catch (err) {
                    console.error('❌ Erreur génération QR terminal:', err.message);
                }
                
                reconnectAttempts = 0; // Reset des tentatives
                isConnecting = false;
            }
            
            // Connexion fermée
            if (connection === 'close') {
                isConnecting = false;
                
                const statusCode = lastDisconnect?.error?.output?.statusCode;
                const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
                
                console.log('\n====================================');
                console.log('❌ CONNEXION FERMÉE');
                console.log('====================================');
                console.log('Raison:', getDisconnectReason(statusCode));
                console.log('Code:', statusCode);
                console.log('Reconnexion nécessaire:', shouldReconnect);
                
                connectionState = 'disconnected';
                qrCodeData = null;
                
                if (shouldReconnect) {
                    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                        reconnectAttempts++;
                        const delay = RECONNECT_DELAY * reconnectAttempts; // Délai croissant
                        console.log(`🔄 Tentative ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS} dans ${delay/1000}s...`);
                        console.log('====================================\n');
                        
                        setTimeout(() => {
                            connectWhatsApp();
                        }, delay);
                    } else {
                        console.error('❌ ÉCHEC APRÈS PLUSIEURS TENTATIVES');
                        console.error('====================================');
                        console.error('💡 Solutions:');
                        console.error('   1. Supprimer le dossier auth_info/:');
                        console.error('      rm -rf whatsapp-bridge/auth_info/');
                        console.error('   2. Redémarrer le service:');
                        console.error('      docker-compose restart whatsapp-bridge');
                        console.error('   3. Vérifier votre connexion internet');
                        console.error('====================================\n');
                        
                        // Réinitialisation automatique après 60 secondes
                        setTimeout(() => {
                            console.log('🔄 Réinitialisation automatique...\n');
                            reconnectAttempts = 0;
                            connectWhatsApp();
                        }, 60000);
                    }
                } else {
                    console.log('🚪 DÉCONNEXION DÉFINITIVE (LOGGED OUT)');
                    console.log('====================================');
                    console.log('💡 Action requise:');
                    console.log('   Supprimez auth_info/ pour générer un nouveau QR');
                    console.log('   curl -X DELETE http://localhost:' + PORT + '/session');
                    console.log('====================================\n');
                }
            }
            
            // Connexion ouverte
            if (connection === 'open') {
                isConnecting = false;
                console.log('\n====================================');
                console.log('✅ CONNEXION ÉTABLIE');
                console.log('====================================');
                connectionState = 'connected';
                qrCodeData = null;
                reconnectAttempts = 0;
                
                // Afficher les infos du compte
                const userInfo = sock.user;
                console.log('👤 Compte:', userInfo.name || userInfo.id);
                console.log('📱 Numéro:', userInfo.id.split(':')[0]);
                console.log('====================================\n');
            }
            
            // En cours de connexion
            if (connection === 'connecting') {
                console.log('🔄 Connexion en cours...');
                connectionState = 'connecting';
            }
        });
        
        // Gestion des messages (pour monitoring)
        sock.ev.on('messages.upsert', async ({ messages, type }) => {
            if (type === 'notify') {
                for (const msg of messages) {
                    if (!msg.key.fromMe) {
                        const from = msg.key.remoteJid;
                        console.log('📩 Message reçu de:', from);
                    }
                }
            }
        });
        
    } catch (error) {
        isConnecting = false;
        console.error('\n====================================');
        console.error('❌ ERREUR DE CONNEXION');
        console.error('====================================');
        console.error('Message:', error.message);
        console.error('Stack:', error.stack);
        console.error('====================================\n');
        
        connectionState = 'error';
        
        // Réessayer après délai
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            const delay = RECONNECT_DELAY * reconnectAttempts;
            console.log(`🔄 Nouvelle tentative dans ${delay/1000}s...\n`);
            setTimeout(connectWhatsApp, delay);
        }
    }
}

/**
 * Obtenir une description lisible de la raison de déconnexion
 */
function getDisconnectReason(code) {
    const reasons = {
        [DisconnectReason.badSession]: 'Session invalide',
        [DisconnectReason.connectionClosed]: 'Connexion fermée',
        [DisconnectReason.connectionLost]: 'Connexion perdue',
        [DisconnectReason.connectionReplaced]: 'Connexion remplacée',
        [DisconnectReason.loggedOut]: 'Déconnecté (logged out)',
        [DisconnectReason.restartRequired]: 'Redémarrage requis',
        [DisconnectReason.timedOut]: 'Timeout',
        [DisconnectReason.forbidden]: 'Interdit (banned?)',
        [DisconnectReason.unavailableService]: 'Service indisponible'
    };
    return reasons[code] || 'Raison inconnue';
}

// ============================
// ENDPOINTS API
// ============================

/**
 * GET /health - Vérifier l'état du service
 */
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        connection_state: connectionState,
        is_connecting: isConnecting,
        reconnect_attempts: reconnectAttempts,
        qr_available: qrCodeData !== null,
        socket_exists: sock !== null,
        timestamp: new Date().toISOString()
    });
});

/**
 * GET /qr - Obtenir le QR code
 */
app.get('/qr', async (req, res) => {
    const format = req.query.format || 'image';
    
    if (!qrCodeData) {
        return res.status(404).json({
            error: 'Aucun QR code disponible',
            connection_state: connectionState,
            is_connecting: isConnecting,
            message: connectionState === 'connected' 
                ? 'Déjà connecté à WhatsApp' 
                : connectionState === 'connecting'
                ? 'Connexion en cours, QR en attente...'
                : 'En attente de génération du QR code'
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
                expires_in: '60s',
                instructions: 'Ouvrez WhatsApp > Appareils liés > Lier un appareil'
            });
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * GET /groups - Lister tous les groupes
 */
app.get('/groups', async (req, res) => {
    if (connectionState !== 'connected' || !sock) {
        return res.status(503).json({ 
            error: 'WhatsApp non connecté',
            connection_state: connectionState,
            is_connecting: isConnecting
        });
    }
    
    try {
        const groups = await sock.groupFetchAllParticipating();
        const groupsList = Object.values(groups).map(group => ({
            id: group.id,
            name: group.subject,
            participants_count: group.participants.length,
            creation: group.creation,
            description: group.desc || ''
        }));
        
        res.json({
            count: groupsList.length,
            groups: groupsList
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * GET /groups/:groupId/messages - Messages d'un groupe
 */
app.get('/groups/:groupId/messages', async (req, res) => {
    if (connectionState !== 'connected' || !sock) {
        return res.status(503).json({ 
            error: 'WhatsApp non connecté',
            connection_state: connectionState
        });
    }
    
    const { groupId } = req.params;
    const limit = parseInt(req.query.limit) || 50;
    
    try {
        const messages = await sock.fetchMessagesFromWA(groupId, limit);
        
        const formattedMessages = messages.map(msg => ({
            id: msg.key.id,
            from: msg.key.participant || msg.key.remoteJid,
            timestamp: msg.messageTimestamp,
            message: msg.message?.conversation || 
                     msg.message?.extendedTextMessage?.text ||
                     msg.message?.imageMessage?.caption ||
                     msg.message?.videoMessage?.caption ||
                     '[Media]',
            type: Object.keys(msg.message || {})[0]
        }));
        
        res.json({
            group_id: groupId,
            count: formattedMessages.length,
            messages: formattedMessages
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * POST /send - Envoyer un message
 */
app.post('/send', async (req, res) => {
    if (connectionState !== 'connected' || !sock) {
        return res.status(503).json({ 
            error: 'WhatsApp non connecté',
            connection_state: connectionState
        });
    }
    
    const { to, message } = req.body;
    
    if (!to || !message) {
        return res.status(400).json({ 
            error: 'Paramètres "to" et "message" requis',
            example: {
                to: "237698773224@s.whatsapp.net",
                message: "Test message"
            }
        });
    }
    
    try {
        await sock.sendMessage(to, { text: message });
        res.json({ 
            success: true, 
            message: 'Message envoyé',
            to: to
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * POST /reconnect - Forcer reconnexion
 */
app.post('/reconnect', (req, res) => {
    console.log('\n====================================');
    console.log('🔄 RECONNEXION FORCÉE');
    console.log('====================================\n');
    
    reconnectAttempts = 0;
    isConnecting = false;
    
    if (sock) {
        sock.end();
    }
    
    setTimeout(connectWhatsApp, 1000);
    
    res.json({ 
        success: true, 
        message: 'Reconnexion initiée'
    });
});

/**
 * DELETE /session - Supprimer la session
 */
app.delete('/session', async (req, res) => {
    console.log('\n====================================');
    console.log('🗑️ SUPPRESSION DE SESSION');
    console.log('====================================\n');
    
    if (sock) {
        try {
            await sock.logout();
        } catch (err) {
            console.error('⚠️ Erreur logout:', err.message);
        }
        sock.end();
    }
    
    // Supprimer les fichiers d'authentification
    const fsPromises = require('fs').promises;
    try {
        await fsPromises.rm(AUTH_FOLDER, { recursive: true, force: true });
        console.log('✅ Fichiers supprimés');
    } catch (err) {
        console.error('⚠️ Erreur suppression:', err.message);
    }
    
    // Recréer le dossier
    ensureAuthFolder();
    
    // Réinitialiser l'état
    reconnectAttempts = 0;
    isConnecting = false;
    qrCodeData = null;
    connectionState = 'disconnected';
    
    setTimeout(connectWhatsApp, 1000);
    
    res.json({ 
        success: true, 
        message: 'Session supprimée. Nouveau QR en génération...'
    });
});

// ============================
// PAGE HTML SIMPLE POUR QR
// ============================

app.get('/', (req, res) => {
    res.send(`
<!DOCTYPE html>
<html>
<head>
    <title>WhatsApp Bridge - QR Code</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            text-align: center;
            background: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #25D366; }
        .qr-container {
            margin: 30px 0;
            min-height: 400px;
        }
        img { max-width: 100%; }
        .status {
            padding: 10px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .connected { background: #d4edda; color: #155724; }
        .qr-ready { background: #fff3cd; color: #856404; }
        .disconnected { background: #f8d7da; color: #721c24; }
        button {
            background: #25D366;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        button:hover { background: #128C7E; }
        .instructions {
            text-align: left;
            margin: 20px 0;
            padding: 15px;
            background: #e7f3ff;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 WhatsApp Bridge</h1>
        <div id="status" class="status">Chargement...</div>
        <div class="qr-container" id="qr-container">
            <p>Vérification de l'état...</p>
        </div>
        <div class="instructions">
            <h3>Instructions:</h3>
            <ol>
                <li>Ouvrez WhatsApp sur votre téléphone</li>
                <li>Allez dans <strong>Paramètres</strong> → <strong>Appareils liés</strong></li>
                <li>Appuyez sur <strong>Lier un appareil</strong></li>
                <li>Scannez le QR code ci-dessus</li>
            </ol>
        </div>
        <button onclick="refresh()">🔄 Rafraîchir</button>
        <button onclick="reconnect()">🔌 Reconnecter</button>
        <button onclick="deleteSession()">🗑️ Nouvelle Session</button>
    </div>
    
    <script>
        async function checkStatus() {
            try {
                const res = await fetch('/health');
                const data = await res.json();
                
                const statusDiv = document.getElementById('status');
                const qrDiv = document.getElementById('qr-container');
                
                if (data.connection_state === 'connected') {
                    statusDiv.className = 'status connected';
                    statusDiv.innerHTML = '✅ Connecté à WhatsApp';
                    qrDiv.innerHTML = '<p style="color: green; font-size: 20px;">✅ WhatsApp connecté avec succès!</p>';
                } else if (data.qr_available) {
                    statusDiv.className = 'status qr-ready';
                    statusDiv.innerHTML = '⏳ QR Code disponible - Scannez-le maintenant';
                    qrDiv.innerHTML = '<img src="/qr?format=image" alt="QR Code">';
                } else {
                    statusDiv.className = 'status disconnected';
                    statusDiv.innerHTML = '⏳ En attente du QR code...';
                    qrDiv.innerHTML = '<p>Génération du QR code en cours...</p>';
                }
            } catch (err) {
                console.error(err);
                document.getElementById('status').innerHTML = '❌ Erreur de connexion au service';
            }
        }
        
        function refresh() {
            location.reload();
        }
        
        async function reconnect() {
            if (confirm('Forcer la reconnexion?')) {
                await fetch('/reconnect', { method: 'POST' });
                setTimeout(() => location.reload(), 2000);
            }
        }
        
        async function deleteSession() {
            if (confirm('Supprimer la session et générer un nouveau QR code?')) {
                await fetch('/session', { method: 'DELETE' });
                setTimeout(() => location.reload(), 2000);
            }
        }
        
        // Vérifier l'état toutes les 3 secondes
        checkStatus();
        setInterval(checkStatus, 3000);
    </script>
</body>
</html>
    `);
});

// ============================
// DÉMARRAGE
// ============================

app.listen(PORT, () => {
    console.log('====================================');
    console.log('📱 WhatsApp Bridge v2.1 - OPTIMISÉ');
    console.log('====================================');
    console.log(`🌐 URL: http://localhost:${PORT}`);
    console.log(`📄 Interface Web: http://localhost:${PORT}/`);
    console.log('\n📚 Endpoints:');
    console.log(`   GET    /              - Interface QR web`);
    console.log(`   GET    /health        - État du service`);
    console.log(`   GET    /qr            - QR code`);
    console.log(`   GET    /groups        - Liste des groupes`);
    console.log(`   POST   /send          - Envoyer message`);
    console.log(`   POST   /reconnect     - Reconnecter`);
    console.log(`   DELETE /session       - Nouvelle session`);
    console.log('====================================\n');
    
    // Vérifier le dossier d'authentification
    ensureAuthFolder();
    
    // Démarrer la connexion
    connectWhatsApp();
});

// Gestion propre de l'arrêt
process.on('SIGINT', async () => {
    console.log('\n⚠️ Arrêt du service...');
    if (sock) {
        await sock.end();
    }
    process.exit(0);
});

process.on('uncaughtException', (error) => {
    console.error('❌ Exception non gérée:', error.message);
    console.error('Stack:', error.stack);
});

process.on('unhandledRejection', (error) => {
    console.error('❌ Promesse rejetée:', error);
});