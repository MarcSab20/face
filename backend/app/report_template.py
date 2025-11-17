"""
Template HTML V3 - Style Rapport Ministériel Narratif
"""

def generate_ministerial_report_html(report_data: dict) -> str:
    """Générer HTML rapport ministériel (style narratif)"""
    
    metadata = report_data.get('metadata', {})
    synthese_exec = report_data.get('synthese_executive', {}).get('synthese_executive', {})
    analyse_sit = report_data.get('analyse_situation', {}).get('analyse_situation', {})
    eval_menaces = report_data.get('evaluation_menaces', {}).get('evaluation_menaces', {})
    comments = report_data.get('synthese_commentaires', {})
    activists = report_data.get('activistes_critiques', {})
    reco = report_data.get('recommandations', {})
    viral = report_data.get('contenus_viraux', {})
    metrics = report_data.get('metriques', {})
    
    # Couleur criticité
    criticite = synthese_exec.get('niveau_criticite', 'MODÉRÉ')
    criticite_colors = {
        'CRITIQUE': '#dc2626',
        'ÉLEVÉ': '#ea580c',
        'MODÉRÉ': '#f59e0b',
        'FAIBLE': '#10b981'
    }
    criticite_color = criticite_colors.get(criticite, '#6b7280')
    generated_date = metadata.get('generated_at').strftime('%d/%m/%Y à %H:%M') if metadata.get('generated_at') else 'N/A'

    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>{metadata.get('title')}</title>
    <style>
        @page {{ size: A4; margin: 2.5cm; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.8;
            color: #1a1a1a;
            font-size: 11pt;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e3a8a 0%, #7c3aed 100%);
            color: white;
            padding: 30px;
            margin: -2.5cm -2.5cm 2cm -2.5cm;
            border-bottom: 5px solid #dc2626;
        }}
        
        .header h1 {{
            font-size: 24pt;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .classification {{
            background: #dc2626;
            color: white;
            padding: 8px 15px;
            font-weight: bold;
            text-align: center;
            margin: -2.5cm -2.5cm 2cm -2.5cm;
            font-size: 10pt;
        }}
        
        h2 {{
            color: #1e3a8a;
            font-size: 16pt;
            font-weight: bold;
            margin: 30px 0 15px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #7c3aed;
            page-break-after: avoid;
        }}
        
        h3 {{
            color: #4b5563;
            font-size: 13pt;
            font-weight: 600;
            margin: 20px 0 10px 0;
            page-break-after: avoid;
        }}
        
        p {{
            margin-bottom: 12px;
            text-align: justify;
            text-indent: 1.5em;
        }}
        
        p.no-indent {{
            text-indent: 0;
        }}
        
        .synthese-box {{
            background: #fef3c7;
            border-left: 5px solid #f59e0b;
            padding: 20px;
            margin: 20px 0;
            page-break-inside: avoid;
        }}
        
        .criticite-badge {{
            display: inline-block;
            background: {criticite_color};
            color: white;
            padding: 6px 15px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11pt;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        
        .metric-box {{
            background: #f3f4f6;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }}
        
        .metric-value {{
            font-size: 24pt;
            font-weight: bold;
            color: #1e3a8a;
        }}
        
        .metric-label {{
            font-size: 9pt;
            color: #6b7280;
            text-transform: uppercase;
            margin-top: 5px;
        }}
        
        .activist-card {{
            background: #fee2e2;
            border-left: 4px solid #dc2626;
            padding: 15px;
            margin: 10px 0;
            page-break-inside: avoid;
        }}
        
        .activist-card.known {{
            background: #fef3c7;
            border-left-color: #f59e0b;
        }}
        
        .recommendation-box {{
            background: #e0f2fe;
            border-left: 4px solid #0284c7;
            padding: 15px;
            margin: 15px 0;
            page-break-inside: avoid;
        }}
        
        .page-break {{
            page-break-before: always;
        }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e5e7eb;
            text-align: center;
            font-size: 9pt;
            color: #6b7280;
        }}
        
        .intro-letter {{
            font-style: italic;
            color: #4b5563;
            margin-bottom: 20px;
            padding-left: 20px;
            border-left: 3px solid #7c3aed;
        }}
    </style>
</head>
<body>
    <div class="classification">
        {metadata.get('classification', 'CONFIDENTIEL - DIFFUSION RESTREINTE')}
    </div>
    
    <div class="header">
        <h1>📊 {metadata.get('title')}</h1>
        <p style="opacity: 0.9; margin: 0;">
            Division Stratégie et Analyse - Présidence de la République
        </p>
    </div>
    
    <!-- Métriques clés -->
    <div class="metrics-grid">
        <div class="metric-box">
            <div class="metric-value">{metrics.get('total_publications', 0)}</div>
            <div class="metric-label">Publications</div>
        </div>
        <div class="metric-box">
            <div class="metric-value">{metrics.get('articles_lus', 0)}</div>
            <div class="metric-label">Articles Analysés</div>
        </div>
        <div class="metric-box">
            <div class="metric-value">{metrics.get('commentaires_analyses', 0)}</div>
            <div class="metric-label">Commentaires</div>
        </div>
    </div>
    
    <!-- SECTION 1: SYNTHÈSE EXÉCUTIVE -->
    <h2>I. SYNTHÈSE EXÉCUTIVE</h2>
    
    <p class="no-indent">
        <strong>Niveau de criticité:</strong> 
        <span class="criticite-badge">{criticite}</span>
    </p>
    
    <p class="no-indent" style="margin-top: 15px;">
        <strong>État de la paix publique:</strong> {synthese_exec.get('paix_publique', 'N/A')}<br>
        <strong>Menace pour l'État:</strong> {synthese_exec.get('menace_etat', 'N/A')}
    </p>
    
    <div style="margin-top: 20px; line-height: 1.9;">
        {self._format_narrative_text(synthese_exec.get('texte', 'Non disponible.'))}
    </div>
    
    <!-- SECTION 2: ANALYSE DE LA SITUATION -->
    <h2 class="page-break">II. ANALYSE DE LA SITUATION</h2>
    
    <h3>2.1. Vue d'ensemble</h3>
    <div>
        {self._format_narrative_text(analyse_sit.get('texte', 'Analyse non disponible.'))}
    </div>
    
    <h3>2.2. Synthèse de l'opinion publique (commentaires internautes)</h3>
    <div>
        {self._format_narrative_text(comments.get('synthese', 'Aucun commentaire analysé.'))}
    </div>
    
    {'<div class="synthese-box"><strong>⚠️ Appels à l action détectés:</strong> Des commentaires incitent potentiellement à la mobilisation ou à la contestation.</div>' if comments.get('appels_action') == 'OUI' else ''}
    
    <!-- SECTION 3: ÉVALUATION DES MENACES -->
    <h2 class="page-break">III. ÉVALUATION DES MENACES</h2>
    
    <div>
        {self._format_narrative_text(eval_menaces.get('texte', 'Évaluation non disponible.'))}
    </div>
    
    <!-- SECTION 4: ACTIVISTES CRITIQUES -->
    <h2>IV. COMPTES CRITIQUES IDENTIFIÉS</h2>
    
    <p class="no-indent">
        <strong>{activists.get('total', 0)} compte(s) critique(s)</strong> ont été identifiés, dont 
        <strong>{activists.get('connus', 0)} activiste(s) connu(s)</strong> sous surveillance et 
        <strong>{activists.get('nouveaux', 0)} nouveau(x) compte(s)</strong> à haut engagement.
    </p>
    
    {''.join([f'''
    <div class="activist-card {'known' if a.get('is_known') else ''}">
        <strong>{'🔴 ' if a.get('is_known') else '🆕 '}{a.get('nom')}</strong>
        {'<span style="color: #dc2626; font-weight: bold;"> [ACTIVISTE CONNU]</span>' if a.get('is_known') else ''}<br>
        <small>
            Publications: {a.get('contents')} | 
            Engagement total: {a.get('engagement'):,} | 
            Pic d'engagement: {a.get('peak_engagement', 0):,}
        </small>
    </div>
    ''' for a in activists.get('liste', [])[:10]])}
    
    <!-- SECTION 5: CONTENU VIRAL -->
    <h2>V. CONTENU LE PLUS VIRAL</h2>
    
    <p class="no-indent">
        Le contenu ayant généré le plus d'engagement est:
    </p>
    
    <div class="synthese-box">
        <strong>"{viral.get('plus_engage', {}).get('titre', 'N/A')}"</strong><br>
        <small>
            Auteur: {viral.get('plus_engage', {}).get('auteur', 'N/A')} | 
            Source: {viral.get('plus_engage', {}).get('source', 'N/A')} | 
            Engagement: {viral.get('plus_engage', {}).get('engagement', 0):,}
        </small>
    </div>
    
    <!-- SECTION 6: RECOMMANDATIONS -->
    <h2 class="page-break">VI. RECOMMANDATIONS OPÉRATIONNELLES</h2>
    
    <h3>6.1. Actions immédiates (0-24h)</h3>
    <div class="recommendation-box">
        {self._format_narrative_text(reco.get('actions_immediates', 'Aucune action urgente.'))}
    </div>
    
    <h3>6.2. Actions court terme (1-7 jours)</h3>
    <div class="recommendation-box">
        {self._format_narrative_text(reco.get('actions_court_terme', 'Surveillance continue.'))}
    </div>
    
    <h3>6.3. Actions moyen terme (1 mois)</h3>
    <div class="recommendation-box">
        {self._format_narrative_text(reco.get('actions_moyen_terme', 'Stratégie de long terme à définir.'))}
    </div>
    
    <div class="footer">
        <p>
            <strong>Rapport Stratégique Confidentiel</strong><br>
            Analyse Intelligence Artificielle Souveraine<br>
            Division Stratégie et Analyse - Présidence de la République<br>
            Généré le {generated_date}
        </p>
    </div>
</body>
</html>
"""
    
    return html

def _format_narrative_text(text: str) -> str:
    """Formater texte narratif en paragraphes HTML"""
    if not text:
        return '<p>Non disponible.</p>'
    
    # Séparer par doubles retours à la ligne
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    # Si pas de doubles retours, séparer par simples
    if len(paragraphs) == 1:
        paragraphs = [p.strip() for p in text.split('\n') if p.strip() and len(p.strip()) > 20]
    
    # Formater en HTML
    html_paragraphs = []
    for para in paragraphs:
        # Enlever les bullets si présents
        para = para.lstrip('-•*').strip()
        if para:
            html_paragraphs.append(f'<p>{para}</p>')
    
    return '\n'.join(html_paragraphs) if html_paragraphs else f'<p>{text}</p>'