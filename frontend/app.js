/**
 * Brand Monitor - Application JavaScript Complète
 * Version 2.0 - Toutes fonctionnalités implémentées
 */

// Configuration
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : window.location.origin.replace(':8080', ':8000');

// État global de l'application
const AppState = {
    currentView: 'dashboard',
    keywords: [],
    mentions: [],
    stats: null,
    filters: {
        source: '',
        sentiment: '',
        period: '7d',
        search: ''
    },
    sources: []
};

// Utilitaires
const Utils = {
    /**
     * Faire une requête API
     */
    async fetchAPI(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            this.showError(`Erreur API: ${error.message}`);
            throw error;
        }
    },

    /**
     * Afficher un message de succès
     */
    showSuccess(message) {
        this.showToast(message, 'success');
    },

    /**
     * Afficher un message d'erreur
     */
    showError(message) {
        this.showToast(message, 'error');
    },

    /**
     * Afficher un toast notification
     */
    showToast(message, type = 'info') {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.cssText = `
            background: white;
            padding: 15px 20px;
            margin-bottom: 10px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-left: 4px solid ${type === 'success' ? '#10b981' : (type === 'error' ? '#ef4444' : '#3b82f6')};
            animation: slideIn 0.3s ease;
            max-width: 400px;
        `;
        toast.textContent = message;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    },

    /**
     * Formater une date
     */
    formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    /**
     * Formater un nombre
     */
    formatNumber(num) {
        if (num === null || num === undefined) return '-';
        return new Intl.NumberFormat('fr-FR').format(num);
    },

    /**
     * Afficher l'overlay de chargement
     */
    showLoading(text = 'Chargement...') {
        const overlay = document.getElementById('loadingOverlay');
        const loadingText = document.getElementById('loadingText');
        loadingText.textContent = text;
        overlay.style.display = 'flex';
    },

    /**
     * Masquer l'overlay de chargement
     */
    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = 'none';
    },

    /**
     * Obtenir la couleur du sentiment
     */
    getSentimentColor(sentiment) {
        const colors = {
            positive: '#10b981',
            neutral: '#64748b',
            negative: '#ef4444'
        };
        return colors[sentiment] || colors.neutral;
    },

    /**
     * Obtenir le badge sentiment HTML
     */
    getSentimentBadge(sentiment) {
        const badges = {
            positive: '<span class="badge success">Positif</span>',
            neutral: '<span class="badge info">Neutre</span>',
            negative: '<span class="badge danger">Négatif</span>'
        };
        return badges[sentiment] || '<span class="badge">-</span>';
    },

    /**
     * Obtenir le badge de niveau de risque
     */
    getRiskBadge(riskLevel) {
        const badges = {
            low: '<span class="badge success">Faible</span>',
            medium: '<span class="badge warning">Modéré</span>',
            high: '<span class="badge danger">Élevé</span>',
            critical: '<span class="badge danger risk-critical">CRITIQUE</span>'
        };
        return badges[riskLevel] || '<span class="badge">-</span>';
    }
};

// Gestionnaire de navigation
const Navigation = {
    init() {
        // Navigation dans la sidebar
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const view = item.dataset.view;
                this.navigateTo(view);
            });
        });

        // Toggle sidebar mobile
        document.getElementById('toggleSidebar')?.addEventListener('click', () => {
            document.querySelector('.sidebar').classList.toggle('active');
        });

        // Navigation initiale
        this.navigateTo('dashboard');
    },

    navigateTo(viewName) {
        // Mettre à jour l'état
        AppState.currentView = viewName;

        // Mettre à jour la nav active
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.view === viewName) {
                item.classList.add('active');
            }
        });

        // Afficher la vue
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });
        const targetView = document.getElementById(`${viewName}-view`);
        if (targetView) {
            targetView.classList.add('active');
        }

        // Mettre à jour le titre
        const titles = {
            dashboard: 'Dashboard',
            keywords: 'Mots-clés',
            mentions: 'Mentions',
            influencers: 'Influenceurs',
            analysis: 'Analyse IA',
            reports: 'Rapports',
            settings: 'Paramètres'
        };
        document.getElementById('pageTitle').textContent = titles[viewName] || 'Brand Monitor';

        // Charger les données de la vue
        this.loadViewData(viewName);
    },

    async loadViewData(viewName) {
        switch (viewName) {
            case 'dashboard':
                await Dashboard.load();
                break;
            case 'keywords':
                await Keywords.load();
                break;
            case 'mentions':
                await Mentions.load();
                break;
            case 'influencers':
                await Influencers.load();
                break;
            case 'analysis':
                await Analysis.init();
                break;
            case 'reports':
                await Reports.init();
                break;
            case 'settings':
                await Settings.load();
                break;
        }
    }
};

