
from flask import Flask, render_template, request, jsonify, session
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, VideoUnplayable, CookieError
from transcript_analyzer import analyze_text, get_text_statistics, generate_summary, get_word_cloud_data, extract_words
from sentiment_analyzer import get_comprehensive_analysis
from database import init_database, save_analysis, get_recent_analyses, get_analysis_by_id, search_analyses, get_analysis_stats
from api import create_api_routes  # API REST Phase 4
from dashboard_service import dashboard_service  # Dashboard Analytics Phase 6
from report_export import report_export_service  # Report Export Phase 6
import logging
import os
from datetime import datetime

# Configuration de l'application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialisation de la base de données
init_database()

# Variable globale pour stocker temporairement la transcription
TEMP_TRANSCRIPT = ""

# Configuration de l'API REST (Phase 4)
api = create_api_routes(app)
logger.info("API REST configurée avec documentation Swagger disponible sur /api/docs/")

def extract_video_id(url_or_id):
    """Extrait l'ID vidéo d'une URL YouTube ou valide un ID direct"""
    if not url_or_id or not isinstance(url_or_id, str):
        raise ValueError("URL ou ID vidéo invalide")
    
    url_or_id = url_or_id.strip()
    
    # Si c'est une URL YouTube
    if "youtube.com" in url_or_id or "youtu.be" in url_or_id:
        import re
        match = re.search(r"(?:v=|/|embed/|watch\?v=)([0-9A-Za-z_-]{11})", url_or_id)
        if match:
            return match.group(1)
        else:
            raise ValueError("Impossible d'extraire l'ID de la vidéo depuis l'URL")
    
    # Si c'est déjà un ID (11 caractères)
    if len(url_or_id) == 11 and url_or_id.replace('-', '').replace('_', '').isalnum():
        return url_or_id
    
    raise ValueError("Format d'ID vidéo invalide (doit faire 11 caractères)")

@app.route("/")
def index():
    """Page d'accueil avec la transcription en session si elle existe"""
    transcript = session.get('transcript', '')
    return render_template('index.html', transcript=transcript, result=None, word_count=0)

@app.route("/transcribe", methods=["POST"])
def transcribe():
    global TEMP_TRANSCRIPT
    data = request.get_json()
    video_id = extract_video_id(data.get("video_id", ""))

    try:
        api = YouTubeTranscriptApi()

        transcript_data = None

        # 🔍 Essai auto avec ordre de priorité
        priority_langs = ["en", "fr"]
        try:
            transcript_data = api.fetch(video_id, languages=priority_langs)
            print(f"[INFO] Transcript trouvé avec priorité {priority_langs}")
        except Exception as e_auto:
            print(f"[INFO] Pas trouvé avec {priority_langs} : {e_auto}")

        # 🔄 Si échec, parcourir toutes les langues disponibles
        if transcript_data is None:
            transcript_list = api.list(video_id)
            for transcript in transcript_list:
                try:
                    transcript_data = transcript.fetch()
                    print(f"[INFO] Transcript trouvé en {transcript.language_code}")
                    break
                except Exception as e_try:
                    print(f"[WARN] Impossible de fetch transcript {transcript.language_code} : {e_try}")

        # ❌ Si toujours rien
        if transcript_data is None:
            return jsonify(success=False, error="Aucune transcription disponible")

        # ✅ Assemblage du texte
        TEMP_TRANSCRIPT = " ".join([entry.text for entry in transcript_data])
        TEMP_TRANSCRIPT = TEMP_TRANSCRIPT.replace("aujourd hui", "aujourd'hui")

        return jsonify(success=True, transcript=TEMP_TRANSCRIPT)

    except Exception as e:
        print(f"[ERREUR] Échec transcription : {e}")
        return jsonify(success=False, error=str(e))

