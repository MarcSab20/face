// Configuration de l'API
const API_BASE_URL = 'http://localhost:8000';

// Charger les données au démarrage
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadKeywords();
    loadMentions();
    
    // Actualiser toutes les 30 secondes
    setInterval(() => {
        loadStats();
        loadMentions();
    }, 30000);
});

// ===== Statistiques =====

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats`);
        const data = await response.json();
        
        document.getElementById('totalKeywords').textContent = data.total_keywords;
        document.getElementById('totalMentions').textContent = data.total_mentions;
        document.getElementById('mentionsToday').textContent = data.mentions_today;
        
        // Afficher le graphique des sources
        displaySourceChart(data.mentions_by_source);
        
    } catch (error) {
        console.error('Erreur chargement stats:', error);
    }
}

function displaySourceChart(data) {
    const chartDiv = document.getElementById('sourceChart');
    
    if (!data || Object.keys(data).length === 0) {
        chartDiv.innerHTML = '<p class="empty-state">Aucune donnée disponible</p>';
        return;
    }
    
    const maxValue = Math.max(...Object.values(data));
    
    let html = '';
    const sourceNames = {
        'rss': '📰 RSS',
        'reddit': '🔴 Reddit',
        'youtube': '📺 YouTube',
        'tiktok': '🎵 TikTok',
        'google_search': '🔍 Google Search',
        'google_alerts': '📧 Google Alerts'
    };
    
    for (const [source, count] of Object.entries(data)) {
        const percentage = maxValue > 0 ? (count / maxValue) * 100 : 0;
        
        html += `
            <div class="chart-bar">
                <div class="chart-label">${sourceNames[source] || source}</div>
                <div class="chart-value-container">
                    <div class="chart-value" style="width: ${percentage}%"></div>
                    <span class="chart-number">${count}</span>
                </div>
            </div>
        `;
    }
    
    chartDiv.innerHTML = html;
}

// ===== Mots-clés =====

async function loadKeywords() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/keywords`);
        const keywords = await response.json();
        
        displayKeywords(keywords);
        
        // Mettre à jour le filtre
        const keywordFilter = document.getElementById('keywordFilter');
        keywordFilter.innerHTML = '<option value="">Tous les mots-clés</option>';
        keywords.forEach(kw => {
            keywordFilter.innerHTML += `<option value="${kw.keyword}">${kw.keyword}</option>`;
        });
        
    } catch (error) {
        console.error('Erreur chargement mots-clés:', error);
    }
}