// Module Dashboard
const Dashboard = {
    charts: {},

    async load() {
        try {
            Utils.showLoading('Chargement du dashboard...');

            // Charger les statistiques
            const stats = await Utils.fetchAPI('/api/stats');
            AppState.stats = stats;

            // Mettre à jour les cartes de stats
            this.updateStatsCards(stats);

            // Charger les statistiques avancées pour les graphiques
            const advancedStats = await Utils.fetchAPI('/api/stats/advanced?days=7');
            
            // Créer les graphiques
            this.createActivityChart(advancedStats.timeline);
            this.createSentimentChart(stats.sentiment_distribution);
            this.updateSourcesList(stats.mentions_by_source);
            this.updateTopKeywordsList(stats.top_keywords);

            Utils.hideLoading();
        } catch (error) {
            Utils.hideLoading();
            console.error('Error loading dashboard:', error);
        }
    },

    updateStatsCards(stats) {
        document.getElementById('totalKeywords').textContent = Utils.formatNumber(stats.total_keywords);
        document.getElementById('totalMentions').textContent = Utils.formatNumber(stats.total_mentions);
        document.getElementById('mentionsToday').textContent = Utils.formatNumber(stats.mentions_today);
        
        // Calculer les alertes (mentions négatives)
        const alerts = stats.sentiment_distribution?.negative || 0;
        document.getElementById('alerts').textContent = Utils.formatNumber(alerts);
    },

    createActivityChart(timeline) {
        const ctx = document.getElementById('activityChart');
        if (!ctx) return;

        if (this.charts.activity) {
            this.charts.activity.destroy();
        }

        this.charts.activity = new Chart(ctx, {
            type: 'line',
            data: {
                labels: timeline.map(t => new Date(t.date).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })),
                datasets: [{
                    label: 'Mentions',
                    data: timeline.map(t => t.count),
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    },

    createSentimentChart(sentiments) {
        const ctx = document.getElementById('sentimentChart');
        if (!ctx) return;

        if (this.charts.sentiment) {
            this.charts.sentiment.destroy();
        }

        const data = {
            positive: sentiments?.positive || 0,
            neutral: sentiments?.neutral || 0,
            negative: sentiments?.negative || 0
        };

        this.charts.sentiment = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Positif', 'Neutre', 'Négatif'],
                datasets: [{
                    data: [data.positive, data.neutral, data.negative],
                    backgroundColor: ['#10b981', '#64748b', '#ef4444']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    },

    updateSourcesList(sources) {
        const container = document.getElementById('sourcesList');
        if (!container) return;

        const total = Object.values(sources).reduce((a, b) => a + b, 0);
        
        const html = Object.entries(sources)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([source, count]) => {
                const percentage = ((count / total) * 100).toFixed(1);
                return `
                    <div class="source-item" style="margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <span style="font-weight: 500;">${source}</span>
                            <span style="color: var(--secondary);">${count} (${percentage}%)</span>
                        </div>
                        <div style="background: var(--light); height: 8px; border-radius: 4px; overflow: hidden;">
                            <div style="background: var(--primary); height: 100%; width: ${percentage}%;"></div>
                        </div>
                    </div>
                `;
            })
            .join('');

        container.innerHTML = html || '<p style="color: var(--secondary); text-align: center;">Aucune donnée</p>';
    },

    updateTopKeywordsList(keywords) {
        const container = document.getElementById('topKeywordsList');
        if (!container) return;

        const html = keywords
            .slice(0, 5)
            .map((kw, index) => `
                <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--border);">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-weight: 600; color: var(--primary); font-size: 1.2rem;">#${index + 1}</span>
                        <span style="font-weight: 500;">${kw.keyword}</span>
                    </div>
                    <span class="badge info">${kw.mentions} mentions</span>
                </div>
            `)
            .join('');

        container.innerHTML = html || '<p style="color: var(--secondary); text-align: center;">Aucune donnée</p>';
    }
};

// Module Keywords
const Keywords = {
    async load() {
        try {
            Utils.showLoading('Chargement des mots-clés...');

            const keywords = await Utils.fetchAPI('/api/keywords');
            AppState.keywords = keywords;

            // Charger les sources disponibles
            if (AppState.sources.length === 0) {
                const sourcesData = await Utils.fetchAPI('/api/sources');
                AppState.sources = sourcesData.sources;
            }

            this.renderTable(keywords);

            Utils.hideLoading();
        } catch (error) {
            Utils.hideLoading();
            console.error('Error loading keywords:', error);
        }
    },

    renderTable(keywords) {
        const container = document.getElementById('keywordsTable');
        if (!container) return;

        if (keywords.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--secondary); padding: 40px;">Aucun mot-clé configuré. Cliquez sur "Nouveau Mot-clé" pour commencer.</p>';
            return;
        }

        const html = `
            <table>
                <thead>
                    <tr>
                        <th>Mot-clé</th>
                        <th>Sources</th>
                        <th>Statut</th>
                        <th>Créé le</th>
                        <th>Dernière collecte</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${keywords.map(kw => `
                        <tr>
                            <td><strong>${kw.keyword}</strong></td>
                            <td>${JSON.parse(kw.sources).join(', ')}</td>
                            <td>${kw.active ? '<span class="badge success">Actif</span>' : '<span class="badge">Inactif</span>'}</td>
                            <td>${Utils.formatDate(kw.created_at)}</td>
                            <td>${Utils.formatDate(kw.last_collected) || 'Jamais'}</td>
                            <td>
                                <button class="btn-icon-small" onclick="Keywords.collect(${kw.id})" title="Collecter">
                                    <i class="fas fa-sync-alt"></i>
                                </button>
                                <button class="btn-icon-small" onclick="Keywords.delete(${kw.id})" title="Supprimer">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        container.innerHTML = html;
    },

    showAddModal() {
        const sources = AppState.sources
            .filter(s => s.enabled)
            .map(s => `
                <label class="checkbox">
                    <input type="checkbox" name="sources" value="${s.id}" checked>
                    <span>${s.name}</span>
                </label>
            `).join('');

        const modalBody = `
            <form id="addKeywordForm">
                <div class="form-group">
                    <label>Mot-clé à surveiller</label>
                    <input type="text" id="keywordInput" class="form-control" placeholder="Ex: Cameroun politique" required>
                </div>
                <div class="form-group">
                    <label>Sources à surveiller</label>
                    <div class="checkbox-group">
                        ${sources}
                    </div>
                    <small>Sélectionnez au moins une source</small>
                </div>
                <div class="form-group full-width">
                    <button type="submit" class="btn btn-primary btn-block">
                        <i class="fas fa-plus"></i>
                        Créer le mot-clé
                    </button>
                </div>
            </form>
        `;

        Modal.show('Nouveau Mot-clé', modalBody);

        document.getElementById('addKeywordForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.addKeyword();
        });
    },

    async addKeyword() {
        const keyword = document.getElementById('keywordInput').value.trim();
        const sourcesCheckboxes = document.querySelectorAll('input[name="sources"]:checked');
        const sources = Array.from(sourcesCheckboxes).map(cb => cb.value);

        if (!keyword) {
            Utils.showError('Veuillez saisir un mot-clé');
            return;
        }

        if (sources.length === 0) {
            Utils.showError('Veuillez sélectionner au moins une source');
            return;
        }

        try {
            Utils.showLoading('Création du mot-clé...');

            await Utils.fetchAPI('/api/keywords', {
                method: 'POST',
                body: JSON.stringify({ keyword, sources })
            });

            Utils.hideLoading();
            Modal.hide();
            Utils.showSuccess('Mot-clé créé avec succès');
            this.load();
        } catch (error) {
            Utils.hideLoading();
            console.error('Error adding keyword:', error);
        }
    },

    async collect(keywordId) {
        try {
            Utils.showLoading('Collecte en cours...');

            await Utils.fetchAPI('/api/collect', {
                method: 'POST',
                body: JSON.stringify({ keyword_id: keywordId })
            });

            Utils.hideLoading();
            Utils.showSuccess('Collecte lancée avec succès');

            setTimeout(() => this.load(), 2000);
        } catch (error) {
            Utils.hideLoading();
        }
    },

    async delete(keywordId) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer ce mot-clé ?')) {
            return;
        }

        try {
            await Utils.fetchAPI(`/api/keywords/${keywordId}`, {
                method: 'DELETE'
            });

            Utils.showSuccess('Mot-clé supprimé');
            this.load();
        } catch (error) {
            console.error('Error deleting keyword:', error);
        }
    }
};