@app.route("/analyze", methods=["POST"])
def analyze():
    """Analyse le texte selon le mode spécifié"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, error="Données manquantes")
            
        text = data.get("text", "").strip()
        mode = data.get("mode", "style")
        max_words = data.get("max_words", 30)  # Nouveau paramètre
        
        if not text:
            return jsonify(success=False, error="Texte à analyser manquant")
            
        if len(text) < 10:
            return jsonify(success=False, error="Le texte est trop court pour une analyse significative")
            
        # Validation du paramètre max_words
        max_words = max(1, min(200, int(max_words)))  # Entre 1 et 200
            
        logger.info(f"Analyse en mode '{mode}' (max_words={max_words}) d'un texte de {len(text)} caractères")
        
        try:
            # Analyse principale
            result, word_count = analyze_text(text, mode, max_words)
            
            # Statistiques détaillées
            words = extract_words(text)
            statistics = get_text_statistics(words, text)
            
            # Analyse de sentiment et lisibilité (Phase 3)
            comprehensive_analysis = get_comprehensive_analysis(text)
            
            # Sauvegarde en base de données
            video_id = session.get('video_id')
            video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None
            
            analysis_id = save_analysis(
                original_text=text,
                analysis_mode=mode,
                results=result,
                statistics=statistics,
                video_id=video_id,
                video_url=video_url,
                sentiment_data=comprehensive_analysis.get('sentiment'),
                readability_metrics=comprehensive_analysis.get('readability')
            )
            
            response_data = {
                'success': True,
                'result': result, 
                'word_count': word_count,
                'mode': mode,
                'text_length': len(text),
                'analysis_id': analysis_id
            }
            
            # Ajouter l'analyse complémentaire si disponible
            if comprehensive_analysis:
                response_data['advanced_analysis'] = comprehensive_analysis
                
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}")
            return jsonify(success=False, error=f"Erreur d'analyse: {str(e)}")
            
    except Exception as e:
        logger.error(f"Erreur inattendue dans analyze(): {e}")
        return jsonify(success=False, error=f"Erreur interne du serveur: {str(e)}")

@app.route("/statistics", methods=["POST"])
def get_statistics():
    """Récupère les statistiques détaillées d'un texte"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, error="Données manquantes")
            
        text = data.get("text", "").strip()
        if not text:
            return jsonify(success=False, error="Texte manquant")
        
        words = extract_words(text)
        stats = get_text_statistics(words, text)
        
        logger.info(f"Statistiques calculées pour un texte de {len(text)} caractères")
        
        return jsonify(
            success=True,
            statistics=stats
        )
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques: {e}")
        return jsonify(success=False, error=f"Erreur de calcul: {str(e)}")

