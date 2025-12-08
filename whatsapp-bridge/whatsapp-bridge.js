/**
 * WhatsApp Bridge pour Brand Monitor
 * Utilise Baileys pour se connecter à WhatsApp
 */

const { default: makeWASocket, DisconnectReason, useMultiFileAuthState } = require('@whiskeysockets/baileys');
const express = require('express');
const cors = require('cors');
const qrcode = require('qrcode-terminal');
const pino = require('pino');

const app = express();
app.use(cors());
app.use(express.json());

// Logger
const logger = pino({ level: 'info' });

let sock;
let isConnected = false;
let qrCodeData = null;

/**
 * Connexion à WhatsApp
 */
async function connectWhatsApp() {
    try {
        const { state, saveCreds } = await useMultiFileAuthState('auth_info');
        
        sock = makeWASocket({
            auth: state,
            printQRInTerminal: true,
            logger: pino({ level: 'silent' }),
            browser: ['Brand Monitor', 'Chrome', '1.0.0']
        });
        
        // Gestion des événements de connexion
        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;
            
            if (qr) {
                qrCodeData = qr;
                console.log('\n📱 QR Code généré - Scannez avec WhatsApp\n');
                qrcode.generate(qr, { small: true });
            }
            
            if (connection === 'close') {
                const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
                
                if (shouldReconnect) {
                    console.log('🔄 Reconnexion...');
                    await connectWhatsApp();
                } else {
                    console.log('❌ Déconnecté de WhatsApp');
                    isConnected = false;
                }
            } else if (connection === 'open') {
                isConnected = true;
                qrCodeData = null;
                console.log('✅ Connecté à WhatsApp');
            }
        });
        
        // Sauvegarder les credentials
        sock.ev.on('creds.update', saveCreds);
        
        // Écouter les nouveaux messages (optionnel)
        sock.ev.on('messages.upsert', async (m) => {
            const msg = m.messages[0];
            if (!msg.key.fromMe && m.type === 'notify') {
                console.log('📩 Nouveau message:', msg.key.remoteJid);
            }
        });
        
    } catch (error) {
        console.error('❌ Erreur connexion WhatsApp:', error);
        setTimeout(connectWhatsApp, 5000);
    }
}

// ============ ROUTES API ============

/**
 * Vérifier le statut de connexion
 */
app.get('/status', (req, res) => {
    res.json({
        connected: isConnected,
        qrCode: qrCodeData,
        timestamp: new Date().toISOString()
    });
});

/**
 * Obtenir le QR Code
 */
app.get('/qr', (req, res) => {
    if (qrCodeData) {
        res.json({ qr: qrCodeData });
    } else if (isConnected) {
        res.status(200).json({ message: 'Déjà connecté' });
    } else {
        res.status(404).json({ error: 'QR Code non disponible' });
    }
});

/**
 * Collecter les messages d'un groupe
 */
app.post('/messages/group', async (req, res) => {
    const { group_id, limit = 50 } = req.body;
    
    if (!isConnected) {
        return res.status(503).json({ error: 'WhatsApp non connecté' });
    }
    
    try {
        // Récupérer les messages du groupe
        const messages = await sock.fetchMessagesFromWA(group_id, limit, { before: null });
        
        const formattedMessages = messages.map(msg => ({
            id: msg.key.id,
            text: msg.message?.conversation || 
                  msg.message?.extendedTextMessage?.text || 
                  '[Média]',
            sender: msg.key.participant || msg.key.remoteJid,
            sender_name: msg.pushName || 'Inconnu',
            timestamp: msg.messageTimestamp,
            group_id: group_id,
            has_media: !!(msg.message?.imageMessage || msg.message?.videoMessage),
            media_type: msg.message?.imageMessage ? 'image' : 
                       msg.message?.videoMessage ? 'video' : null,
            quoted: !!msg.message?.extendedTextMessage?.contextInfo?.quotedMessage
        }));
        
        res.json({ messages: formattedMessages });
        
    } catch (error) {
        console.error('Erreur récupération messages:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * Obtenir les informations d'un groupe
 */
app.get('/group/:id', async (req, res) => {
    if (!isConnected) {
        return res.status(503).json({ error: 'WhatsApp non connecté' });
    }
    
    try {
        const metadata = await sock.groupMetadata(req.params.id);
        
        res.json({
            id: metadata.id,
            subject: metadata.subject,
            description: metadata.desc,
            owner: metadata.owner,
            creation: metadata.creation,
            participants: metadata.participants.length,
            participants_list: metadata.participants.map(p => ({
                id: p.id,
                admin: p.admin,
            }))
        });
        
    } catch (error) {
        console.error('Erreur récupération metadata groupe:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * Lister tous les groupes
 */
app.get('/groups', async (req, res) => {
    if (!isConnected) {
        return res.status(503).json({ error: 'WhatsApp non connecté' });
    }
    
    try {
        const chats = await sock.groupFetchAllParticipating();
        
        const groups = Object.values(chats).map(chat => ({
            id: chat.id,
            subject: chat.subject,
            participants: chat.participants.length,
            creation: chat.creation
        }));
        
        res.json({ groups });
        
    } catch (error) {
        console.error('Erreur liste groupes:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * Health check
 */
app.get('/health', (req, res) => {
    res.json({ 
        status: 'ok',
        service: 'WhatsApp Bridge',
        version: '1.0.0',
        connected: isConnected
    });
});

// ============ DÉMARRAGE ============

const PORT = process.env.PORT || 3500;

app.listen(PORT, () => {
    console.log('='.repeat(50));
    console.log(`🚀 WhatsApp Bridge démarré sur le port ${PORT}`);
    console.log('='.repeat(50));
    console.log('\n📱 Initialisation de la connexion WhatsApp...\n');
    
    connectWhatsApp();
});

// Gestion de l'arrêt propre
process.on('SIGINT', async () => {
    console.log('\n\n🛑 Arrêt du serveur...');
    if (sock) {
        await sock.logout();
    }
    process.exit(0);
});