// Module Mentions
const Mentions = {
    currentFilters: {},

    async load() {
        try {
            Utils.showLoading('Chargement des mentions...');

            // Charger les sources disponibles pour le filtre
            if (AppState.sources.length === 0) {
                const sourcesData = await Utils.fetchAPI('/api/sources');
                AppState.sources = sourcesData.sources;
            }

            // Peupler le select des sources
            this.populateSourceFilter();

            // Charger les mentions avec les filtres actuels
            await this.applyFilters();

            Utils.hideLoading();
        } catch (error) {
            Utils.hideLoading();
            console.error('Error loading mentions:', error);
        }
    },

    populateSourceFilter() {
        const select = document.getElementById('filterSource');
        if (!select) return;

        const options = AppState.sources
            .filter(s => s.enabled)
            .map(s => `<option value="${s.id}">${s.name}</option>`)
            .join('');

        select.innerHTML = '<option value="">Toutes</option>' + options;
    },

    async applyFilters() {
        const source = document.getElementById('filterSource')?.value || '';
        const sentiment = document.getElementById('filterSentiment')?.value || '';
        const period = document.getElementById('filterPeriod')?.value || '7d';
        const search = document.getElementById('globalSearch')?.value || '';

        // Construire les paramètres de requête
        const params = new URLSearchParams();
        params.append('limit', '100');
        
        if (source) params.append('source', source);
        if (sentiment) params.append('sentiment', sentiment);
        if (search) params.append('search', search);

        // Calculer la date de début selon la période
        if (period !== 'all') {
            const now = new Date();
            let daysAgo = 7;
            
            if (period === '24h') daysAgo = 1;
            else if (period === '7d') daysAgo = 7;
            else if (period === '30d') daysAgo = 30;

            const dateFrom = new Date(now.getTime() - daysAgo * 24 * 60 * 60 * 1000);
            params.append('date_from', dateFrom.toISOString());
        }

        const mentions = await Utils.fetchAPI(`/api/mentions?${params.toString()}`);
        AppState.mentions = mentions;

        this.renderTable(mentions);
    },

    renderTable(mentions) {
        const container = document.getElementById('mentionsTable');
        if (!container) return;

        if (mentions.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--secondary); padding: 40px;">Aucune mention collectée</p>';
            return;
        }

        const html = `
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Titre</th>
                        <th>Source</th>
                        <th>Auteur</th>
                        <th>Sentiment</th>
                        <th>Engagement</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${mentions.slice(0, 50).map(m => `
                        <tr>
                            <td>${Utils.formatDate(m.published_at)}</td>
                            <td>
                                <a href="${m.source_url}" target="_blank" style="color: var(--primary); text-decoration: none;">
                                    ${m.title.substring(0, 60)}${m.title.length > 60 ? '...' : ''}
                                </a>
                            </td>
                            <td>${m.source}</td>
                            <td>${m.author}</td>
                            <td>${Utils.getSentimentBadge(m.sentiment)}</td>
                            <td>${Utils.formatNumber(m.engagement_score)}</td>
                            <td>
                                <button class="btn-icon-small" onclick="Mentions.viewDetails(${m.id})" title="Détails">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        container.innerHTML = html;
    },

    async viewDetails(mentionId) {
        try {
            const mention = await Utils.fetchAPI(`/api/mentions/${mentionId}`);
            
            const modalBody = `
                <div style="max-height: 60vh; overflow-y: auto;">
                    <div style="margin-bottom: 15px;">
                        <strong>Titre:</strong>
                        <p>${mention.title}</p>
                    </div>
                    <div style="margin-bottom: 15px;">
                        <strong>Contenu:</strong>
                        <p style="white-space: pre-wrap;">${mention.content}</p>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div>
                            <strong>Source:</strong>
                            <p>${mention.source}</p>
                        </div>
                        <div>
                            <strong>Auteur:</strong>
                            <p>${mention.author}</p>
                        </div>
                        <div>
                            <strong>Sentiment:</strong>
                            <p>${Utils.getSentimentBadge(mention.sentiment)}</p>
                        </div>
                        <div>
                            <strong>Engagement:</strong>
                            <p>${Utils.formatNumber(mention.engagement_score)}</p>
                        </div>
                        <div>
                            <strong>Publié le:</strong>
                            <p>${Utils.formatDate(mention.published_at)}</p>
                        </div>
                        <div>
                            <strong>Collecté le:</strong>
                            <p>${Utils.formatDate(mention.collected_at)}</p>
                        </div>
                    </div>
                    <div style="margin-top: 20px;">
                        <a href="${mention.source_url}" target="_blank" class="btn btn-primary" style="text-decoration: none;">
                            <i class="fas fa-external-link-alt"></i>
                            Voir la source
                        </a>
                    </div>
                </div>
            `;

            Modal.show('Détails de la Mention', modalBody);
        } catch (error) {
            console.error('Error loading mention details:', error);
        }
    }
};

