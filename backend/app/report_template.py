"""
Template HTML Professionnel pour Rapports Stratégiques
Style inspiration Redaction.pdf
"""

def generate_strategic_report_html(report_data: dict) -> str:
    """Générer le HTML du rapport stratégique"""
    
    metadata = report_data.get('metadata', {})
    positive = report_data.get('tonalite_positive', {})
    negative = report_data.get('tonalite_negative', {})
    neutral = report_data.get('tonalite_neutre', {})
    synthesis = report_data.get('synthese_generale', {})
    activists = report_data.get('activistes_comptes_sensibles', {})
    
    # Déterminer la couleur du niveau de risque
    risk_level = negative.get('risk_level', 'FAIBLE')
    risk_colors = {
        'ÉLEVÉ': '#ef4444',
        'MODÉRÉ': '#f59e0b',
        'FAIBLE': '#10b981'
    }
    risk_color = risk_colors.get(risk_level, '#6b7280')
    
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
        
        body {{
            font-family: 'Segoe UI', 'Arial', sans-serif;
            line-height: 1.6;
            color: #1f2937;
            font-size: 11pt;
            margin: 0;
            padding: 0;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            margin: -2cm -2cm 2cm -2cm;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 28pt;
            font-weight: bold;
        }}
        
        .header .subtitle {{
            font-size: 12pt;
            opacity: 0.9;
        }}
        
        .metadata {{
            background: #f3f4f6;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 25px;
            border-left: 4px solid #667eea;
        }}
        
        .metadata-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }}
        
        .metadata-item {{
            font-size: 10pt;
        }}
        
        .metadata-label {{
            font-weight: bold;
            color: #4b5563;
        }}
        
        h2 {{
            color: #1f2937;
            font-size: 18pt;
            font-weight: bold;
            margin: 30px 0 15px 0;
            padding-bottom: 8px;
            border-bottom: 3px solid #667eea;
            page-break-after: avoid;
        }}
        
        h3 {{
            color: #374151;
            font-size: 14pt;
            font-weight: 600;
            margin: 20px 0 10px 0;
            page-break-after: avoid;
        }}
        
        .section {{
            margin-bottom: 35px;
            page-break-inside: avoid;
        }}
        
        .synthesis-box {{
            background: #f0fdf4;
            border-left: 5px solid #10b981;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        
        .warning-box {{
            background: #fef3c7;
            border-left: 5px solid #f59e0b;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        
        .danger-box {{
            background: #fee2e2;
            border-left: 5px solid #ef4444;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        
        .info-box {{
            background: #e0e7ff;
            border-left: 5px solid #6366f1;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        
        .stat-box {{
            background: white;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 24pt;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 9pt;
            color: #6b7280;
            text-transform: uppercase;
        }}
        
        .content-item {{
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 15px;
            margin: 10px 0;
        }}
        
        .content-title {{
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 8px;
        }}
        
        .content-meta {{
            font-size: 9pt;
            color: #6b7280;
            margin-bottom: 8px;
        }}
        
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 8pt;
            font-weight: 600;
            margin-right: 5px;
        }}
        
        .badge-critical {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .badge-high {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .badge-medium {{
            background: #dbeafe;
            color: #1e40af;
        }}
        
        .badge-low {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .recommendation {{
            background: #fffbeb;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        
        .recommendation-priority {{
            font-weight: bold;
            color: #92400e;
            text-transform: uppercase;
            font-size: 9pt;
            margin-bottom: 5px;
        }}
        
        .activist-item {{
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 6px;
            padding: 12px;
            margin: 8px 0;
        }}
        
        .activist-name {{
            font-weight: bold;
            color: #991b1b;
            margin-bottom: 5px;
        }}
        
        .activist-stats {{
            font-size: 9pt;
            color: #6b7280;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 10pt;
        }}
        
        th {{
            background: #f3f4f6;
            padding: 10px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #d1d5db;
        }}
        
        td {{
            padding: 10px;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .page-break {{
            page-break-before: always;
        }}
        
        ul {{
            margin: 10px 0;
            padding-left: 25px;
        }}
        
        li {{
            margin: 5px 0;
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
    <div class="metadata">
        <div class="metadata-grid">
            <div class="metadata-item">
                <span class="metadata-label">Mots-clés analysés:</span><br>
                {', '.join(metadata.get('keywords', []))}
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Période:</span><br>
                {metadata.get('period_days', 0)} jours
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Contenus analysés:</span><br>
                {metadata.get('total_contents', 0)} publications
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Généré le:</span><br>
                {datetime.utcnow().strftime('%d/%m/%Y à %H:%M')}
            </div>
        </div>
    </div>
    
    <!-- ====== SECTION 1: SYNTHÈSE GÉNÉRALE ====== -->
    <div class="section page-break">
        <h2>🎯 SYNTHÈSE GÉNÉRALE STRATÉGIQUE</h2>
        
        <div class="synthesis-box">
            <p><strong>Tonalité globale:</strong> {synthesis.get('overall_tone', 'N/A')} {synthesis.get('emoji', '')}</p>
            <p><strong>Évaluation stratégique:</strong> Situation {synthesis.get('strategic_assessment', 'N/A')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-value">{synthesis.get('breakdown', {}).get('positive', 0)}</div>
                <div class="stat-label">Contenus Positifs</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{synthesis.get('breakdown', {}).get('neutral', 0)}</div>
                <div class="stat-label">Contenus Neutres</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{synthesis.get('breakdown', {}).get('negative', 0)}</div>
                <div class="stat-label">Contenus Négatifs</div>
            </div>
        </div>
        
        <h3>Analyse de la Situation</h3>
        <p>{synthesis.get('synthesis_text', 'Synthèse non disponible.')}</p>
        
        <h3>Points Stratégiques Clés</h3>
        <ul>
            {"".join([f"<li>{point}</li>" for point in synthesis.get('strategic_points', [])])}
        </ul>
        
        <h3>Recommandations Prioritaires</h3>
        {"".join([
            f'''<div class="recommendation">
                <div class="recommendation-priority">{rec.get('priority', 'N/A')}</div>
                <strong>{rec.get('action', 'N/A')}</strong><br>
                <span style="font-size: 9pt; color: #6b7280;">Timeline: {rec.get('timeline', 'N/A')}</span>
            </div>'''
            for rec in synthesis.get('priority_recommendations', [])
        ])}
    </div>
    
    <!-- ====== SECTION 2: TONALITÉ POSITIVE ====== -->
    <div class="section page-break">
        <h2>😊 CONTENUS À TONALITÉ POSITIVE</h2>
        
        <div class="info-box">
            <p><strong>{positive.get('count', 0)} contenu(s) positif(s) identifié(s)</strong></p>
            <p>{positive.get('synthesis', 'Aucune synthèse disponible.')}</p>
        </div>
        
        {f'''
        <h3>Messages Clés Positifs</h3>
        <ul>
            {"".join([f"<li>{msg}</li>" for msg in positive.get('key_messages', [])])}
        </ul>
        ''' if positive.get('key_messages') else ''}
        
        {f'''
        <h3>Top Contenus Positifs</h3>
        {"".join([
            f'''<div class="content-item">
                <div class="content-title">{content.get('title', 'Sans titre')}</div>
                <div class="content-meta">
                    <span class="badge badge-low">{content.get('source', 'N/A')}</span>
                    Par {content.get('author', 'Inconnu')} • 
                    Engagement: {content.get('engagement_score', 0):,.0f}
                </div>
            </div>'''
            for content in positive.get('top_contents', [])[:5]
        ])}
        ''' if positive.get('top_contents') else ''}
        
        <h3>Recommandations d'Exploitation</h3>
        <ul>
            {"".join([f"<li>{rec}</li>" for rec in positive.get('recommendations', [])])}
        </ul>
    </div>
    
    <!-- ====== SECTION 3: TONALITÉ NÉGATIVE ====== -->
    <div class="section page-break">
        <h2>😟 CONTENUS À TONALITÉ NÉGATIVE</h2>
        
        <div class="danger-box">
            <p><strong>{negative.get('count', 0)} contenu(s) négatif(s) identifié(s)</strong></p>
            <p><strong>Niveau de risque:</strong> <span style="color: {risk_color}; font-weight: bold;">{negative.get('risk_level', 'N/A')}</span></p>
        </div>
        
        <h3>Analyse des Contenus Critiques</h3>
        <p>{negative.get('synthesis', 'Aucune synthèse disponible.')}</p>
        
        {f'''
        <h3>Principales Critiques Identifiées</h3>
        <ul>
            {"".join([f"<li>{crit}</li>" for crit in negative.get('key_criticisms', [])])}
        </ul>
        ''' if negative.get('key_criticisms') else ''}
        
        {f'''
        <h3>Top Contenus Critiques (Surveillance Prioritaire)</h3>
        {"".join([
            f'''<div class="content-item" style="border-left: 3px solid #ef4444;">
                <div class="content-title">{content.get('title', 'Sans titre')}</div>
                <div class="content-meta">
                    <span class="badge badge-critical">{content.get('strategic_impact', 'N/A').upper()}</span>
                    <span class="badge badge-high">{content.get('source', 'N/A')}</span>
                    Par {content.get('author', 'Inconnu')} • 
                    Engagement: {content.get('engagement_score', 0):,.0f}
                </div>
            </div>'''
            for content in negative.get('top_contents', [])[:5]
        ])}
        ''' if negative.get('top_contents') else ''}
        
        <h3>Recommandations de Contre-Information</h3>
        {"".join([
            f'''<div class="recommendation">
                <div class="recommendation-priority">ACTION REQUISE</div>
                {rec}
            </div>'''
            for rec in negative.get('recommendations', [])
        ])}
    </div>
    
    <!-- ====== SECTION 4: TONALITÉ NEUTRE ====== -->
    <div class="section page-break">
        <h2>😐 CONTENUS À TONALITÉ NEUTRE</h2>
        
        <div class="info-box">
            <p><strong>{neutral.get('count', 0)} contenu(s) neutre(s) identifié(s)</strong></p>
            <p>{neutral.get('synthesis', 'Aucune synthèse disponible.')}</p>
        </div>
        
        {f'''
        <h3>Opportunités de Positionnement</h3>
        <ul>
            {"".join([f"<li>{opp}</li>" for opp in neutral.get('opportunities', [])])}
        </ul>
        ''' if neutral.get('opportunities') else ''}
        
        {f'''
        <h3>Principaux Contenus Neutres</h3>
        {"".join([
            f'''<div class="content-item">
                <div class="content-title">{content.get('title', 'Sans titre')}</div>
                <div class="content-meta">
                    <span class="badge badge-medium">{content.get('source', 'N/A')}</span>
                    Par {content.get('author', 'Inconnu')} • 
                    Engagement: {content.get('engagement_score', 0):,.0f}
                </div>
            </div>'''
            for content in neutral.get('top_contents', [])[:3]
        ])}
        ''' if neutral.get('top_contents') else ''}
    </div>
    
    <!-- ====== SECTION 5: ACTIVISTES ET COMPTES SENSIBLES ====== -->
    <div class="section page-break">
        <h2>🚨 ACTIVISTES ET COMPTES SENSIBLES</h2>
        
        <div class="warning-box">
            <p><strong>Synthèse:</strong> {activists.get('synthesis', 'Aucune détection.')}</p>
            <p>
                <strong>{activists.get('total_known', 0)}</strong> activiste(s) connu(s) détecté(s) • 
                <strong>{activists.get('total_suspicious', 0)}</strong> compte(s) suspect(s) identifié(s)
            </p>
        </div>
        
        {f'''
        <h3>⚠️ Activistes Prioritaires (Surveillance Critique)</h3>
        {"".join([
            f'''<div class="activist-item">
                <div class="activist-name">🔴 {activist.get('author', 'Inconnu')}</div>
                <div class="activist-stats">
                    <span class="badge badge-critical">{activist.get('alert_level', 'N/A')}</span>
                    {activist.get('total_contents', 0)} contenu(s) • 
                    Engagement total: {activist.get('total_engagement', 0):,.0f} • 
                    Négatif: {activist.get('negative_ratio', 0)}%
                </div>
            </div>'''
            for activist in activists.get('priority_activists', [])[:10]
        ])}
        ''' if activists.get('priority_activists') else '<p>Aucun activiste prioritaire identifié.</p>'}
        
        {f'''
        <h3>Activistes Connus Détectés</h3>
        <table>
            <thead>
                <tr>
                    <th>Nom</th>
                    <th>Contenus</th>
                    <th>Engagement</th>
                    <th>Tonalité</th>
                </tr>
            </thead>
            <tbody>
                {"".join([
                    f'''<tr>
                        <td><strong>{activist.get('author', 'Inconnu')}</strong></td>
                        <td>{activist.get('total_contents', 0)}</td>
                        <td>{activist.get('total_engagement', 0):,.0f}</td>
                        <td>
                            {f"{sum(1 for t in activist.get('tones', []) if t in ['negative', 'very_negative'])}/{len(activist.get('tones', []))} négatifs" if activist.get('tones') else 'N/A'}
                        </td>
                    </tr>'''
                    for activist in activists.get('known_activists', [])[:20]
                ])}
            </tbody>
        </table>
        ''' if activists.get('known_activists') else '<p>Aucun activiste connu détecté durant cette période.</p>'}
        
        {f'''
        <h3>Comptes Suspects Identifiés (Non Répertoriés)</h3>
        <table>
            <thead>
                <tr>
                    <th>Compte</th>
                    <th>Contenus</th>
                    <th>Engagement</th>
                    <th>Tonalité</th>
                </tr>
            </thead>
            <tbody>
                {"".join([
                    f'''<tr>
                        <td><strong>{suspect.get('author', 'Inconnu')}</strong></td>
                        <td>{suspect.get('total_contents', 0)}</td>
                        <td>{suspect.get('total_engagement', 0):,.0f}</td>
                        <td>
                            {f"{sum(1 for t in suspect.get('tones', []) if t in ['negative', 'very_negative'])}/{len(suspect.get('tones', []))} négatifs" if suspect.get('tones') else 'N/A'}
                        </td>
                    </tr>'''
                    for suspect in activists.get('suspicious_accounts', [])[:10]
                ])}
            </tbody>
        </table>
        ''' if activists.get('suspicious_accounts') else '<p>Aucun compte suspect identifié.</p>'}
    </div>
    
    <!-- Footer -->
    <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #e5e7eb; text-align: center; font-size: 9pt; color: #6b7280;">
        <p>
            <strong>Rapport Stratégique Confidentiel</strong><br>
            Division Communication et Contre-Information<br>
            Généré automatiquement avec Intelligence Artificielle Souveraine
        </p>
    </div>
</body>
</html>
"""
    
    return html