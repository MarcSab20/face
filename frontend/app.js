// Configuration de l'API
const API_BASE_URL = 'http://localhost:8000';

// Variables globales
let currentOffset = 0;
let currentFilters = {};
let charts = {};

// Charger les données au démarrage
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadKeywords();
    loadMentions();
    loadAdvancedStats();
    
    // Actualiser toutes les 30 secondes
    setInterval(() => {
        loadStats();
        loadMentions();
    }, 30000);
    
    // Actualiser les graphiques toutes les 60 secondes
    setInterval(() => {
        loadAdvancedStats();
    }, 60000);
});

// ===== Statistiques de base =====

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats`);
        const data = await response.json();
        
        document.getElementById('totalKeywords').textContent = data.total_keywords;
        document.getElementById('totalMentions').textContent = data.total_mentions;
        document.getElementById('mentionsToday').textContent = data.mentions_today;
        
        // Afficher les sentiments
        if (data.sentiment_distribution) {
            document.getElementById('positiveCount').textContent = data.sentiment_distribution.positive || 0;
            document.getElementById('neutralCount').textContent = data.sentiment_distribution.neutral || 0;
            document.getElementById('negativeCount').textContent = data.sentiment_distribution.negative || 0;
        }
        
    } catch (error) {
        console.error('Erreur chargement stats:', error);
    }
}

// ===== Statistiques avancées et graphiques =====

async function loadAdvancedStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats/advanced?days=7`);
        const data = await response.json();
        
        // Timeline
        createTimelineChart(data.timeline);
        
        // Sentiment par source
        createSentimentBySourceChart(data.sentiment_by_source);
        
        // Top mentions engageantes
        displayTopEngaged(data.top_engaged);
        
        // Créer le graphique des sentiments
        await createSentimentChart();
        
        // Créer le graphique des sources
        await createSourcesChart();
        
    } catch (error) {
        console.error('Erreur chargement stats avancées:', error);
    }
}

function createTimelineChart(timelineData) {
    const ctx = document.getElementById('timelineChart');
    if (!ctx) return;
    
    // Détruire l'ancien graphique s'il existe
    if (charts.timeline) {
        charts.timeline.destroy();
    }
    
    const labels = timelineData.map(d => d.date);
    const data = timelineData.map(d => d.count);
    
    charts.timeline = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Mentions',
                data: data,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

async function createSentimentChart() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats`);
        const data = await response.json();
        
        if (!data.sentiment_distribution) return;
        
        const ctx = document.getElementById('sentimentChart');
        if (!ctx) return;
        
        if (charts.sentiment) {
            charts.sentiment.destroy();
        }
        
        const sentiments = data.sentiment_distribution;
        
        charts.sentiment = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Positif', 'Neutre', 'Négatif'],
                datasets: [{
                    data: [
                        sentiments.positive || 0,
                        sentiments.neutral || 0,
                        sentiments.negative || 0
                    ],
                    backgroundColor: [
                        '#28a745',
                        '#6c757d',
                        '#dc3545'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    } catch (error) {
        console.error('Erreur création graphique sentiment:', error);
    }
}

async function createSourcesChart() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats`);
        const data = await response.json();
        
        const ctx = document.getElementById('sourcesChart');
        if (!ctx) return;
        
        if (charts.sources) {
            charts.sources.destroy();
        }
        
        const sources = data.mentions_by_source;
        const labels = Object.keys(sources);
        const values = Object.values(sources);
        
        charts.sources = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Mentions',
                    data: values,
                    backgroundColor: [
                        '#ff6b35',
                        '#ff4500',
                        '#ff0000',
                        '#000000',
                        '#4285f4',
                        '#34a853'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Erreur création graphique sources:', error);
    }
}

