"""
Template HTML pour Rapports Exécutifs
Format adapté aux dirigeants - Focus sur la synthèse narrative
"""

def generate_executive_html_template(report_data: Dict) -> str:
    """Générer le HTML du rapport exécutif"""
    
    metadata = report_data['metadata']
    synthesis = report_data['executive_synthesis']
    summaries = report_data['content_summaries']
    key_messages = report_data['key_messages']
    recommendations = report_data['strategic_recommendations']
    stats = report_data['statistics']
    
    # Calculer les pourcentages pour le graphique
    total = synthesis['total_contents_analyzed']
    breakdown = synthesis['breakdown']
    
    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata['title']}</title>
    <style>
        @page {{
            size: A4;
            margin: 1.5cm;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            font-size: 11pt;
            background: white;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 28pt;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header .meta {{
            font-size: 10pt;
            opacity: 0.9;
            margin-top: 15px;
        }}
        
        /* Section */
        .section {{
            margin-bottom: 30px;
            page-break-inside: avoid;
        }}
        
        .section-title {{
            font-size: 18pt;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 3px solid #667eea;
        }}
        
        /* Executive Summary */
        .executive-summary {{
            background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
            border-left: 5px solid #667eea;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        
        .tone-indicator {{
            display: inline-flex;
            align-items: center;
            font-size: 16pt;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 15px;
        }}
        
        .tone-emoji {{
            font-size: 32pt;
            margin-right: 15px;
        }}
        
        .synthesis-text {{
            font-size: 12pt;
            line-height: 1.8;
            color: #2c3e50;
            margin: 20px 0;
            text-align: justify;
        }}
        
        /* Alert Boxes */
        .alert {{
            padding: 15px 20px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 5px solid;
        }}
        
        .alert-critical {{
            background: #fee;
            border-color: #c00;
            color: #900;
        }}
        
        .alert-opportunity {{
            background: #efe;
            border-color: #0a0;
            color: #060;
        }}
        
        .alert-warning {{
            background: #ffeaa7;
            border-color: #f39c12;
            color: #6d4c00;
        }}
        
        .alert strong {{
            font-weight: 700;
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 25px 0;
        }}
        
        .stat-card {{
            background: white;
            border: 2px solid #e1e8ed;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 32pt;
            font-weight: 700;
            color: #667eea;
            margin: 10px 0;
        }}
        
        .stat-label {{
            font-size: 10pt;
            color: #657786;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }}
        
        /* Content Categories */
        .category-section {{
            margin: 25px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 10px;
            page-break-inside: avoid;
        }}
        
        .category-header {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .category-icon {{
            font-size: 28pt;
            margin-right: 15px;
        }}
        
        .category-title {{
            font-size: 14pt;
            font-weight: 700;
            color: #2c3e50;
        }}
        
        .category-count {{
            margin-left: auto;
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 10pt;
        }}
        
        .category-summary {{
            font-size: 11pt;
            line-height: 1.7;
            color: #34495e;
            margin: 15px 0;
            text-align: justify;
        }}
        
        .excerpt-box {{
            background: white;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            font-size: 10pt;
            color: #555;
        }}
        
        .excerpt-title {{
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .excerpt-meta {{
            font-size: 9pt;
            color: #999;
            margin-top: 8px;
        }}
        
        /* Recommendations */
        .recommendation {{
            background: white;
            border: 2px solid #e1e8ed;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            page-break-inside: avoid;
        }}
        
        .rec-header {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }}
        
        .rec-priority {{
            font-size: 9pt;
            font-weight: 700;
            padding: 5px 12px;
            border-radius: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-right: 15px;
        }}
        
        .priority-urgent {{
            background: #ff4444;
            color: white;
        }}
        
        .priority-élevée {{
            background: #ff8800;
            color: white;
        }}
        
        .priority-moyenne {{
            background: #4CAF50;
            color: white;
        }}
        
        .rec-category {{
            font-size: 11pt;
            font-weight: 600;
            color: #667eea;
        }}
        
        .rec-action {{
            font-size: 12pt;
            font-weight: 700;
            color: #2c3e50;
            margin: 10px 0;
        }}
        
        .rec-rationale {{
            font-size: 10pt;
            color: #657786;
            line-height: 1.6;
            margin: 8px 0;
        }}
        
        .rec-timeline {{
            display: inline-block;
            background: #e8f4f8;
            color: #2c3e50;
            padding: 5px 12px;
            border-radius: 5px;
            font-size: 9pt;
            font-weight: 600;
            margin-top: 8px;
        }}
        
        /* Footer */
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e1e8ed;
            text-align: center;
            color: #657786;
            font-size: 9pt;
        }}
        
        .footer strong {{
            color: #667eea;
            font-weight: 700;
        }}
        
        /* Print specific */
        @media print {{
            body {{
                font-size: 10pt;
            }}
            
            .section {{
                page-break-inside: avoid;
            }}
            
            .recommendation {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>{metadata['title']}</h1>
            <div class="meta">
                📅 Généré le {metadata['generated_at'].strftime('%d/%m/%Y à %H:%M')} •
                📊 Période analysée: {metadata['period_days']} jours •
                📝 {total} contenus analysés
            </div>
            <div class="meta">
                🎯 Mots-clés: {', '.join(metadata['keywords'])}
            </div>
        </div>
        
        <!-- Executive Summary -->
        <div class="section">
            <h2 class="section-title">📋 Synthèse Exécutive</h2>
            
            <div class="executive-summary">
                <div class="tone-indicator">
                    <span class="tone-emoji">{synthesis['sentiment_emoji']}</span>
                    <span>Tonalité: {synthesis['overall_tone']}</span>
                </div>
                
                <div class="synthesis-text">
                    {synthesis['synthesis_text']}
                </div>
            </div>
            
            <!-- Stats rapides -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Contenus Positifs</div>
                    <div class="stat-value">{breakdown['very_positive'] + breakdown['positive']}</div>
                    <div class="stat-label">{round((breakdown['very_positive'] + breakdown['positive']) / total * 100, 1)}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Contenus Neutres</div>
                    <div class="stat-value">{breakdown['neutral']}</div>
                    <div class="stat-label">{round(breakdown['neutral'] / total * 100, 1)}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Contenus Négatifs</div>
                    <div class="stat-value">{breakdown['negative'] + breakdown['very_negative']}</div>
                    <div class="stat-label">{round((breakdown['negative'] + breakdown['very_negative']) / total * 100, 1)}%</div>
                </div>
            </div>
"""
    
    # Points critiques
    if synthesis.get('critical_points'):
        html += """
            <div class="section">
                <h3 style="font-size: 14pt; color: #c00; font-weight: 700; margin: 20px 0 15px 0;">
                    🚨 Points d'Attention Prioritaires
                </h3>
"""
        for point in synthesis['critical_points']:
            html += f"""
                <div class="alert alert-critical">
                    <strong>{point}</strong>
                </div>
"""
        html += "</div>"
    
    # Opportunités
    if synthesis.get('opportunities'):
        html += """
            <div class="section">
                <h3 style="font-size: 14pt; color: #0a0; font-weight: 700; margin: 20px 0 15px 0;">
                    ✨ Opportunités Identifiées
                </h3>
"""
        for opportunity in synthesis['opportunities']:
            html += f"""
                <div class="alert alert-opportunity">
                    <strong>{opportunity}</strong>
                </div>
"""
        html += "</div>"
    
    html += "</div>"
    
    # Analyse par catégorie
    html += """
        <div class="section">
            <h2 class="section-title">📊 Analyse Détaillée par Sentiment</h2>
"""
    
    category_config = {
        'very_negative': {
            'icon': '😠',
            'title': 'Contenus Très Négatifs',
            'color': '#c00'
        },
        'negative': {
            'icon': '😟',
            'title': 'Contenus Négatifs',
            'color': '#f39c12'
        },
        'neutral': {
            'icon': '😐',
            'title': 'Contenus Neutres',
            'color': '#657786'
        },
        'positive': {
            'icon': '🙂',
            'title': 'Contenus Positifs',
            'color': '#27ae60'
        },
        'very_positive': {
            'icon': '😊',
            'title': 'Contenus Très Positifs',
            'color': '#0a0'
        }
    }
    
    for category, config in category_config.items():
        category_data = summaries.get(category, {})
        if category_data.get('count', 0) > 0:
            html += f"""
            <div class="category-section">
                <div class="category-header">
                    <span class="category-icon">{config['icon']}</span>
                    <span class="category-title">{config['title']}</span>
                    <span class="category-count">{category_data['count']} contenu(s)</span>
                </div>
                
                <div class="category-summary">
                    {category_data['summary']}
                </div>
"""
            
            # Extraits représentatifs
            if category_data.get('representative_excerpts'):
                html += '<h4 style="font-size: 11pt; font-weight: 700; margin: 15px 0 10px 0; color: #2c3e50;">Extraits Représentatifs:</h4>'
                
                for excerpt in category_data['representative_excerpts'][:2]:  # Max 2 par catégorie
                    html += f"""
                <div class="excerpt-box">
                    <div class="excerpt-title">{excerpt['title']}</div>
                    <div style="margin: 8px 0; font-style: italic;">"{excerpt['excerpt']}"</div>
                    <div class="excerpt-meta">
                        {excerpt['source'].upper()} • {excerpt['date'][:10] if excerpt['date'] else 'Date inconnue'}
                    </div>
                </div>
"""
            
            html += "</div>"
    
    html += "</div>"
    
    # Recommandations Stratégiques
    html += """
        <div class="section">
            <h2 class="section-title">🎯 Recommandations Stratégiques</h2>
            <p style="font-size: 11pt; color: #657786; margin-bottom: 20px;">
                Actions prioritaires à considérer selon l'analyse des contenus
            </p>
"""
    
    for rec in recommendations:
        priority_class = f"priority-{rec['priority'].lower()}"
        html += f"""
            <div class="recommendation">
                <div class="rec-header">
                    <span class="rec-priority {priority_class}">{rec['priority']}</span>
                    <span class="rec-category">{rec['category']}</span>
                </div>
                
                <div class="rec-action">
                    {rec['action']}
                </div>
                
                <div class="rec-rationale">
                    <strong>Justification:</strong> {rec['rationale']}
                </div>
                
                <span class="rec-timeline">
                    ⏱️ {rec['timeline']}
                </span>
            </div>
"""
    
    html += "</div>"
    
    # Footer
    html += f"""
        <div class="footer">
            <p>
                <strong>Rapport Exécutif Intelligent</strong> • Brand Monitor IA Souveraine
            </p>
            <p style="margin-top: 10px;">
                Analyse basée sur {total} contenus complets •
                Technologies: Ollama LLM + Analyse Sémantique Avancée
            </p>
            <p style="margin-top: 5px; font-size: 8pt;">
                Ce rapport est confidentiel et destiné uniquement à un usage interne
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return html