"""
Collecteur WhatsApp via Baileys (Node.js wrapper) ou OpenWA
Surveillance de groupes et status WhatsApp
"""

import logging
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
import subprocess
import os

logger = logging.getLogger(__name__)


class WhatsAppCollector:
    """
    Collecteur WhatsApp
    
    Utilise un serveur Node.js externe avec Baileys
    """
    
    def __init__(self, api_url: str = "http://localhost:3500"):
        """
        Initialiser le collecteur WhatsApp
        
        Args:
            api_url: URL du serveur WhatsApp Bridge
        """
        self.api_url = api_url
        self.is_connected = False
        
        logger.info("✅ WhatsApp Collector initialisé")
    
    def check_connection(self) -> bool:
        """Vérifier la connexion au serveur WhatsApp"""
        try:
            response = requests.get(f"{self.api_url}/status", timeout=5)
            self.is_connected = response.status_code == 200
            return self.is_connected
        except:
            self.is_connected = False
            return False
    
    def collect_group_messages(
        self,
        group_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Collecter les messages récents d'un groupe WhatsApp
        
        Args:
            group_id: ID du groupe WhatsApp
            limit: Nombre maximum de messages
            
        Returns:
            Liste de messages
        """
        if not self.check_connection():
            logger.error("❌ Serveur WhatsApp non disponible")
            return []
        
        logger.info(f"🔍 Collecte WhatsApp groupe: {group_id}")
        
        try:
            response = requests.post(
                f"{self.api_url}/messages/group",
                json={'group_id': group_id, 'limit': limit},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get('messages', [])
                
                # Formater les messages
                formatted_messages = []
                for msg in messages:
                    formatted_messages.append({
                        'id': msg.get('id'),
                        'text': msg.get('text', ''),
                        'sender': msg.get('sender', 'Inconnu'),
                        'sender_name': msg.get('sender_name', 'Inconnu'),
                        'timestamp': datetime.fromtimestamp(msg.get('timestamp', 0)),
                        'group_id': group_id,
                        'group_name': msg.get('group_name', ''),
                        'has_media': msg.get('has_media', False),
                        'media_type': msg.get('media_type'),
                        'quoted': msg.get('quoted', False),
                        'source': 'whatsapp'
                    })
                
                logger.info(f"✅ {len(formatted_messages)} messages collectés")
                return formatted_messages
            else:
                logger.error(f"❌ Erreur API WhatsApp: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur collecte WhatsApp: {e}")
            return []
    
    def collect_status_updates(self, limit: int = 20) -> List[Dict]:
        """
        Collecter les status WhatsApp récents
        
        Returns:
            Liste de status
        """
        if not self.check_connection():
            logger.error("❌ Serveur WhatsApp non disponible")
            return []
        
        logger.info("🔍 Collecte WhatsApp status")
        
        try:
            response = requests.get(
                f"{self.api_url}/status",
                params={'limit': limit},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('status', [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur collecte status: {e}")
            return []
    
    def get_group_info(self, group_id: str) -> Optional[Dict]:
        """Obtenir les informations d'un groupe"""
        if not self.check_connection():
            return None
        
        try:
            response = requests.get(
                f"{self.api_url}/group/{group_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            logger.error(f"Erreur récupération info groupe: {e}")
            return None


# Script Node.js à déployer séparément
WHATSAPP_BRIDGE_CODE = """
// whatsapp-bridge.js
// Installation: npm install @whiskeysockets/baileys express

const { default: makeWASocket, DisconnectReason, useMultiFileAuthState } = require('@whiskeysockets/baileys');
const express = require('express');
const app = express();
app.use(express.json());

let sock;
let isConnected = false;

// Initialiser connexion WhatsApp
async function connectWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info');
    
    sock = makeWASocket({
        auth: state,
        printQRInTerminal: true
    });
    
    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect } = update;
        if (connection === 'close') {
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
            if (shouldReconnect) {
                connectWhatsApp();
            }
        } else if (connection === 'open') {
            isConnected = true;
            console.log('✅ WhatsApp connecté');
        }
    });
    
    sock.ev.on('creds.update', saveCreds);
}

// Routes API
app.get('/status', (req, res) => {
    res.json({ connected: isConnected });
});

app.post('/messages/group', async (req, res) => {
    const { group_id, limit = 50 } = req.body;
    
    try {
        const messages = await sock.fetchMessagesFromWA(group_id, limit);
        res.json({ messages });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/group/:id', async (req, res) => {
    try {
        const metadata = await sock.groupMetadata(req.params.id);
        res.json(metadata);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Démarrer serveur
const PORT = process.env.PORT || 3500;
app.listen(PORT, () => {
    console.log(`🚀 WhatsApp Bridge démarré sur port ${PORT}`);
    connectWhatsApp();
});
"""


def setup_whatsapp_bridge():
    """Instructions pour configurer le pont WhatsApp"""
    print("""
    📱 Configuration du pont WhatsApp
    
    1. Créer un nouveau dossier:
       mkdir whatsapp-bridge && cd whatsapp-bridge
    
    2. Initialiser Node.js:
       npm init -y
    
    3. Installer dépendances:
       npm install @whiskeysockets/baileys express
    
    4. Créer le fichier whatsapp-bridge.js avec le code fourni
    
    5. Lancer le serveur:
       node whatsapp-bridge.js
    
    6. Scanner le QR code avec WhatsApp
    
    7. Le serveur sera accessible sur http://localhost:3500
    """)
    
    # Sauvegarder le code dans un fichier
    with open('whatsapp-bridge-setup.js', 'w') as f:
        f.write(WHATSAPP_BRIDGE_CODE)
    
    print("✅ Code sauvegardé dans: whatsapp-bridge-setup.js")


if __name__ == '__main__':
    # Afficher les instructions
    setup_whatsapp_bridge()
    
    # Test de connexion (si serveur déjà lancé)
    collector = WhatsAppCollector()
    if collector.check_connection():
        print("✅ Serveur WhatsApp disponible")
    else:
        print("❌ Serveur WhatsApp non disponible")