function displayKeywords(keywords) {
    const listDiv = document.getElementById('keywordsList');
    
    if (keywords.length === 0) {
        listDiv.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <p>Aucun mot-clé configuré</p>
                <p style="font-size: 0.9em; margin-top: 10px;">Ajoutez votre premier mot-clé ci-dessus pour commencer</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    for (const keyword of keywords) {
        const sources = JSON.parse(keyword.sources);
        const lastCollected = keyword.last_collected 
            ? new Date(keyword.last_collected).toLocaleString('fr-FR')
            : 'Jamais';
        
        html += `
            <div class="keyword-item">
                <div class="keyword-info">
                    <div class="keyword-name">${keyword.keyword}</div>
                    <div class="keyword-meta">
                        <span>📊 Sources: ${sources.join(', ')}</span>
                        <span>🕒 Dernière collecte: ${lastCollected}</span>
                    </div>
                </div>
                <div class="keyword-actions">
                    <button onclick="collectKeyword(${keyword.id})" class="btn btn-success">
                        Collecter
                    </button>
                    <button onclick="deleteKeyword(${keyword.id})" class="btn btn-danger">
                        Supprimer
                    </button>
                </div>
            </div>
        `;
    }
    
    listDiv.innerHTML = html;
}

async function addKeyword() {
    const keywordInput = document.getElementById('keywordInput');
    const keyword = keywordInput.value.trim();
    
    if (!keyword) {
        alert('Veuillez entrer un mot-clé');
        return;
    }
    
    // Récupérer les sources sélectionnées
    const checkboxes = document.querySelectorAll('input[name="source"]:checked');
    const sources = Array.from(checkboxes).map(cb => cb.value);
    
    if (sources.length === 0) {
        alert('Veuillez sélectionner au moins une source');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/keywords`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ keyword, sources })
        });
        
        if (response.ok) {
            keywordInput.value = '';
            loadKeywords();
            alert('Mot-clé ajouté avec succès !');
        } else {
            const error = await response.json();
            alert('Erreur: ' + (error.detail || 'Impossible d\'ajouter le mot-clé'));
        }
    } catch (error) {
        console.error('Erreur ajout mot-clé:', error);
        alert('Erreur de connexion au serveur');
    }
}

async function deleteKeyword(id) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce mot-clé ?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/keywords/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadKeywords();
            loadStats();
            loadMentions();
        } else {
            alert('Erreur lors de la suppression');
        }
    } catch (error) {
        console.error('Erreur suppression mot-clé:', error);
        alert('Erreur de connexion au serveur');
    }
}

async function collectKeyword(id) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/collect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ keyword_id: id })
        });
        
        if (response.ok) {
            alert('Collecte lancée ! Les résultats apparaîtront dans quelques instants.');
            setTimeout(() => {
                loadStats();
                loadMentions();
                loadKeywords();
            }, 3000);
        } else {
            alert('Erreur lors du lancement de la collecte');
        }
    } catch (error) {
        console.error('Erreur collecte:', error);
        alert('Erreur de connexion au serveur');
    }
}

// ===== Collecte globale =====

async function startCollection() {
    const btn = document.getElementById('collectBtn');
    btn.disabled = true;
    btn.textContent = 'Collecte en cours...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/collect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        if (response.ok) {
            alert('Collecte lancée pour tous les mots-clés ! Les résultats apparaîtront progressivement.');
            
            // Actualiser après quelques secondes
            setTimeout(() => {
                loadStats();
                loadMentions();
                loadKeywords();
            }, 5000);
        } else {
            alert('Erreur lors du lancement de la collecte');
        }
    } catch (error) {
        console.error('Erreur collecte:', error);
        alert('Erreur de connexion au serveur');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Lancer la collecte';
    }
}

// ===== Mentions =====

async function loadMentions() {
    const sourceFilter = document.getElementById('sourceFilter').value;
    const keywordFilter = document.getElementById('keywordFilter').value;
    
    const listDiv = document.getElementById('mentionsList');
    listDiv.innerHTML = '<p class="loading">Chargement des mentions...</p>';
    
    try {
        let url = `${API_BASE_URL}/api/mentions?limit=50`;
        if (sourceFilter) url += `&source=${sourceFilter}`;
        if (keywordFilter) url += `&keyword=${encodeURIComponent(keywordFilter)}`;
        
        const response = await fetch(url);
        const mentions = await response.json();
        
        displayMentions(mentions);
        
    } catch (error) {
        console.error('Erreur chargement mentions:', error);
        listDiv.innerHTML = '<p class="loading">Erreur de chargement</p>';
    }
}

function displayMentions(mentions) {
    const listDiv = document.getElementById('mentionsList');
    
    if (mentions.length === 0) {
        listDiv.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <p>Aucune mention trouvée</p>
                <p style="font-size: 0.9em; margin-top: 10px;">
                    Lancez une collecte pour obtenir des résultats
                </p>
            </div>
        `;
        return;
    }
    
    const sourceEmojis = {
        'rss': '📰',
        'reddit': '🔴',
        'youtube': '📺',
        'tiktok': '🎵',
        'google_search': '🔍',
        'google_alerts': '📧'
    };
    
    let html = '';
    for (const mention of mentions) {
        const publishedDate = mention.published_at 
            ? new Date(mention.published_at).toLocaleString('fr-FR')
            : 'Date inconnue';
        
        const collectedDate = new Date(mention.collected_at).toLocaleString('fr-FR');
        
        const emoji = sourceEmojis[mention.source] || '📄';
        
        html += `
            <div class="mention-item">
                <div class="mention-header">
                    <span class="mention-source source-${mention.source}">
                        ${emoji} ${mention.source}
                    </span>
                    <span class="mention-date">${publishedDate}</span>
                </div>
                
                <h3 class="mention-title">
                    <a href="${mention.source_url}" target="_blank">
                        ${escapeHtml(mention.title || 'Sans titre')}
                    </a>
                </h3>
                
                <p class="mention-content">
                    ${escapeHtml(mention.content.substring(0, 300))}${mention.content.length > 300 ? '...' : ''}
                </p>
                
                <div class="mention-meta">
                    <span>👤 ${escapeHtml(mention.author)}</span>
                    <span>⭐ Score: ${Math.round(mention.engagement_score)}</span>
                    <span>🕒 Collecté: ${collectedDate}</span>
                </div>
            </div>
        `;
    }
    
    listDiv.innerHTML = html;
}

// ===== Utilitaires =====

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Raccourcis clavier
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.target.id === 'keywordInput') {
        addKeyword();
    }
});