@app.route("/summary", methods=["POST"])
def get_summary():
    """Génère un résumé automatique du texte"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, error="Données manquantes")
            
        text = data.get("text", "").strip()
        num_sentences = data.get("num_sentences", 3)
        
        if not text:
            return jsonify(success=False, error="Texte manquant")
            
        if len(text) < 100:
            return jsonify(success=False, error="Le texte est trop court pour générer un résumé")
        
        summary = generate_summary(text, num_sentences)
        
        logger.info(f"Résumé généré: {len(summary)} caractères depuis {len(text)} caractères")
        
        return jsonify(
            success=True,
            summary=summary,
            original_length=len(text),
            summary_length=len(summary),
            compression_ratio=round((1 - len(summary) / len(text)) * 100, 1)
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du résumé: {e}")
        return jsonify(success=False, error=f"Erreur de génération: {str(e)}")

@app.route("/wordcloud", methods=["POST"])
def get_wordcloud():
    """Génère les données pour un nuage de mots"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, error="Données manquantes")
            
        text = data.get("text", "").strip()
        max_words = data.get("max_words", 50)
        
        if not text:
            return jsonify(success=False, error="Texte manquant")
        
        words = extract_words(text)
        wordcloud_data = get_word_cloud_data(words, max_words)
        
        logger.info(f"Nuage de mots généré avec {len(wordcloud_data)} mots")
        
        return jsonify(
            success=True,
            wordcloud_data=wordcloud_data,
            total_words=len(words)
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du nuage de mots: {e}")
        return jsonify(success=False, error=f"Erreur de génération: {str(e)}")

@app.route("/history", methods=["GET"])
def get_history():
    """Récupère l'historique des analyses récentes"""
    try:
        limit = request.args.get('limit', 10, type=int)
        analyses = get_recent_analyses(limit=limit)
        
        # Conversion pour JSON
        history = []
        for analysis in analyses:
            history.append({
                'id': analysis.id,
                'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
                'analysis_mode': analysis.analysis_mode,
                'text_preview': analysis.original_text[:100] + ('...' if len(analysis.original_text) > 100 else ''),
                'video_id': analysis.video_id,
                'total_words': analysis.total_words,
                'sentiment_label': analysis.sentiment_label,
                'complexity_score': analysis.complexity_score
            })
        
        # Statistiques globales
        stats = get_analysis_stats()
        
        return jsonify(
            success=True,
            history=history,
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique: {e}")
        return jsonify(success=False, error=str(e))

@app.route("/history/<int:analysis_id>", methods=["GET"])
def get_analysis_details(analysis_id):
    """Récupère les détails d'une analyse spécifique"""
    try:
        analysis = get_analysis_by_id(analysis_id)
        
        if not analysis:
            return jsonify(success=False, error="Analyse introuvable")
            
        details = {
            'id': analysis.id,
            'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
            'analysis_mode': analysis.analysis_mode,
            'original_text': analysis.original_text,
            'video_id': analysis.video_id,
            'video_url': analysis.video_url,
            
            # Résultats d'analyse
            'word_frequency': analysis.word_frequency,
            'concepts_detected': analysis.concepts_detected,
            
            # Statistiques
            'total_words': analysis.total_words,
            'unique_words': analysis.unique_words,
            'sentences': analysis.sentences,
            'vocabulary_richness': analysis.vocabulary_richness,
            'reading_time_minutes': analysis.reading_time_minutes,
            'complexity_score': analysis.complexity_score,
            
            # Sentiment
            'sentiment_polarity': analysis.sentiment_polarity,
            'sentiment_subjectivity': analysis.sentiment_subjectivity,
            'sentiment_label': analysis.sentiment_label,
            'emotions_detected': analysis.emotions_detected,
            
            # Lisibilité
            'flesch_reading_ease': analysis.flesch_reading_ease,
            'flesch_kincaid_grade': analysis.flesch_kincaid_grade,
            
            # Résumé
            'summary_text': analysis.summary_text,
            'summary_compression_ratio': analysis.summary_compression_ratio
        }
        
        return jsonify(success=True, analysis=details)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'analyse {analysis_id}: {e}")
        return jsonify(success=False, error=str(e))

@app.route("/history/search", methods=["GET"])
def search_history():
    """Recherche dans l'historique des analyses"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify(success=False, error="Requête de recherche vide")
            
        analyses = search_analyses(query)
        
        results = []
        for analysis in analyses:
            results.append({
                'id': analysis.id,
                'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
                'analysis_mode': analysis.analysis_mode,
                'text_preview': analysis.original_text[:150] + ('...' if len(analysis.original_text) > 150 else ''),
                'video_id': analysis.video_id,
                'total_words': analysis.total_words,
                'sentiment_label': analysis.sentiment_label
            })
            
        return jsonify(success=True, results=results, query=query)
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {e}")
        return jsonify(success=False, error=str(e))

# === ROUTES DASHBOARD ANALYTICS (PHASE 6) ===

@app.route("/dashboard")
def dashboard():
    """Page du dashboard analytics"""
    return render_template('dashboard.html')

@app.route("/api/dashboard/data", methods=["GET"])
def get_dashboard_data():
    """API pour récupérer toutes les données du dashboard"""
    try:
        days = request.args.get('days', 30, type=int)
        
        dashboard_data = dashboard_service.generate_comprehensive_dashboard(days=days)
        
        if dashboard_data:
            return jsonify(success=True, data=dashboard_data)
        else:
            return jsonify(success=False, error="Impossible de générer les données du dashboard")
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données dashboard: {e}")
        return jsonify(success=False, error=str(e))

@app.route("/api/dashboard/kpis", methods=["GET"])
def get_dashboard_kpis():
    """API pour récupérer les KPIs uniquement"""
    try:
        days = request.args.get('days', 30, type=int)
        
        kpis = dashboard_service.get_global_kpis(days=days)
        
        if kpis:
            return jsonify(success=True, kpis=kpis)
        else:
            return jsonify(success=False, error="Impossible de calculer les KPIs")
            
    except Exception as e:
        logger.error(f"Erreur lors du calcul des KPIs: {e}")
        return jsonify(success=False, error=str(e))

@app.route("/api/dashboard/trends", methods=["GET"])
def get_dashboard_trends():
    """API pour récupérer les tendances temporelles"""
    try:
        days = request.args.get('days', 30, type=int)
        
        trends = dashboard_service.get_temporal_trends(days=days)
        
        if trends:
            return jsonify(success=True, trends=trends)
        else:
            return jsonify(success=False, error="Impossible de calculer les tendances")
            
    except Exception as e:
        logger.error(f"Erreur lors du calcul des tendances: {e}")
        return jsonify(success=False, error=str(e))

@app.route("/api/dashboard/insights", methods=["GET"])
def get_dashboard_insights():
    """API pour récupérer les insights sur le contenu"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        insights = dashboard_service.get_content_insights(limit=limit)
        
        if insights:
            return jsonify(success=True, insights=insights)
        else:
            return jsonify(success=False, error="Impossible de calculer les insights")
            
    except Exception as e:
        logger.error(f"Erreur lors du calcul des insights: {e}")
        return jsonify(success=False, error=str(e))

@app.route("/api/dashboard/export/<format_type>", methods=["GET"])
def export_dashboard_report(format_type):
    """Export du rapport dashboard en PDF ou Excel"""
    try:
        days = request.args.get('days', 30, type=int)
        
        if format_type.lower() not in ['pdf', 'excel']:
            return jsonify(success=False, error="Format non supporté. Utilisez 'pdf' ou 'excel'.")
        
        # Générer le rapport
        report_buffer = report_export_service.generate_dashboard_report(days=days, format_type=format_type)
        
        # Préparer la réponse
        filename = f"rapport_dashboard_{days}j_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format_type.lower() == 'pdf':
            filename += '.pdf'
            mimetype = 'application/pdf'
        else:
            filename += '.xlsx'
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        return app.response_class(
            report_buffer.getvalue(),
            mimetype=mimetype,
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Length': len(report_buffer.getvalue())
            }
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de l'export du rapport: {e}")
        return jsonify(success=False, error=str(e))

if __name__ == "__main__":
    app.run(debug=True, port=5001)