// Module Influencers
const Influencers = {
    async load() {
        try {
            Utils.showLoading('Analyse des influenceurs...');

            const influencers = await Utils.fetchAPI('/api/advanced/influencers?days=30');
            
            this.renderActivists(influencers.activists);
            this.renderEmerging(influencers.emerging);
            this.renderMedia(influencers.official_media);

            Utils.hideLoading();
        } catch (error) {
            Utils.hideLoading();
            Utils.showError('Fonctionnalité d\'analyse des influenceurs non disponible');
            console.error('Error loading influencers:', error);
        }
    },

    renderActivists(activists) {
        const container = document.getElementById('activistsGrid');
        if (!container) return;

        if (activists.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--secondary); padding: 40px;">Aucun activiste détecté</p>';
            return;
        }

        const html = activists.map(inf => `
            <div class="card">
                <div class="card-body">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                        <div>
                            <h4 style="margin-bottom: 5px;">${inf.name}</h4>
                            <small style="color: var(--secondary);">${inf.source}</small>
                        </div>
                        ${Utils.getRiskBadge(inf.risk_level)}
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
                        <div>
                            <small style="color: var(--secondary);">Mentions</small>
                            <p style="font-weight: 600;">${inf.total_mentions}</p>
                        </div>
                        <div>
                            <small style="color: var(--secondary);">Engagement</small>
                            <p style="font-weight: 600;">${Utils.formatNumber(inf.total_engagement)}</p>
                        </div>
                        <div>
                            <small style="color: var(--secondary);">Portée estimée</small>
                            <p style="font-weight: 600;">${Utils.formatNumber(inf.reach_estimate)}</p>
                        </div>
                        <div>
                            <small style="color: var(--secondary);">Sentiment</small>
                            <p style="font-weight: 600;">${inf.sentiment_score}/100</p>
                        </div>
                    </div>
                    ${inf.trending ? '<span class="badge warning"><i class="fas fa-fire"></i> En tendance</span>' : ''}
                    <button class="btn btn-secondary btn-block" style="margin-top: 10px;" onclick="Influencers.viewDetails('${inf.name}', '${inf.source}')">
                        <i class="fas fa-chart-line"></i>
                        Voir le rapport détaillé
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = `<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px;">${html}</div>`;
    },

    renderEmerging(emerging) {
        const container = document.getElementById('emergingGrid');
        if (!container) return;

        if (emerging.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--secondary); padding: 40px;">Aucun influenceur émergent</p>';
            return;
        }

        const html = `
            <div class="card">
                <div class="card-body">
                    <table>
                        <thead>
                            <tr>
                                <th>Nom</th>
                                <th>Source</th>
                                <th>Mentions</th>
                                <th>Engagement</th>
                                <th>Sentiment</th>
                                <th>Risque</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${emerging.map(inf => `
                                <tr>
                                    <td>
                                        <strong>${inf.name}</strong>
                                        ${inf.trending ? ' <i class="fas fa-fire" style="color: var(--warning);" title="En tendance"></i>' : ''}
                                    </td>
                                    <td>${inf.source}</td>
                                    <td>${inf.total_mentions}</td>
                                    <td>${Utils.formatNumber(inf.total_engagement)}</td>
                                    <td>${inf.sentiment_score}/100</td>
                                    <td>${Utils.getRiskBadge(inf.risk_level)}</td>
                                    <td>
                                        <button class="btn-icon-small" onclick="Influencers.viewDetails('${inf.name}', '${inf.source}')" title="Détails">
                                            <i class="fas fa-eye"></i>
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        container.innerHTML = html;
    },

    renderMedia(media) {
        const container = document.getElementById('mediaGrid');
        if (!container) return;

        if (media.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--secondary); padding: 40px;">Aucun média officiel détecté</p>';
            return;
        }

        const html = `
            <div class="card">
                <div class="card-body">
                    <table>
                        <thead>
                            <tr>
                                <th>Nom</th>
                                <th>Source</th>
                                <th>Mentions</th>
                                <th>Engagement</th>
                                <th>Sentiment</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${media.map(inf => `
                                <tr>
                                    <td><strong>${inf.name}</strong></td>
                                    <td>${inf.source}</td>
                                    <td>${inf.total_mentions}</td>
                                    <td>${Utils.formatNumber(inf.total_engagement)}</td>
                                    <td>${inf.sentiment_score}/100</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        container.innerHTML = html;
    },

    async viewDetails(authorName, source) {
        try {
            Utils.showLoading('Chargement du rapport détaillé...');
            
            const report = await Utils.fetchAPI(`/api/advanced/influencers/${encodeURIComponent(authorName)}?source=${source}&days=30`);
            
            Utils.hideLoading();
            
            const modalBody = `
                <div style="max-height: 70vh; overflow-y: auto;">
                    <div class="card" style="margin-bottom: 20px;">
                        <div class="card-header">
                            <h4>Profil</h4>
                        </div>
                        <div class="card-body">
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                <div>
                                    <strong>Catégorie:</strong>
                                    <p>${report.influencer.category_label}</p>
                                </div>
                                <div>
                                    <strong>Niveau de risque:</strong>
                                    <p>${Utils.getRiskBadge(report.risk_assessment.level)}</p>
                                </div>
                                <div>
                                    <strong>Total mentions:</strong>
                                    <p>${report.activity.total_mentions}</p>
                                </div>
                                <div>
                                    <strong>Engagement total:</strong>
                                    <p>${Utils.formatNumber(report.activity.total_engagement)}</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="card" style="margin-bottom: 20px;">
                        <div class="card-header">
                            <h4>Analyse de Sentiment</h4>
                        </div>
                        <div class="card-body">
                            <div style="display: flex; justify-content: space-around; text-align: center;">
                                <div>
                                    <p style="font-size: 2rem; font-weight: 600; color: #10b981;">${report.sentiment.percentages.positive}%</p>
                                    <p>Positif</p>
                                </div>
                                <div>
                                    <p style="font-size: 2rem; font-weight: 600; color: #64748b;">${report.sentiment.percentages.neutral}%</p>
                                    <p>Neutre</p>
                                </div>
                                <div>
                                    <p style="font-size: 2rem; font-weight: 600; color: #ef4444;">${report.sentiment.percentages.negative}%</p>
                                    <p>Négatif</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h4>Publications Principales</h4>
                        </div>
                        <div class="card-body">
                            ${report.content_analysis.top_posts.map(post => `
                                <div style="padding: 10px 0; border-bottom: 1px solid var(--border);">
                                    <p style="font-weight: 500;">${post.title}</p>
                                    <div style="display: flex; gap: 15px; margin-top: 5px;">
                                        <small>Engagement: ${Utils.formatNumber(post.engagement)}</small>
                                        <small>${Utils.getSentimentBadge(post.sentiment)}</small>
                                        <small>${Utils.formatDate(post.date)}</small>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;

            Modal.show(`Rapport: ${authorName}`, modalBody);
        } catch (error) {
            Utils.hideLoading();
            Utils.showError('Impossible de charger le rapport détaillé');
            console.error('Error loading influencer details:', error);
        }
    }
};

