"""
Template HTML Stratégique V2
Format: Synthèse + Problématiques + Activistes
"""

from datetime import datetime

def generate_strategic_report_v2_html(report_data: dict) -> str:
    """Générer le HTML du rapport stratégique V2"""
    
    metadata = report_data.get('metadata', {})
    synthesis = report_data.get('synthese_strategique', {})
    problematiques_data = report_data.get('problematiques_identifiees', {})
    if isinstance(problematiques_data, dict):
        problematiques = problematiques_data.get('problematiques', [])
    elif isinstance(problematiques_data, list):
        problematiques = problematiques_data
    else:
        problematiques = []
    activists = report_data.get('activistes_comptes_sensibles', {})
    stats = report_data.get('statistiques', {})
    
    # Couleur du niveau de risque
    risk_level = synthesis.get('niveau_risque', 'FAIBLE')
    risk_colors = {
        'CRITIQUE': '#dc2626',
        'ÉLEVÉ': '#ea580c',
        'MODÉRÉ': '#f59e0b',
        'FAIBLE': '#10b981'
    }
    risk_color = risk_colors.get(risk_level, '#6b7280')
    
    # Construire les sections des problématiques
    problematiques_html = ""
    if problematiques:
        for idx, prob in enumerate(problematiques, 1):
            importance_badge = f"""
            <span class="badge badge-{
                'critical' if prob.get('importance') == 'critique' else
                'high' if prob.get('importance') == 'élevé' else 'medium'
            }">
                {prob.get('importance', 'N/A').upper()}
            </span>
            """
            
            elements_cles_html = ""
            if prob.get('elements_cles'):
                elements_items = "".join([
                    f'<li class="quote-item">"{elem}"</li>' 
                    for elem in prob.get('elements_cles', [])[:5]
                ])
                elements_cles_html = f"""
                <div class="elements-cles">
                    <strong>Éléments clés:</strong>
                    <ul class="quote-list">
                        {elements_items}
                    </ul>
                </div>
                """
            
            sources_html = ""
            if prob.get('sources'):
                sources_html = f"""
                <div class="sources-info">
                    <strong>Sources:</strong> {', '.join(prob.get('sources', [])[:5])} 
                    ({prob.get('nombre_mentions', 0)} mentions)
                </div>
                """
            
            problematiques_html += f"""
            <div class="problematique-card">
                <div class="problematique-header">
                    <h3 class="problematique-title">
                        {idx}. {prob.get('titre', 'Sans titre')}
                    </h3>
                    {importance_badge}
                </div>
                
                <div class="problematique-description">
                    {prob.get('description', 'Pas de description disponible.')}
                </div>
                
                {elements_cles_html}
                
                {sources_html}
            </div>
            """
    else:
        problematiques_html = """
        <div class="alert alert-info">
            Aucune problématique majeure identifiée durant cette période.
        </div>
        """
    
    # Construire le tableau des activistes
    activists_table_html = ""
    if activists.get('liste'):
        rows_html = "".join([
            f"""<tr class="{'known-activist' if a.get('is_known') else ''}">
                <td>
                    <strong>{a.get('nom', 'Inconnu')}</strong>
                    {'<span class="badge badge-warning">Connu</span>' if a.get('is_known') else ''}
                </td>
                <td class="text-center">{a.get('contenus', 0)}</td>
                <td class="text-right">{a.get('engagement_total', 0):,}</td>
                <td class="text-center"><small>{a.get('sources', 'N/A')}</small></td>
            </tr>"""
            for a in activists.get('liste', [])[:30]
        ])
        
        activists_table_html = f"""
        <table class="activists-table">
            <thead>
                <tr>
                    <th>Nom</th>
                    <th class="text-center">Contenus</th>
                    <th class="text-right">Engagement Total</th>
                    <th class="text-center">Sources</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        """
    else:
        activists_table_html = """
        <div class="alert alert-info">
            Aucun compte influent détecté durant cette période.
        </div>
        """
    
    # HTML principal
    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata.get('title', 'Rapport Stratégique')}</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.5;
            color: #1f2937;
            font-size: 10.5pt;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
            color: white;
            padding: 25px 30px;
            margin: -2cm -2cm 1.5cm -2cm;
        }}
        
        .header h1 {{
            font-size: 24pt;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        
        .header .subtitle {{
            font-size: 11pt;
            opacity: 0.95;
        }}
        
        .metadata-box {{
            background: #f8fafc;
            border-left: 4px solid #3b82f6;
            padding: 12px 15px;
            margin-bottom: 20px;
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            font-size: 9.5pt;
        }}
        
        .metadata-item {{
            display: flex;
            flex-direction: column;
        }}
        
        .metadata-label {{
            font-weight: 600;
            color: #475569;
            margin-bottom: 2px;
        }}
        
        h2 {{
            color: #1e293b;
            font-size: 16pt;
            font-weight: bold;
            margin: 25px 0 12px 0;
            padding-bottom: 6px;
            border-bottom: 2px solid #3b82f6;
            page-break-after: avoid;
        }}
        
        h3 {{
            color: #334155;
            font-size: 12pt;
            font-weight: 600;
            margin: 15px 0 8px 0;
            page-break-after: avoid;
        }}
        
        .section {{
            margin-bottom: 25px;
            page-break-inside: avoid;
        }}
        
        .synthesis-box {{
            background: #fef3c7;
            border-left: 5px solid #f59e0b;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        
        .risk-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 10pt;
            color: white;
            background: {risk_color};
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin: 15px 0;
        }}
        
        .metric-box {{
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 12px;
            text-align: center;
        }}
        
        .metric-value {{
            font-size: 18pt;
            font-weight: bold;
            color: #3b82f6;
        }}
        
        .metric-label {{
            font-size: 8pt;
            color: #64748b;
            text-transform: uppercase;
            margin-top: 3px;
        }}
        
        .problematique-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            margin: 12px 0;
            page-break-inside: avoid;
        }}
        
        .problematique-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 10px;
        }}
        
        .problematique-title {{
            font-size: 11.5pt;
            font-weight: 600;
            color: #1e293b;
            margin: 0;
            flex: 1;
        }}
        
        .problematique-description {{
            color: #475569;
            margin: 10px 0;
            line-height: 1.6;
        }}
        
        .elements-cles {{
            background: #f1f5f9;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            font-size: 9.5pt;
        }}
        
        .quote-list {{
            list-style: none;
            padding: 8px 0 0 0;
        }}
        
        .quote-item {{
            padding: 6px 0;
            border-left: 3px solid #cbd5e1;
            padding-left: 10px;
            margin: 5px 0;
            font-style: italic;
            color: #334155;
        }}
        
        .sources-info {{
            font-size: 9pt;
            color: #64748b;
            margin-top: 8px;
        }}
        
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 8pt;
            font-weight: 600;
        }}
        
        .badge-critical {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .badge-high {{
            background: #fed7aa;
            color: #9a3412;
        }}
        
        .badge-medium {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .badge-warning {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .activists-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 9.5pt;
        }}
        
        .activists-table thead {{
            background: #f1f5f9;
        }}
        
        .activists-table th {{
            padding: 10px 8px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #cbd5e1;
            color: #475569;
        }}
        
        .activists-table td {{
            padding: 10px 8px;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .activists-table .known-activist {{
            background: #fef3c7;
        }}
        
        .text-center {{
            text-align: center;
        }}
        
        .text-right {{
            text-align: right;
        }}
        
        .alert {{
            padding: 12px 15px;
            border-radius: 6px;
            margin: 15px 0;
            font-size: 9.5pt;
        }}
        
        .alert-info {{
            background: #dbeafe;
            color: #1e40af;
            border-left: 4px solid #3b82f6;
        }}
        
        .page-break {{
            page-break-before: always;
        }}
        
        .footer {{
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #e2e8f0;
            text-align: center;
            font-size: 8.5pt;
            color: #64748b;
        }}
    </style>
</head>
<body>
    <!-- En-tête -->
    <div class="header">
        <h1>📊 {metadata.get('title', 'Rapport Stratégique')}</h1>
        <div class="subtitle">
            Division Communication et Contre-Information
        </div>
    </div>
    
    <!-- Métadonnées -->
    <div class="metadata-box">
        <div class="metadata-item">
            <span class="metadata-label">Mots-clés analysés</span>
            <span>{', '.join(metadata.get('keywords', []))}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Période</span>
            <span>{metadata.get('period_days', 0)} jours</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Contenus analysés</span>
            <span>{metadata.get('total_contents', 0)} publications</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Généré le</span>
            <span>{datetime.utcnow().strftime('%d/%m/%Y à %H:%M')}</span>
        </div>
    </div>
    
    <!-- ===== SECTION 1: SYNTHÈSE STRATÉGIQUE ===== -->
    <div class="section">
        <h2>🎯 SYNTHÈSE STRATÉGIQUE</h2>
        
        <div class="synthesis-box">
            <div style="margin-bottom: 12px;">
                <strong>Niveau de risque:</strong> 
                <span class="risk-badge">{risk_level}</span>
            </div>
            
            <div style="line-height: 1.7;">
                {synthesis.get('synthese_text', 'Synthèse non disponible.')}
            </div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-box">
                <div class="metric-value">{synthesis.get('metriques_cles', {}).get('total_contenus', 0)}</div>
                <div class="metric-label">Contenus</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{synthesis.get('metriques_cles', {}).get('problematiques_identifiees', 0)}</div>
                <div class="metric-label">Problématiques</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{synthesis.get('metriques_cles', {}).get('activistes_detectes', 0)}</div>
                <div class="metric-label">Activistes</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{synthesis.get('metriques_cles', {}).get('periode_jours', 0)}j</div>
                <div class="metric-label">Période</div>
            </div>
        </div>
    </div>
    
    <!-- ===== SECTION 2: PROBLÉMATIQUES IDENTIFIÉES ===== -->
    <div class="section page-break">
        <h2>🔍 PROBLÉMATIQUES IDENTIFIÉES</h2>
        
        <p style="color: #64748b; margin-bottom: 15px; font-size: 9.5pt;">
            Analyse approfondie des enjeux stratégiques basée sur la lecture du contenu réel (articles, commentaires, vidéos).
        </p>
        
        {problematiques_html}
    </div>
    
    <!-- ===== SECTION 3: ACTIVISTES ET COMPTES SENSIBLES ===== -->
    <div class="section page-break">
        <h2>🚨 ACTIVISTES ET COMPTES SENSIBLES</h2>
        
        <div style="margin-bottom: 15px; font-size: 9.5pt;">
            <strong>{activists.get('total_detectes', 0)}</strong> compte(s) influent(s) détecté(s), 
            dont <strong>{activists.get('activistes_connus', 0)}</strong> activiste(s) connu(s) 
            et <strong>{activists.get('comptes_suspects', 0)}</strong> compte(s) suspect(s).
        </div>
        
        {activists_table_html}
    </div>
    
    <!-- Footer -->
    <div class="footer">
        <p>
            <strong>Rapport Stratégique Confidentiel</strong><br>
            Analyse IA Souveraine • Division Communication et Contre-Information<br>
            Généré automatiquement avec Intelligence Artificielle locale
        </p>
    </div>
</body>
</html>
"""
    
    return html