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
            case 'channels':
                await Channels.load();
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

// ============ MODULE CHANNELS ============
const Channels = {
    currentChannels: [],
    charts: {},

    async load() {
        try {
            Utils.showLoading('Chargement des channels...');

            // Charger les channels
            const channels = await Utils.fetchAPI('/api/channels/?active_only=false');
            this.currentChannels = channels;

            // Mettre à jour les stats
            this.updateStats(channels);

            // Afficher la liste
            this.renderChannelsList(channels);

            // Charger le monitoring si on est sur cet onglet
            const activeTab = document.querySelector('.tab.active[data-tab="channels-monitoring"]');
            if (activeTab) {
                await this.loadMonitoring();
            }

            Utils.hideLoading();
        } catch (error) {
            Utils.hideLoading();
            console.error('Error loading channels:', error);
        }
    },

    updateStats(channels) {
        const activeChannels = channels.filter(ch => ch.active).length;
        const totalItems = channels.reduce((sum, ch) => sum + (ch.total_items_collected || 0), 0);
        const alertsActive = channels.filter(ch => ch.enable_email_alerts).length;

        document.getElementById('totalChannels').textContent = Utils.formatNumber(activeChannels);
        document.getElementById('totalChannelItems').textContent = Utils.formatNumber(totalItems);
        document.getElementById('channelAlerts').textContent = Utils.formatNumber(alertsActive);

        // Prochaine collecte
        const nextCheck = channels
            .filter(ch => ch.active && ch.last_check)
            .map(ch => {
                const lastCheck = new Date(ch.last_check);
                const nextCheck = new Date(lastCheck.getTime() + ch.check_interval_minutes * 60000);
                return nextCheck;
            })
            .sort((a, b) => a - b)[0];

        if (nextCheck) {
            const now = new Date();
            const diff = Math.max(0, Math.floor((nextCheck - now) / 60000));
            document.getElementById('nextChannelCheck').textContent = `${diff}min`;
        } else {
            document.getElementById('nextChannelCheck').textContent = '-';
        }
    },

    renderChannelsList(channels) {
        const container = document.getElementById('channelsTable');
        if (!container) return;

        if (channels.length === 0) {
            container.innerHTML = `
                <p style="text-align: center; color: var(--secondary); padding: 40px;">
                    Aucun channel configuré. Cliquez sur "Nouveau Channel" pour commencer.
                </p>
            `;
            return;
        }

        const html = `
            <table>
                <thead>
                    <tr>
                        <th>Nom</th>
                        <th>Type</th>
                        <th>Statut</th>
                        <th>Intervalle</th>
                        <th>Dernière collecte</th>
                        <th>Items</th>
                        <th>Alertes</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${channels.map(ch => `
                        <tr>
                            <td>
                                <strong>${ch.name}</strong>
                                <br>
                                <small style="color: var(--secondary);">${this.formatChannelId(ch.channel_id)}</small>
                            </td>
                            <td>${this.getChannelTypeBadge(ch.channel_type)}</td>
                            <td>${ch.active ? '<span class="badge success">Actif</span>' : '<span class="badge">Inactif</span>'}</td>
                            <td>${ch.check_interval_minutes} min</td>
                            <td>${Utils.formatDate(ch.last_check) || 'Jamais'}</td>
                            <td>${Utils.formatNumber(ch.total_items_collected || 0)}</td>
                            <td>${ch.enable_email_alerts ? '🔔' : '🔕'}</td>
                            <td>
                                <button class="btn-icon-small" onclick="Channels.viewChannel(${ch.id})" title="Voir">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="btn-icon-small" onclick="Channels.collectChannel(${ch.id})" title="Collecter">
                                    <i class="fas fa-sync-alt"></i>
                                </button>
                                <button class="btn-icon-small" onclick="Channels.editChannel(${ch.id})" title="Éditer">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn-icon-small" onclick="Channels.deleteChannel(${ch.id})" title="Supprimer">
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

    getChannelTypeBadge(type) {
        const badges = {
            'youtube_rss': '<span class="badge danger"><i class="fab fa-youtube"></i> YouTube</span>',
            'telegram': '<span class="badge info"><i class="fab fa-telegram"></i> Telegram</span>',
            'whatsapp': '<span class="badge success"><i class="fab fa-whatsapp"></i> WhatsApp</span>',
            'web_rss': '<span class="badge warning"><i class="fas fa-rss"></i> RSS</span>'
        };
        return badges[type] || `<span class="badge">${type}</span>`;
    },

    formatChannelId(channelId) {
        if (channelId.length > 50) {
            return channelId.substring(0, 47) + '...';
        }
        return channelId;
    },

    showAddChannelModal() {
        const modalBody = `
            <form id="addChannelForm">
                <div class="form-group">
                    <label>Type de Channel *</label>
                    <select id="channelType" class="form-control" required onchange="Channels.updateChannelForm()">
                        <option value="">-- Sélectionner --</option>
                        <option value="youtube_rss">📺 YouTube (RSS)</option>
                        <option value="telegram">✈️ Telegram</option>
                        <option value="whatsapp">💬 WhatsApp</option>
                        <option value="web_rss">🌐 Flux RSS</option>
                    </select>
                </div>

                <div id="channelSpecificFields"></div>

                <div class="form-group">
                    <label>Nom du channel *</label>
                    <input type="text" id="channelName" class="form-control" placeholder="Ex: France 24 Afrique" required>
                </div>

                <div class="form-group">
                    <label>Intervalle de collecte (minutes) *</label>
                    <input type="number" id="channelInterval" class="form-control" value="60" min="5" max="1440" required>
                    <small>Entre 5 et 1440 minutes (24h)</small>
                </div>

                <div class="form-group">
                    <label class="checkbox">
                        <input type="checkbox" id="enableAlerts">
                        <span>Activer les alertes email</span>
                    </label>
                </div>

                <div id="alertFields" style="display: none;">
                    <div class="form-group">
                        <label>Mots-clés d'alerte (séparés par des virgules)</label>
                        <input type="text" id="alertKeywords" class="form-control" placeholder="urgent, breaking, important">
                    </div>

                    <div class="form-group">
                        <label>Emails de notification (séparés par des virgules)</label>
                        <input type="text" id="alertEmails" class="form-control" placeholder="admin@example.com">
                    </div>
                </div>

                <div class="form-group full-width">
                    <button type="submit" class="btn btn-primary btn-block">
                        <i class="fas fa-plus"></i>
                        Créer le Channel
                    </button>
                </div>
            </form>
        `;

        Modal.show('Nouveau Channel', modalBody);

        // Gérer l'affichage des champs d'alerte
        document.getElementById('enableAlerts').addEventListener('change', (e) => {
            document.getElementById('alertFields').style.display = e.target.checked ? 'block' : 'none';
        });

        document.getElementById('addChannelForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.createChannel();
        });
    },

    updateChannelForm() {
        const type = document.getElementById('channelType').value;
        const container = document.getElementById('channelSpecificFields');

        if (!type) {
            container.innerHTML = '';
            return;
        }

        let html = '';

        switch (type) {
            case 'youtube_rss':
                html = `
                    <div class="form-group">
                        <label>ID de la chaîne YouTube *</label>
                        <input type="text" id="channelId" class="form-control" 
                               placeholder="UCXuqSBlHAE6Xw-yeJA0Tunw" required>
                        <small>
                            Trouvez l'ID dans l'URL : youtube.com/channel/<strong>ID_ICI</strong><br>
                            Ou utilisez la recherche ci-dessous
                        </small>
                    </div>
                    <div class="form-group">
                        <label>Ou rechercher par nom</label>
                        <div style="display: flex; gap: 10px;">
                            <input type="text" id="youtubeSearch" class="form-control" placeholder="France 24">
                            <button type="button" class="btn btn-secondary" onclick="Channels.searchYouTube()">
                                <i class="fas fa-search"></i>
                            </button>
                        </div>
                        <div id="youtubeSearchResults"></div>
                    </div>
                `;
                break;

            case 'telegram':
                html = `
                    <div class="form-group">
                        <label>Username du canal Telegram *</label>
                        <input type="text" id="channelId" class="form-control" 
                               placeholder="@france24_fr" required>
                        <small>Format : @username ou simplement username</small>
                    </div>
                `;
                break;

            case 'whatsapp':
                html = `
                    <div class="form-group">
                        <label>ID du groupe WhatsApp *</label>
                        <input type="text" id="channelId" class="form-control" 
                               placeholder="120363xxx@g.us" required>
                        <small>
                            Format : numéro@g.us<br>
                            ⚠️ WhatsApp Bridge doit être connecté
                        </small>
                    </div>
                    <div class="form-group">
                        <button type="button" class="btn btn-secondary btn-block" onclick="Channels.checkWhatsAppStatus()">
                            <i class="fas fa-info-circle"></i>
                            Vérifier WhatsApp Bridge
                        </button>
                    </div>
                `;
                break;

            case 'web_rss':
                html = `
                    <div class="form-group">
                        <label>URL du flux RSS *</label>
                        <input type="text" id="channelId" class="form-control" 
                               placeholder="https://www.france24.com/fr/rss" required>
                        <small>URL complète du flux RSS/Atom</small>
                    </div>
                    <div class="form-group">
                        <label>Ou découvrir automatiquement</label>
                        <div style="display: flex; gap: 10px;">
                            <input type="text" id="websiteUrl" class="form-control" placeholder="https://www.france24.com">
                            <button type="button" class="btn btn-secondary" onclick="Channels.discoverRSS()">
                                <i class="fas fa-search"></i>
                            </button>
                        </div>
                        <div id="rssDiscoverResults"></div>
                    </div>
                `;
                break;
        }

        container.innerHTML = html;
    },

    async searchYouTube() {
        const query = document.getElementById('youtubeSearch').value.trim();
        if (!query) {
            Utils.showError('Entrez un terme de recherche');
            return;
        }

        try {
            Utils.showLoading('Recherche YouTube...');
            const result = await Utils.fetchAPI(`/api/channels/discover/youtube?search=${encodeURIComponent(query)}`);
            Utils.hideLoading();

            const resultsDiv = document.getElementById('youtubeSearchResults');
            
            if (result.found && result.info) {
                resultsDiv.innerHTML = `
                    <div style="margin-top: 10px; padding: 10px; background: var(--light); border-radius: 5px;">
                        <strong>${result.info.title || 'Chaîne trouvée'}</strong><br>
                        <small>ID: ${result.channel_id}</small><br>
                        <button type="button" class="btn btn-primary" style="margin-top: 10px;" 
                                onclick="document.getElementById('channelId').value='${result.channel_id}'; 
                                         document.getElementById('channelName').value='${(result.info.title || '').replace(/'/g, "\\'")}';
                                         document.getElementById('youtubeSearchResults').innerHTML='';">
                            <i class="fas fa-check"></i> Utiliser cette chaîne
                        </button>
                    </div>
                `;
            } else {
                resultsDiv.innerHTML = '<p style="color: var(--danger); margin-top: 10px;">Aucun résultat trouvé</p>';
            }
        } catch (error) {
            Utils.hideLoading();
        }
    },

    async discoverRSS() {
        const url = document.getElementById('websiteUrl').value.trim();
        if (!url) {
            Utils.showError('Entrez une URL');
            return;
        }

        try {
            Utils.showLoading('Recherche du flux RSS...');
            const result = await Utils.fetchAPI(`/api/channels/discover/rss?website_url=${encodeURIComponent(url)}`);
            Utils.hideLoading();

            const resultsDiv = document.getElementById('rssDiscoverResults');
            
            if (result.found) {
                resultsDiv.innerHTML = `
                    <div style="margin-top: 10px; padding: 10px; background: var(--light); border-radius: 5px;">
                        <strong>Flux RSS découvert !</strong><br>
                        <small>${result.feed_url}</small><br>
                        <button type="button" class="btn btn-primary" style="margin-top: 10px;" 
                                onclick="document.getElementById('channelId').value='${result.feed_url}'; 
                                         document.getElementById('rssDiscoverResults').innerHTML='';">
                            <i class="fas fa-check"></i> Utiliser ce flux
                        </button>
                    </div>
                `;
            } else {
                resultsDiv.innerHTML = '<p style="color: var(--danger); margin-top: 10px;">Aucun flux RSS trouvé</p>';
            }
        } catch (error) {
            Utils.hideLoading();
        }
    },

    async checkWhatsAppStatus() {
        try {
            Utils.showLoading('Vérification WhatsApp Bridge...');
            
            // Essayer de contacter le bridge WhatsApp (port 3500)
            const response = await fetch('http://localhost:3500/health');
            const data = await response.json();
            
            Utils.hideLoading();

            if (data.connection_state === 'connected') {
                Utils.showSuccess('✅ WhatsApp Bridge connecté');
                
                // Charger les groupes
                const groupsResponse = await fetch('http://localhost:3500/groups');
                const groupsData = await groupsResponse.json();
                
                if (groupsData.groups && groupsData.groups.length > 0) {
                    const select = document.createElement('select');
                    select.className = 'form-control';
                    select.style.marginTop = '10px';
                    
                    groupsData.groups.forEach(group => {
                        const option = document.createElement('option');
                        option.value = group.id;
                        option.textContent = `${group.name} (${group.participants_count} membres)`;
                        select.appendChild(option);
                    });
                    
                    select.addEventListener('change', () => {
                        document.getElementById('channelId').value = select.value;
                    });
                    
                    document.getElementById('channelId').parentElement.appendChild(select);
                }
            } else {
                Utils.showError(`WhatsApp Bridge: ${data.connection_state}`);
            }
        } catch (error) {
            Utils.hideLoading();
            Utils.showError('WhatsApp Bridge non accessible. Assurez-vous qu\'il est démarré.');
        }
    },

    async createChannel() {
        const type = document.getElementById('channelType').value;
        const channelId = document.getElementById('channelId').value.trim();
        const name = document.getElementById('channelName').value.trim();
        const interval = parseInt(document.getElementById('channelInterval').value);
        const enableAlerts = document.getElementById('enableAlerts').checked;

        if (!type || !channelId || !name) {
            Utils.showError('Tous les champs obligatoires doivent être remplis');
            return;
        }

        const data = {
            name: name,
            channel_type: type,
            channel_id: channelId,
            check_interval_minutes: interval,
            enable_email_alerts: enableAlerts
        };

        if (enableAlerts) {
            const keywords = document.getElementById('alertKeywords').value.trim();
            const emails = document.getElementById('alertEmails').value.trim();
            
            if (keywords) {
                data.alert_keywords = keywords.split(',').map(k => k.trim()).filter(k => k);
            }
            if (emails) {
                data.alert_emails = emails.split(',').map(e => e.trim()).filter(e => e);
            }
        }

        try {
            Utils.showLoading('Création du channel...');
            await Utils.fetchAPI('/api/channels/', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            Utils.hideLoading();
            Modal.hide();
            Utils.showSuccess('Channel créé avec succès');
            this.load();
        } catch (error) {
            Utils.hideLoading();
        }
    },

    async collectChannel(channelId) {
        try {
            Utils.showLoading('Collecte en cours...');
            await Utils.fetchAPI(`/api/channels/${channelId}/collect`, {
                method: 'POST'
            });
            Utils.hideLoading();
            Utils.showSuccess('Collecte lancée avec succès');
            setTimeout(() => this.load(), 2000);
        } catch (error) {
            Utils.hideLoading();
        }
    },

    async collectAllChannels() {
        try {
            Utils.showLoading('Collecte de tous les channels...');
            await Utils.fetchAPI('/api/channels/collect-all', {
                method: 'POST'
            });
            Utils.hideLoading();
            Utils.showSuccess('Collecte lancée pour tous les channels actifs');
            setTimeout(() => this.load(), 3000);
        } catch (error) {
            Utils.hideLoading();
        }
    },

    async viewChannel(channelId) {
        try {
            Utils.showLoading('Chargement des détails...');
            const channel = await Utils.fetchAPI(`/api/channels/${channelId}`);
            const stats = await Utils.fetchAPI(`/api/channels/${channelId}/stats?days=7`);
            const items = await Utils.fetchAPI(`/api/channels/${channelId}/items?limit=20`);
            Utils.hideLoading();

            const modalBody = `
                <div style="max-height: 70vh; overflow-y: auto;">
                    <div class="card" style="margin-bottom: 20px;">
                        <div class="card-header">
                            <h4>Informations du Channel</h4>
                        </div>
                        <div class="card-body">
                            <p><strong>Nom:</strong> ${channel.name}</p>
                            <p><strong>Type:</strong> ${this.getChannelTypeBadge(channel.channel_type)}</p>
                            <p><strong>ID:</strong> <code>${channel.channel_id}</code></p>
                            <p><strong>Statut:</strong> ${channel.active ? '<span class="badge success">Actif</span>' : '<span class="badge">Inactif</span>'}</p>
                            <p><strong>Intervalle:</strong> ${channel.check_interval_minutes} minutes</p>
                            <p><strong>Alertes:</strong> ${channel.enable_email_alerts ? '🔔 Activées' : '🔕 Désactivées'}</p>
                        </div>
                    </div>

                    <div class="card" style="margin-bottom: 20px;">
                        <div class="card-header">
                            <h4>Statistiques (7 derniers jours)</h4>
                        </div>
                        <div class="card-body">
                            <p><strong>Items collectés:</strong> ${stats.stats.total_items}</p>
                            <p><strong>Alertes déclenchées:</strong> ${stats.stats.alert_items}</p>
                            <p><strong>Dernière collecte:</strong> ${Utils.formatDate(stats.stats.last_check) || 'Jamais'}</p>
                            ${stats.stats.sentiment_distribution ? `
                                <p><strong>Sentiments:</strong></p>
                                <ul>
                                    <li>Positif: ${stats.stats.sentiment_distribution.positive || 0}</li>
                                    <li>Neutre: ${stats.stats.sentiment_distribution.neutral || 0}</li>
                                    <li>Négatif: ${stats.stats.sentiment_distribution.negative || 0}</li>
                                </ul>
                            ` : ''}
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h4>Contenus Récents (${items.items.length})</h4>
                        </div>
                        <div class="card-body">
                            ${items.items.length > 0 ? `
                                ${items.items.map(item => `
                                    <div style="padding: 10px 0; border-bottom: 1px solid var(--border);">
                                        <p style="font-weight: 500;">${item.title}</p>
                                        <div style="display: flex; gap: 15px; margin-top: 5px;">
                                            <small>${Utils.formatDate(item.published_at)}</small>
                                            <small>${item.sentiment ? Utils.getSentimentBadge(item.sentiment) : ''}</small>
                                            ${item.alert_triggered ? '<small>🔔 Alerte</small>' : ''}
                                        </div>
                                    </div>
                                `).join('')}
                            ` : '<p style="color: var(--secondary);">Aucun contenu collecté</p>'}
                        </div>
                    </div>
                </div>
            `;

            Modal.show(`Channel: ${channel.name}`, modalBody);
        } catch (error) {
            Utils.hideLoading();
        }
    },

    async deleteChannel(channelId) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer ce channel ?')) {
            return;
        }

        try {
            await Utils.fetchAPI(`/api/channels/${channelId}`, {
                method: 'DELETE'
            });
            Utils.showSuccess('Channel supprimé');
            this.load();
        } catch (error) {
            console.error('Error deleting channel:', error);
        }
    },

    async editChannel(channelId) {
        try {
            const channel = await Utils.fetchAPI(`/api/channels/${channelId}`);
            
            const modalBody = `
                <form id="editChannelForm">
                    <div class="form-group">
                        <label>Nom du channel *</label>
                        <input type="text" id="editChannelName" class="form-control" value="${channel.name}" required>
                    </div>

                    <div class="form-group">
                        <label>Intervalle (minutes) *</label>
                        <input type="number" id="editChannelInterval" class="form-control" 
                               value="${channel.check_interval_minutes}" min="5" max="1440" required>
                    </div>

                    <div class="form-group">
                        <label class="checkbox">
                            <input type="checkbox" id="editChannelActive" ${channel.active ? 'checked' : ''}>
                            <span>Channel actif</span>
                        </label>
                    </div>

                    <div class="form-group">
                        <label class="checkbox">
                            <input type="checkbox" id="editEnableAlerts" ${channel.enable_email_alerts ? 'checked' : ''}>
                            <span>Activer les alertes email</span>
                        </label>
                    </div>

                    <div class="form-group full-width">
                        <button type="submit" class="btn btn-primary btn-block">
                            <i class="fas fa-save"></i>
                            Enregistrer
                        </button>
                    </div>
                </form>
            `;

            Modal.show(`Éditer: ${channel.name}`, modalBody);

            document.getElementById('editChannelForm').addEventListener('submit', async (e) => {
                e.preventDefault();

                const data = {
                    name: document.getElementById('editChannelName').value.trim(),
                    check_interval_minutes: parseInt(document.getElementById('editChannelInterval').value),
                    active: document.getElementById('editChannelActive').checked,
                    enable_email_alerts: document.getElementById('editEnableAlerts').checked
                };

                try {
                    Utils.showLoading('Mise à jour...');
                    await Utils.fetchAPI(`/api/channels/${channelId}`, {
                        method: 'PUT',
                        body: JSON.stringify(data)
                    });
                    Utils.hideLoading();
                    Modal.hide();
                    Utils.showSuccess('Channel mis à jour');
                    this.load();
                } catch (error) {
                    Utils.hideLoading();
                }
            });
        } catch (error) {
            console.error('Error loading channel:', error);
        }
    },

    async loadMonitoring() {
        try {
            // Charger le planning de collecte
            const schedule = await Utils.fetchAPI('/api/channels/monitoring/schedule');
            this.renderSchedule(schedule);

            // Charger les stats d'activité
            // TODO: Créer un graphique d'activité si endpoint disponible
        } catch (error) {
            console.error('Error loading monitoring:', error);
        }
    },

    renderSchedule(schedule) {
        const container = document.getElementById('channelSchedule');
        if (!container) return;

        if (!schedule.channels || schedule.channels.length === 0) {
            container.innerHTML = '<p style="color: var(--secondary);">Aucun channel actif</p>';
            return;
        }

        const html = Object.entries(schedule.channels)
            .sort((a, b) => {
                const dateA = new Date(a[1].next_check);
                const dateB = new Date(b[1].next_check);
                return dateA - dateB;
            })
            .map(([name, info]) => {
                const nextCheck = new Date(info.next_check);
                const now = new Date();
                const isImmediate = info.next_check === 'Immédiat';
                const isOverdue = !isImmediate && nextCheck < now;

                return `
                    <div style="padding: 10px; margin-bottom: 10px; background: var(--light); border-radius: 5px;">
                        <strong>${name}</strong><br>
                        <small>
                            Dernière: ${info.last_check ? Utils.formatDate(info.last_check) : 'Jamais'}<br>
                            Prochaine: <span style="color: ${isOverdue ? 'var(--danger)' : 'var(--primary)'};">
                                ${isImmediate ? 'Immédiat' : Utils.formatDate(info.next_check)}
                            </span><br>
                            Intervalle: ${info.interval_minutes}min
                        </small>
                    </div>
                `;
            })
            .join('');

        container.innerHTML = html;
    },

    async loadPopularChannels() {
        try {
            const presets = await Utils.fetchAPI('/api/channels/presets/popular');
            this.renderPopularChannels(presets);
        } catch (error) {
            console.error('Error loading popular channels:', error);
        }
    },

    renderPopularChannels(presets) {
        const container = document.getElementById('popularChannelsGrid');
        if (!container) return;

        const html = Object.entries(presets).map(([category, channels]) => `
            <div class="card" style="margin-bottom: 20px;">
                <div class="card-header">
                    <h3>${category.replace(/_/g, ' ').toUpperCase()}</h3>
                </div>
                <div class="card-body">
                    ${channels.map(ch => `
                        <div style="padding: 10px; margin-bottom: 10px; background: var(--light); border-radius: 5px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>${ch.name}</strong><br>
                                <small>${ch.channel_id}</small>
                                ${ch.description ? `<br><small style="color: var(--secondary);">${ch.description}</small>` : ''}
                            </div>
                            <button class="btn btn-primary" onclick='Channels.quickAddChannel(${JSON.stringify(ch)})'>
                                <i class="fas fa-plus"></i>
                                Ajouter
                            </button>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    },

    async quickAddChannel(channelData) {
        const name = prompt(`Nom du channel:`, channelData.name);
        if (!name) return;

        const data = {
            name: name,
            channel_type: channelData.type,
            channel_id: channelData.channel_id,
            check_interval_minutes: 60,
            enable_email_alerts: false
        };

        try {
            Utils.showLoading('Ajout du channel...');
            await Utils.fetchAPI('/api/channels/', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            Utils.hideLoading();
            Utils.showSuccess('Channel ajouté avec succès');
            this.load();
        } catch (error) {
            Utils.hideLoading();
        }
    },

    applyFilters() {
        const typeFilter = document.getElementById('channelTypeFilter').value;
        const statusFilter = document.getElementById('channelStatusFilter').value;

        let filtered = this.currentChannels;

        if (typeFilter) {
            filtered = filtered.filter(ch => ch.channel_type === typeFilter);
        }

        if (statusFilter === 'active') {
            filtered = filtered.filter(ch => ch.active);
        } else if (statusFilter === 'inactive') {
            filtered = filtered.filter(ch => !ch.active);
        }

        this.renderChannelsList(filtered);
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
    currentReport: null,
    
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
            Utils.showLoading('Génération du rapport intelligent avec IA...');

            // ✅ RÉCUPÉRER LES PARAMÈTRES DU FORMULAIRE
            const select = document.getElementById('reportKeywords');
            const keywordIds = Array.from(select.selectedOptions).map(opt => parseInt(opt.value));
            const periodDays = document.getElementById('reportPeriod').value;
            
            // Période au format attendu par le backend
            const period = periodDays + 'd'; // Ex: "7d", "30d"

            console.log('📊 Paramètres du rapport:', { keywordIds, period });

            if (keywordIds.length === 0) {
                Utils.hideLoading();
                Utils.showError('⚠️ Sélectionnez au moins un mot-clé');
                return;
            }

            // ✅ RÉCUPÉRER LES SECTIONS COCHÉES
            const sectionCheckboxes = document.querySelectorAll('input[name="section"]:checked');
            const sections = Array.from(sectionCheckboxes).map(cb => cb.value);

            console.log('📋 Sections sélectionnées:', sections);

            if (sections.length === 0) {
                Utils.hideLoading();
                Utils.showError('⚠️ Sélectionnez au moins une section à inclure');
                return;
            }

            // ✅ CONSTRUIRE L'URL AVEC LES BONS PARAMÈTRES
            const params = new URLSearchParams();
            
            // Ajouter chaque keyword_id séparément
            keywordIds.forEach(id => params.append('keyword_ids', id));
            
            // Ajouter la période
            params.append('period', period);
            
            // Ajouter chaque section séparément
            sections.forEach(s => params.append('sections', s));

            console.log('🔗 URL complète:', `/api/reports/generate-narrative?${params.toString()}`);

            // ✅ APPELER LA NOUVELLE ROUTE NARRATIVE
            const result = await Utils.fetchAPI(
                `/api/reports/generate-narrative?${params.toString()}`,
                { method: 'POST' }
            );

            console.log('✅ Rapport reçu:', result);

            Utils.hideLoading();

            // Afficher le rapport
            this.displayNarrativeReport(result);

            Utils.showSuccess('✅ Rapport généré avec succès');

        } catch (error) {
            Utils.hideLoading();
            console.error('❌ Erreur génération rapport:', error);
            
            // Message d'erreur plus détaillé
            let errorMessage = 'Erreur lors de la génération du rapport';
            
            if (error.message) {
                errorMessage += ': ' + error.message;
            }
            
            Utils.showError(errorMessage);
        }
    },

    displayNarrativeReport(report) {
        console.log('📊 Affichage rapport narratif', report);
        
        // Sauvegarder le rapport dans l'objet
        this.currentReport = report;
        
        const container = document.getElementById('reportResult');
        if (!container) {
            console.error('❌ Container reportResult introuvable');
            return;
        }

        // ===== EXTRACTION SÉCURISÉE DES DONNÉES =====
        const metadata = report.metadata || {};
        const sections = report.sections || {};
        
        // Gérer keywords (peut être string ou array)
        let keywords = 'N/A';
        if (metadata.keywords) {
            if (Array.isArray(metadata.keywords)) {
                keywords = metadata.keywords.join(', ');
            } else if (typeof metadata.keywords === 'string') {
                keywords = metadata.keywords;
            }
        }
        
        // Gérer ai_service_used (STRING pas ARRAY)
        let aiService = 'Service IA';
        if (metadata.ai_service_used) {
            aiService = metadata.ai_service_used; // ✅ Singulier, string directement
        } else if (metadata.ai_services_used) {
            // Fallback pour ancienne version (si c'était un tableau)
            if (Array.isArray(metadata.ai_services_used)) {
                aiService = metadata.ai_services_used.join(', ');
            } else {
                aiService = metadata.ai_services_used;
            }
        }
        
        // Ordre et configuration des sections
        const sectionOrder = [
            { key: 'summary', title: 'Résumé Exécutif', icon: 'fa-file-alt' },
            { key: 'sentiment', title: 'Analyse des Sentiments', icon: 'fa-heart' },
            { key: 'influencers', title: 'Acteurs Clés', icon: 'fa-users' },
            { key: 'themes', title: 'Thèmes Principaux', icon: 'fa-lightbulb' },
            { key: 'recommendations', title: 'Recommandations', icon: 'fa-check-circle' }
        ];

        // ===== CONSTRUCTION DU HTML =====
        const html = `
            <div class="narrative-report">
                <!-- En-tête -->
                <div class="report-header">
                    <div class="report-title-block">
                        <h2 class="report-title">${metadata.title || 'Rapport d\'Analyse'}</h2>
                        <div class="report-classification">
                            ${metadata.classification || 'DOCUMENT DE TRAVAIL'}
                        </div>
                    </div>
                    
                    <div class="report-metadata">
                        <div class="meta-item">
                            <i class="fas fa-calendar"></i>
                            <span>Généré le ${Utils.formatDate(metadata.generated_at)}</span>
                        </div>
                        <div class="meta-item">
                            <i class="fas fa-clock"></i>
                            <span>Période: ${metadata.period || 'N/A'}</span>
                        </div>
                        <div class="meta-item">
                            <i class="fas fa-tags"></i>
                            <span>Mots-clés: ${keywords}</span>
                        </div>
                        <div class="meta-item">
                            <i class="fas fa-database"></i>
                            <span>${metadata.relevant_mentions_analyzed || metadata.total_mentions_collected || 0} contenus analysés</span>
                        </div>
                        <div class="meta-item">
                            <i class="fas fa-robot"></i>
                            <span>IA: ${aiService}</span>
                        </div>
                    </div>
                </div>

                <!-- Corps du rapport -->
                <div class="report-body">
                    ${sectionOrder.map(section => {
                        if (!sections[section.key]) {
                            console.log(`⏭️ Section ${section.key} non incluse`);
                            return '';
                        }
                        
                        const content = sections[section.key];
                        
                        return `
                            <div class="report-section">
                                <h3 class="section-title">
                                    <i class="fas ${section.icon}"></i>
                                    ${section.title}
                                </h3>
                                <div class="section-content">
                                    ${this.formatNarrativeText(content)}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>

                <!-- Pied de page -->
                <div class="report-footer">
                    <div class="footer-note">
                        <i class="fas fa-info-circle"></i>
                        <span>Ce rapport a été généré automatiquement par analyse IA. 
                        Les contenus reflètent les discussions publiques collectées et ne constituent pas une position officielle.</span>
                    </div>
                    
                    <div class="report-actions">
                        <button onclick="Reports.exportJSON()" class="btn btn-secondary">
                            <i class="fas fa-download"></i> Exporter JSON
                        </button>
                        <button onclick="Reports.printReport()" class="btn btn-secondary">
                            <i class="fas fa-print"></i> Imprimer
                        </button>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;
        
        // Animation d'apparition
        setTimeout(() => {
            const report = container.querySelector('.narrative-report');
            if (report) {
                report.style.opacity = '0';
                report.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    report.style.transition = 'all 0.5s ease';
                    report.style.opacity = '1';
                    report.style.transform = 'translateY(0)';
                }, 50);
            }
        }, 100);
        
        console.log('✅ Rapport narratif affiché avec succès');
    },

    formatNarrativeText(text) {
        if (!text || typeof text !== 'string') {
            return '<p class="narrative-paragraph"><em>Aucun contenu disponible</em></p>';
        }

        // Formater le texte narratif en paragraphes HTML
        const paragraphs = text.split('\n\n').filter(p => p.trim().length > 0);
        
        return paragraphs.map(para => {
            const trimmed = para.trim();
            
            // Vérifier si c'est un titre ou un paragraphe normal
            if (trimmed.length < 100 && trimmed.endsWith(':')) {
                return `<h3 class="narrative-subheading">${trimmed}</h3>`;
            }
            
            return `<p class="narrative-paragraph">${trimmed}</p>`;
        }).join('');
    },

    exportJSON() {
        if (!this.currentReport) {
            Utils.showError('Aucun rapport à exporter');
            return;
        }

        const blob = new Blob(
            [JSON.stringify(this.currentReport, null, 2)], 
            { type: 'application/json' }
        );
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        const keywords = this.currentReport.metadata.keywords.join('_');
        const date = new Date().toISOString().split('T')[0];
        a.download = `rapport_${keywords}_${date}.json`;
        
        a.click();
        URL.revokeObjectURL(url);

        Utils.showSuccess('✅ Rapport exporté en JSON');
    },

    printReport() {
        window.print();
        Utils.showSuccess('📄 Dialogue d\'impression ouvert');
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

    // Boutons Channels
    document.getElementById('addChannelBtn')?.addEventListener('click', () => {
        Channels.showAddChannelModal();
    });

    document.getElementById('refreshChannelsBtn')?.addEventListener('click', () => {
        Channels.load();
    });

    document.getElementById('collectAllChannelsBtn')?.addEventListener('click', () => {
        Channels.collectAllChannels();
    });

    document.getElementById('applyChannelFilters')?.addEventListener('click', () => {
        Channels.applyFilters();
    });

    // Gérer les tabs channels
    document.querySelectorAll('.tab[data-tab^="channels-"]').forEach(tab => {
        tab.addEventListener('click', async () => {
            const tabName = tab.dataset.tab;
            if (tabName === 'channels-monitoring') {
                await Channels.loadMonitoring();
            } else if (tabName === 'channels-presets') {
                await Channels.loadPopularChannels();
            }
        });
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