// Module Analysis
const Analysis = {
    init() {
        document.getElementById('generateSummaryBtn')?.addEventListener('click', () => this.generateSummary());
        document.getElementById('detectAnomaliesBtn')?.addEventListener('click', () => this.detectAnomalies());
        document.getElementById('extractTopicsBtn')?.addEventListener('click', () => this.extractTopics());
        document.getElementById('analyzeNetworkBtn')?.addEventListener('click', () => this.analyzeNetwork());
        document.getElementById('closeAnalysisResults')?.addEventListener('click', () => this.hideResults());
    },

    async generateSummary() {
        try {
            Utils.showLoading('Génération du résumé hiérarchique...');

            const keywords = await Utils.fetchAPI('/api/keywords?active_only=true');
            const keywordIds = keywords.map(k => k.id);

            if (keywordIds.length === 0) {
                Utils.hideLoading();
                Utils.showError('Aucun mot-clé actif pour l\'analyse');
                return;
            }

            const result = await Utils.fetchAPI(`/api/advanced/summarize?keyword_ids=${keywordIds.join(',')}&days=30`, {
                method: 'POST'
            });

            Utils.hideLoading();

            const html = `
                <div style="max-height: 60vh; overflow-y: auto;">
                    <div class="card" style="margin-bottom: 20px;">
                        <div class="card-header">
                            <h4>Synthèse Exécutive</h4>
                        </div>
                        <div class="card-body">
                            <p style="line-height: 1.8; white-space: pre-wrap;">${result.summary}</p>
                        </div>
                    </div>

                    <div class="card" style="margin-bottom: 20px;">
                        <div class="card-header">
                            <h4>Insights Clés</h4>
                        </div>
                        <div class="card-body">
                            <ul style="line-height: 2;">
                                ${result.key_insights.map(insight => `<li>${insight}</li>`).join('')}
                            </ul>
                        </div>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div class="card">
                            <div class="card-header">
                                <h4>Analyse de Sentiment</h4>
                            </div>
                            <div class="card-body">
                                <p><strong>Positif:</strong> ${result.sentiment_analysis.percentages.positive}%</p>
                                <p><strong>Neutre:</strong> ${result.sentiment_analysis.percentages.neutral}%</p>
                                <p><strong>Négatif:</strong> ${result.sentiment_analysis.percentages.negative}%</p>
                            </div>
                        </div>

                        <div class="card">
                            <div class="card-header">
                                <h4>Thèmes Principaux</h4>
                            </div>
                            <div class="card-body">
                                ${result.themes.map(theme => `<span class="badge info" style="margin: 5px;">${theme}</span>`).join('')}
                            </div>
                        </div>
                    </div>

                    <div style="margin-top: 20px; padding: 15px; background: var(--light); border-radius: 8px;">
                        <p><strong>Contenus analysés:</strong> ${result.total_contents}</p>
                        <p><strong>Temps de traitement:</strong> ${result.processing_time.toFixed(1)}s</p>
                    </div>
                </div>
            `;

            this.showResults('Résumé Hiérarchique IA', html);
        } catch (error) {
            Utils.hideLoading();
            console.error('Error generating summary:', error);
        }
    },

    async detectAnomalies() {
        try {
            Utils.showLoading('Détection des anomalies...');

            const keywords = await Utils.fetchAPI('/api/keywords?active_only=true');
            if (keywords.length === 0) {
                Utils.hideLoading();
                Utils.showError('Aucun mot-clé actif');
                return;
            }

            const keywordId = keywords[0].id;
            const result = await Utils.fetchAPI(`/api/advanced/anomalies?keyword_id=${keywordId}&days=30&sensitivity=2.0`);

            Utils.hideLoading();

            if (result.anomalies.length === 0) {
                Utils.showSuccess('Aucune anomalie détectée');
                return;
            }

            const html = `
                <div style="max-height: 60vh; overflow-y: auto;">
                    <div style="margin-bottom: 20px;">
                        <p><strong>Total anomalies:</strong> ${result.total_found}</p>
                        <p><strong>Critiques:</strong> ${result.critical_count}</p>
                        <p><strong>Élevées:</strong> ${result.high_count}</p>
                    </div>

                    ${result.anomalies.map(anomaly => `
                        <div class="card" style="margin-bottom: 15px;">
                            <div class="card-body">
                                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                                    <h4 style="margin: 0;">${anomaly.type.replace('_', ' ')}</h4>
                                    ${Utils.getRiskBadge(anomaly.severity)}
                                </div>
                                <p>${anomaly.description}</p>
                                <small style="color: var(--secondary);">${Utils.formatDate(anomaly.timestamp)}</small>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;

            this.showResults('Anomalies Détectées', html);
        } catch (error) {
            Utils.hideLoading();
            console.error('Error detecting anomalies:', error);
        }
    },

    async extractTopics() {
        try {
            Utils.showLoading('Extraction des topics...');

            const keywords = await Utils.fetchAPI('/api/keywords?active_only=true');
            if (keywords.length === 0) {
                Utils.hideLoading();
                Utils.showError('Aucun mot-clé actif');
                return;
            }

            const keywordId = keywords[0].id;
            const result = await Utils.fetchAPI(`/api/advanced/topics?keyword_id=${keywordId}&days=30&min_topic_size=10`);

            Utils.hideLoading();

            if (result.topics.length === 0) {
                Utils.showError('Pas assez de données pour extraire des topics');
                return;
            }

            const html = `
                <div style="max-height: 60vh; overflow-y: auto;">
                    <div style="margin-bottom: 20px;">
                        <p><strong>Topics identifiés:</strong> ${result.total_topics}</p>
                        <p><strong>Documents analysés:</strong> ${result.total_documents}</p>
                    </div>

                    ${result.topics.map(topic => `
                        <div class="card" style="margin-bottom: 15px;">
                            <div class="card-header">
                                <h4>Topic ${topic.topic_id} (${topic.size} documents)</h4>
                            </div>
                            <div class="card-body">
                                <div style="margin-bottom: 10px;">
                                    <strong>Mots-clés:</strong>
                                    <div>
                                        ${topic.keywords.map(kw => `<span class="badge info" style="margin: 3px;">${kw}</span>`).join('')}
                                    </div>
                                </div>
                                <div>
                                    <strong>Score de cohérence:</strong> ${topic.coherence_score.toFixed(2)}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;

            this.showResults('Topics Extraits', html);
        } catch (error) {
            Utils.hideLoading();
            console.error('Error extracting topics:', error);
        }
    },

    async analyzeNetwork() {
        try {
            Utils.showLoading('Analyse du réseau d\'influence...');

            const keywords = await Utils.fetchAPI('/api/keywords?active_only=true');
            if (keywords.length === 0) {
                Utils.hideLoading();
                Utils.showError('Aucun mot-clé actif');
                return;
            }

            const keywordId = keywords[0].id;
            const result = await Utils.fetchAPI(`/api/advanced/network?keyword_id=${keywordId}&days=30`);

            Utils.hideLoading();

            const html = `
                <div style="max-height: 60vh; overflow-y: auto;">
                    <div class="card" style="margin-bottom: 20px;">
                        <div class="card-header">
                            <h4>Métriques du Réseau</h4>
                        </div>
                        <div class="card-body">
                            <p><strong>Nœuds (influenceurs):</strong> ${result.metrics.total_nodes}</p>
                            <p><strong>Relations:</strong> ${result.metrics.total_edges}</p>
                            <p><strong>Communautés:</strong> ${result.metrics.num_communities}</p>
                            <p><strong>Densité:</strong> ${(result.metrics.density * 100).toFixed(2)}%</p>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h4>Influenceurs Centraux</h4>
                        </div>
                        <div class="card-body">
                            <ul>
                                ${result.central_nodes.map(node => `<li>${node}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            `;

            this.showResults('Réseau d\'Influence', html);
        } catch (error) {
            Utils.hideLoading();
            console.error('Error analyzing network:', error);
        }
    },

    showResults(title, html) {
        const resultsDiv = document.getElementById('analysisResults');
        const titleEl = document.getElementById('analysisResultsTitle');
        const contentEl = document.getElementById('analysisResultsContent');

        titleEl.textContent = title;
        contentEl.innerHTML = html;
        resultsDiv.style.display = 'block';

        resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },

    hideResults() {
        document.getElementById('analysisResults').style.display = 'none';
    }
};

// Module Reports
const Reports = {
    async init() {
        try {
            const keywords = await Utils.fetchAPI('/api/keywords?active_only=true');
            const select = document.getElementById('reportKeywords');
            
            if (select) {
                select.innerHTML = keywords.map(k => 
                    `<option value="${k.id}">${k.keyword}</option>`
                ).join('');
            }
        } catch (error) {
            console.error('Error loading keywords for report:', error);
        }

        document.getElementById('reportForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.generateReport();
        });
    },

    async generateReport() {
        try {
            Utils.showLoading('Génération du rapport PDF...');

            const select = document.getElementById('reportKeywords');
            const keywordIds = Array.from(select.selectedOptions).map(opt => opt.value);
            const period = document.getElementById('reportPeriod').value;
            const sections = Array.from(document.querySelectorAll('input[name="section"]:checked')).map(cb => cb.value);

            if (keywordIds.length === 0) {
                Utils.hideLoading();
                Utils.showError('Sélectionnez au moins un mot-clé');
                return;
            }

            // TODO: Implémenter l'endpoint de génération de rapport PDF
            // Pour l'instant, on génère un rapport JSON
            const result = await Utils.fetchAPI(`/api/advanced/summarize?keyword_ids=${keywordIds.join(',')}&days=${period}`, {
                method: 'POST'
            });

            Utils.hideLoading();
            Utils.showSuccess('Rapport généré avec succès (JSON)');
            
            // Télécharger le JSON
            const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `rapport-${new Date().toISOString().split('T')[0]}.json`;
            a.click();

        } catch (error) {
            Utils.hideLoading();
            console.error('Error generating report:', error);
        }
    }
};

// Module Settings
const Settings = {
    async load() {
        try {
            // Charger le statut des services IA
            const aiHealth = await Utils.fetchAPI('/api/advanced/ai/health');
            this.renderAIStatus(aiHealth);

            // Charger les sources disponibles
            const sources = await Utils.fetchAPI('/api/sources');
            AppState.sources = sources.sources;
            this.renderSourcesStatus(sources.sources);
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    },

    renderAIStatus(health) {
        const container = document.getElementById('aiServicesStatus');
        if (!container) return;

        const html = `
            <div style="margin-bottom: 20px;">
                <h4 style="margin-bottom: 10px;">Ordre de priorité:</h4>
                <ol style="line-height: 2; padding-left: 20px;">
                    ${health.priority_order.map(service => `<li>${service}</li>`).join('')}
                </ol>
            </div>
            <div style="margin-bottom: 15px;">
                <h4 style="margin-bottom: 10px;">Statut des services:</h4>
                ${Object.entries(health.services).map(([name, status]) => `
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border);">
                        <span>${status.label}</span>
                        <span class="badge ${status.status === 'healthy' ? 'success' : 'danger'}">
                            ${status.status === 'healthy' ? '✓ Opérationnel' : '✗ Indisponible'}
                        </span>
                    </div>
                    ${status.error ? `<small style="color: var(--danger);">Erreur: ${status.error}</small>` : ''}
                `).join('')}
            </div>
        `;

        container.innerHTML = html;
    },

    renderSourcesStatus(sources) {
        const container = document.getElementById('sourcesStatus');
        if (!container) return;

        const html = sources.map(source => `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--border);">
                <div>
                    <strong>${source.name}</strong>
                    <p style="font-size: 0.85rem; color: var(--secondary); margin-top: 3px;">${source.description}</p>
                    <small style="color: var(--secondary);">Limite: ${source.limit}</small>
                    ${source.enhanced ? '<span class="badge info" style="margin-left: 10px;">Enhanced</span>' : ''}
                </div>
                <span class="badge ${source.enabled ? 'success' : ''}">
                    ${source.enabled ? '✓ Activé' : 'Désactivé'}
                </span>
            </div>
        `).join('');

        container.innerHTML = html;
    }
};

// Module Modal
const Modal = {
    show(title, body) {
        const overlay = document.getElementById('modalOverlay');
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');

        modalTitle.textContent = title;
        modalBody.innerHTML = body;
        overlay.classList.add('active');

        const closeBtn = overlay.querySelector('.modal-close');
        closeBtn.onclick = () => this.hide();

        overlay.onclick = (e) => {
            if (e.target === overlay) {
                this.hide();
            }
        };
    },

    hide() {
        document.getElementById('modalOverlay').classList.remove('active');
    }
};

// Initialisation de la gestion des tabs
function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
                if (content.dataset.content === tabName) {
                    content.classList.add('active');
                }
            });
        });
    });
}

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Brand Monitor initialized');
    Navigation.init();
    initTabs();
    
    // Événements des boutons globaux
    document.getElementById('addKeywordBtn')?.addEventListener('click', () => {
        Keywords.showAddModal();
    });

    document.getElementById('refreshData')?.addEventListener('click', () => {
        Navigation.loadViewData(AppState.currentView);
    });

    document.getElementById('collectNowBtn')?.addEventListener('click', async () => {
        try {
            Utils.showLoading('Collecte en cours...');
            await Utils.fetchAPI('/api/collect', {
                method: 'POST',
                body: JSON.stringify({})
            });
            Utils.hideLoading();
            Utils.showSuccess('Collecte lancée pour tous les mots-clés actifs');
            setTimeout(() => Mentions.load(), 3000);
        } catch (error) {
            Utils.hideLoading();
        }
    });

    document.getElementById('applyFilters')?.addEventListener('click', () => {
        Mentions.applyFilters();
    });

    document.getElementById('refreshInfluencersBtn')?.addEventListener('click', () => {
        Influencers.load();
    });

    // Test des services IA
    document.getElementById('testAiBtn')?.addEventListener('click', async () => {
        try {
            Utils.showLoading('Test des services IA...');
            const result = await Utils.fetchAPI('/api/advanced/ai/test?prompt=Test de connexion&max_tokens=50', {
                method: 'POST'
            });
            Utils.hideLoading();
            Utils.showSuccess(`Service ${result.service_used} opérationnel: ${result.text.substring(0, 50)}...`);
        } catch (error) {
            Utils.hideLoading();
        }
    });
});

// Styles pour les animations (ajouter dans le head si nécessaire)
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