function createSentimentBySourceChart(sentimentBySource) {
    const ctx = document.getElementById('sentimentBySourceChart');
    if (!ctx) return;
    
    if (charts.sentimentBySource) {
        charts.sentimentBySource.destroy();
    }
    
    // Préparer les données
    const sources = Object.keys(sentimentBySource);
    const positiveData = sources.map(s => sentimentBySource[s].positive || 0);
    const neutralData = sources.map(s => sentimentBySource[s].neutral || 0);
    const negativeData = sources.map(s => sentimentBySource[s].negative || 0);
    
    charts.sentimentBySource = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sources,
            datasets: [
                {
                    label: 'Positif',
                    data: positiveData,
                    backgroundColor: '#28a745'
                },
                {
                    label: 'Neutre',
                    data: neutralData,
                    backgroundColor: '#6c757d'
                },
                {
                    label: 'Négatif',
                    data: negativeData,
                    backgroundColor: '#dc3545'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true
                }
            }
        }
    });
}

function displayTopEngaged(topEngaged) {
    const container = document.getElementById('topEngaged');
    if (!container) return;
    
    if (topEngaged.length === 0) {
        container.innerHTML = '<p class="empty-state">Aucune mention engageante</p>';
        return;
    }
    
    let html = '<div class="top-engaged-grid">';
    
    topEngaged.forEach((mention, index) => {
        const sentimentEmoji = {
            'positive': '😊',
            'neutral': '😐',
            'negative': '😞'
        }[mention.sentiment] || '😐';
        
        const sentimentClass = mention.sentiment || 'neutral';
        
        html += `
            <div class="top-engaged-item">
                <div class="rank">#${index + 1}</div>
                <div class="content">
                    <h4>
                        <a href="${mention.url}" target="_blank">
                            ${escapeHtml(mention.title.substring(0, 80))}${mention.title.length > 80 ? '...' : ''}
                        </a>
                    </h4>
                    <div class="metadata">
                        <span class="source-badge source-${mention.source}">${mention.source}</span>
                        <span class="sentiment-badge sentiment-${sentimentClass}">
                            ${sentimentEmoji} ${sentimentClass}
                        </span>
                        <span class="engagement">
                            ⭐ ${formatNumber(mention.engagement)}
                        </span>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
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
            showNotification('Mot-clé ajouté avec succès !', 'success');
        } else {
            const error = await response.json();
            showNotification('Erreur: ' + (error.detail || 'Impossible d\'ajouter le mot-clé'), 'error');
        }
    } catch (error) {
        console.error('Erreur ajout mot-clé:', error);
        showNotification('Erreur de connexion au serveur', 'error');
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
            showNotification('Mot-clé supprimé', 'success');
        } else {
            showNotification('Erreur lors de la suppression', 'error');
        }
    } catch (error) {
        console.error('Erreur suppression mot-clé:', error);
        showNotification('Erreur de connexion au serveur', 'error');
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
            showNotification('Collecte lancée ! Les résultats apparaîtront dans quelques instants.', 'success');
            setTimeout(() => {
                loadStats();
                loadMentions();
                loadKeywords();
                loadAdvancedStats();
            }, 3000);
        } else {
            showNotification('Erreur lors du lancement de la collecte', 'error');
        }
    } catch (error) {
        console.error('Erreur collecte:', error);
        showNotification('Erreur de connexion au serveur', 'error');
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
            showNotification('Collecte lancée pour tous les mots-clés ! Les résultats apparaîtront progressivement.', 'success');
            
            setTimeout(() => {
                loadStats();
                loadMentions();
                loadKeywords();
                loadAdvancedStats();
            }, 5000);
        } else {
            showNotification('Erreur lors du lancement de la collecte', 'error');
        }
    } catch (error) {
        console.error('Erreur collecte:', error);
        showNotification('Erreur de connexion au serveur', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Lancer la collecte';
    }
}

// ===== Analyse de sentiment =====

async function analyzeSentiments() {
    const btn = document.getElementById('analyzeBtn');
    btn.disabled = true;
    btn.textContent = 'Analyse en cours...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/analyze-all-sentiments`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            showNotification(`Analyse lancée pour ${data.count} mentions`, 'success');
            
            setTimeout(() => {
                loadStats();
                loadMentions();
                loadAdvancedStats();
            }, 3000);
        } else {
            showNotification('Erreur lors de l\'analyse', 'error');
        }
    } catch (error) {
        console.error('Erreur analyse:', error);
        showNotification('Erreur de connexion au serveur', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Analyser les sentiments';
    }
}


async function loadMentions() {
    const listDiv = document.getElementById('mentionsList');
    listDiv.innerHTML = '<p class="loading">Chargement des mentions...</p>';
    
    currentOffset = 0;
    
    try {
        let url = `${API_BASE_URL}/api/mentions?limit=50`;
        
        // Appliquer les filtres
        const filters = buildFiltersQuery();
        url += filters;
        
        const response = await fetch(url);
        const mentions = await response.json();
        
        displayMentions(mentions);
        
        // Mettre à jour le compteur
        document.getElementById('mentionsCount').textContent = mentions.length;
        
    } catch (error) {
        console.error('Erreur chargement mentions:', error);
        listDiv.innerHTML = '<p class="loading">Erreur de chargement</p>';
    }
}

function buildFiltersQuery() {
    let query = '';
    
    // Source
    const sourceFilter = document.getElementById('sourceFilter').value;
    if (sourceFilter) {
        query += `&source=${sourceFilter}`;
    }
    
    // Mot-clé
    const keywordFilter = document.getElementById('keywordFilter').value;
    if (keywordFilter) {
        query += `&keyword=${encodeURIComponent(keywordFilter)}`;
    }
    
    // Sentiment
    const sentimentFilter = document.getElementById('sentimentFilter').value;
    if (sentimentFilter) {
        query += `&sentiment=${sentimentFilter}`;
    }
    
    // Engagement
    const engagementFilter = document.getElementById('engagementFilter').value;
    if (engagementFilter) {
        query += `&min_engagement=${engagementFilter}`;
    }
    
    // Dates
    const dateFrom = document.getElementById('dateFrom').value;
    if (dateFrom) {
        query += `&date_from=${encodeURIComponent(dateFrom)}`;
    }
    
    const dateTo = document.getElementById('dateTo').value;
    if (dateTo) {
        query += `&date_to=${encodeURIComponent(dateTo)}`;
    }
    
    // Recherche textuelle
    const searchFilter = document.getElementById('searchFilter').value;
    if (searchFilter) {
        query += `&search=${encodeURIComponent(searchFilter)}`;
    }
    
    return query;
}

function displayMentions(mentions) {
    const listDiv = document.getElementById('mentionsList');
    
    if (mentions.length === 0) {
        listDiv.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <p>Aucune mention trouvée</p>
                <p style="font-size: 0.9em; margin-top: 10px;">
                    Modifiez vos filtres ou lancez une collecte
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
    
    const sentimentEmojis = {
        'positive': '😊',
        'neutral': '😐',
        'negative': '😞'
    };
    
    const sentimentColors = {
        'positive': '#28a745',
        'neutral': '#6c757d',
        'negative': '#dc3545'
    };
    
    let html = '';
    for (const mention of mentions) {
        const publishedDate = mention.published_at 
            ? new Date(mention.published_at).toLocaleString('fr-FR')
            : 'Date inconnue';
        
        const collectedDate = new Date(mention.collected_at).toLocaleString('fr-FR');
        
        const emoji = sourceEmojis[mention.source] || '📄';
        const sentimentEmoji = sentimentEmojis[mention.sentiment] || '😐';
        const sentimentColor = sentimentColors[mention.sentiment] || '#6c757d';
        
        html += `
            <div class="mention-item">
                <div class="mention-header">
                    <span class="mention-source source-${mention.source}">
                        ${emoji} ${mention.source}
                    </span>
                    <span class="mention-sentiment" style="background-color: ${sentimentColor};">
                        ${sentimentEmoji} ${mention.sentiment || 'inconnu'}
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
                    <span>⭐ Score: ${formatNumber(mention.engagement_score)}</span>
                    <span>🕒 Collecté: ${collectedDate}</span>
                </div>
            </div>
        `;
    }
    
    listDiv.innerHTML = html;
}

async function loadMoreMentions() {
    currentOffset += 50;
    
    try {
        let url = `${API_BASE_URL}/api/mentions?limit=50&offset=${currentOffset}`;
        const filters = buildFiltersQuery();
        url += filters;
        
        const response = await fetch(url);
        const mentions = await response.json();
        
        if (mentions.length === 0) {
            showNotification('Plus de mentions à charger', 'info');
            return;
        }
        
        // Ajouter les nouvelles mentions
        const listDiv = document.getElementById('mentionsList');
        const tempDiv = document.createElement('div');
        displayMentions(mentions);
        tempDiv.innerHTML = listDiv.innerHTML;
        
        listDiv.appendChild(tempDiv);
        
    } catch (error) {
        console.error('Erreur chargement mentions:', error);
    }
}

// ===== Filtres =====

function applyPeriodFilter() {
    const period = document.getElementById('periodFilter').value;
    const dateFrom = document.getElementById('dateFrom');
    const dateTo = document.getElementById('dateTo');
    
    const now = new Date();
    
    switch(period) {
        case 'today':
            const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            dateFrom.value = formatDateForInput(todayStart);
            dateTo.value = formatDateForInput(now);
            break;
            
        case 'week':
            const weekStart = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
            dateFrom.value = formatDateForInput(weekStart);
            dateTo.value = formatDateForInput(now);
            break;
            
        case 'month':
            const monthStart = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
            dateFrom.value = formatDateForInput(monthStart);
            dateTo.value = formatDateForInput(now);
            break;
            
        case 'custom':
            // Laisser l'utilisateur choisir
            break;
            
        default:
            dateFrom.value = '';
            dateTo.value = '';
    }
    
    if (period !== 'custom') {
        loadMentions();
    }
}

function resetFilters() {
    document.getElementById('sourceFilter').value = '';
    document.getElementById('keywordFilter').value = '';
    document.getElementById('sentimentFilter').value = '';
    document.getElementById('periodFilter').value = '';
    document.getElementById('engagementFilter').value = '';
    document.getElementById('dateFrom').value = '';
    document.getElementById('dateTo').value = '';
    document.getElementById('searchFilter').value = '';
    
    loadMentions();
}

// ===== Export de données =====

async function exportData() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/mentions?limit=1000`);
        const mentions = await response.json();
        
        if (mentions.length === 0) {
            showNotification('Aucune mention à exporter', 'info');
            return;
        }
        
        // Créer le CSV
        let csv = 'Date,Source,Titre,Auteur,Sentiment,Engagement,URL\n';
        
        mentions.forEach(m => {
            const date = m.published_at ? new Date(m.published_at).toISOString() : '';
            const title = `"${m.title.replace(/"/g, '""')}"`;
            const author = `"${m.author.replace(/"/g, '""')}"`;
            const sentiment = m.sentiment || 'inconnu';
            const engagement = m.engagement_score;
            const url = m.source_url;
            
            csv += `${date},${m.source},${title},${author},${sentiment},${engagement},${url}\n`;
        });
        
        // Télécharger le fichier
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        link.setAttribute('href', url);
        link.setAttribute('download', `mentions_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showNotification(`${mentions.length} mentions exportées`, 'success');
        
    } catch (error) {
        console.error('Erreur export:', error);
        showNotification('Erreur lors de l\'export', 'error');
    }
}

// ===== Utilitaires =====

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return Math.round(num).toString();
}

function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function showNotification(message, type = 'info') {
    // Créer la notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        z-index: 10000;
        animation: slideIn 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    `;
    
    // Couleurs selon le type
    const colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'info': '#17a2b8',
        'warning': '#ffc107'
    };
    
    notification.style.backgroundColor = colors[type] || colors.info;
    
    // Ajouter au body
    document.body.appendChild(notification);
    
    // Supprimer après 3 secondes
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Raccourcis clavier
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.target.id === 'keywordInput') {
        addKeyword();
    }
    
    if (e.key === 'Enter' && e.target.id === 'searchFilter') {
        loadMentions();
    }
});

// CSS pour les animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);