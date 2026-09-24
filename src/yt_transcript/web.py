from __future__ import annotations

import logging
from datetime import datetime

from flask import Blueprint, abort, current_app, jsonify, render_template, request, session
from flask.typing import ResponseReturnValue
from youtube_transcript_api import YouTubeTranscriptApi

from .dashboard_service import dashboard_service  # Dashboard Analytics Phase 6
from .database import (
    get_analysis_by_id,
    get_analysis_stats,
    get_recent_analyses,
    save_transcript,
    list_transcripts,
    find_transcript,
    delete_transcript,
    save_analysis,
    search_analyses,
)
from .report_export import report_export_service  # Report Export Phase 6
from .sentiment_analyzer import get_comprehensive_analysis
from .transcript_analyzer import (
    analyze_text,
    extract_words,
    generate_summary,
    get_text_statistics,
    get_word_cloud_data,
)
from .video import extract_video_id

bp = Blueprint("web", __name__)
logger = logging.getLogger(__name__)


def validate_request() -> None:
    """Reject malformed input before business handlers and bound expensive work."""
    for name, maximum in (("limit", 1000), ("offset", 1_000_000), ("days", 3650)):
        value = request.args.get(name)
        if value is not None:
            try:
                number = int(value)
            except ValueError:
                abort(400, f"Paramètre {name} invalide")
            if number < (0 if name == "offset" else 1) or number > maximum:
                abort(400, f"Paramètre {name} hors limites")
    if request.method != "POST" or request.path not in {
        "/transcribe",
        "/analyze",
        "/statistics",
        "/summary",
        "/wordcloud",
    }:
        return
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, "Un objet JSON est requis")
    field = "video_id" if request.path == "/transcribe" else "text"
    if not isinstance(data.get(field), str) or not data[field].strip():
        abort(400, f"Champ {field} manquant ou invalide")
    if "mode" in data and data["mode"] not in ("style", "concepts"):
        abort(400, "Mode d'analyse invalide")
    for name, maximum in (("max_words", 200), ("num_sentences", 20)):
        if name in data:
            value = data[name]
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
                abort(400, f"Paramètre {name} invalide (1 à {maximum})")


@bp.route("/")
def index() -> ResponseReturnValue:
    """Page d'accueil avec la transcription en session si elle existe"""
    transcript = session.get("transcript", "")
    return render_template("index.html", transcript=transcript, result=None, word_count=0)


@bp.route("/transcribe", methods=["POST"])
def transcribe() -> ResponseReturnValue:
    data = request.get_json()
    try:
        video_id = extract_video_id(data["video_id"])
    except ValueError as error:
        return jsonify(success=False, error=str(error)), 400
    # Clear previous metadata even if the next request fails.
    session.pop("video_id", None)
    try:
        youtube = YouTubeTranscriptApi()
        transcript_data = None
        try:
            transcript_data = youtube.fetch(video_id, languages=["fr", "en"])
        except Exception:
            logger.info("Recherche des autres langues pour %s", video_id)
        if transcript_data is None:
            for transcript in youtube.list(video_id):
                try:
                    transcript_data = transcript.fetch()
                    break
                except Exception:
                    logger.info("Transcription indisponible en %s", transcript.language_code)
        if transcript_data is None:
            return jsonify(success=False, error="Aucune transcription disponible"), 404
        text = " ".join(entry.text for entry in transcript_data)
        text = text.replace("aujourd hui", "aujourd'hui")
        if not save_transcript(video_id, text):
            return jsonify(success=False, error="Sauvegarde de la transcription impossible"), 500
        session["video_id"] = video_id
        return jsonify(success=True, transcript=text)
    except Exception:
        logger.exception("Échec de récupération de la transcription")
        return jsonify(success=False, error="Impossible de récupérer la transcription YouTube"), 502


@bp.get("/transcripts")
def transcript_history() -> ResponseReturnValue:
    rows = list_transcripts()
    return jsonify(success=True, transcripts=[
        {"video_id": row.video_id, "created_at": row.created_at.isoformat(),
         "characters": len(row.text), "preview": row.text[:160]}
        for row in rows
    ])


@bp.get("/transcripts/<video_id>")
def transcript_detail(video_id: str) -> ResponseReturnValue:
    try:
        video_id = extract_video_id(video_id)
    except ValueError:
        abort(400, "Identifiant vidéo invalide")
    row = find_transcript(video_id)
    if row is None:
        abort(404, "Transcription introuvable")
    session["video_id"] = video_id
    return jsonify(success=True, video_id=row.video_id, transcript=row.text,
                   created_at=row.created_at.isoformat())


@bp.delete("/transcripts/<video_id>")
def transcript_remove(video_id: str) -> ResponseReturnValue:
    try:
        video_id = extract_video_id(video_id)
    except ValueError:
        abort(400, "Identifiant vidéo invalide")
    if not delete_transcript(video_id):
        abort(404, "Transcription introuvable")
    if session.get("video_id") == video_id:
        session.pop("video_id", None)
    return jsonify(success=True)


@bp.route("/analyze", methods=["POST"])
def analyze() -> ResponseReturnValue:
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
            return jsonify(
                success=False, error="Le texte est trop court pour une analyse significative"
            )

        # Validation du paramètre max_words
        max_words = max(1, min(200, int(max_words)))  # Entre 1 et 200

        logger.info(
            f"Analyse en mode '{mode}' (max_words={max_words}) d'un texte de {len(text)} caractères"
        )

        try:
            # Analyse principale
            result, word_count = analyze_text(text, mode, max_words)

            # Statistiques détaillées
            words = extract_words(text)
            statistics = get_text_statistics(words, text)

            # Analyse de sentiment et lisibilité (Phase 3)
            comprehensive_analysis = get_comprehensive_analysis(text)

            # Sauvegarde en base de données
            video_id = session.get("video_id")
            video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None

            analysis_id = save_analysis(
                original_text=text,
                analysis_mode=mode,
                results=result,
                statistics=statistics,
                video_id=video_id,
                video_url=video_url,
                sentiment_data=comprehensive_analysis.get("sentiment"),
                readability_metrics=comprehensive_analysis.get("readability"),
            )

            if analysis_id is None:
                return jsonify(success=False, error="Impossible de sauvegarder l'analyse"), 500

            response_data = {
                "success": True,
                "result": result,
                "word_count": word_count,
                "mode": mode,
                "text_length": len(text),
                "analysis_id": analysis_id,
            }

            # Ajouter l'analyse complémentaire si disponible
            if comprehensive_analysis:
                response_data["advanced_analysis"] = comprehensive_analysis

            return jsonify(response_data)

        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}")
            return jsonify(success=False, error="Erreur interne du serveur"), 500

    except Exception as e:
        logger.error(f"Erreur inattendue dans analyze(): {e}")
        return jsonify(success=False, error="Erreur interne du serveur"), 500


@bp.route("/statistics", methods=["POST"])
def get_statistics() -> ResponseReturnValue:
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

        return jsonify(success=True, statistics=stats)

    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques: {e}")
        return jsonify(success=False, error="Erreur interne du serveur"), 500


@bp.route("/summary", methods=["POST"])
def get_summary() -> ResponseReturnValue:
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
            compression_ratio=round((1 - len(summary) / len(text)) * 100, 1),
        )

    except Exception as e:
        logger.error(f"Erreur lors de la génération du résumé: {e}")
        return jsonify(success=False, error="Erreur interne du serveur"), 500


@bp.route("/wordcloud", methods=["POST"])
def get_wordcloud() -> ResponseReturnValue:
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

        return jsonify(success=True, wordcloud_data=wordcloud_data, total_words=len(words))

    except Exception as e:
        logger.error(f"Erreur lors de la génération du nuage de mots: {e}")
        return jsonify(success=False, error="Erreur interne du serveur"), 500


@bp.route("/history", methods=["GET"])
def get_history() -> ResponseReturnValue:
    """Récupère l'historique des analyses récentes"""
    try:
        limit = request.args.get("limit", 10, type=int)
        analyses = get_recent_analyses(limit=limit)

        # Conversion pour JSON
        history = []
        for analysis in analyses:
            history.append(
                {
                    "id": analysis.id,
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
                    "analysis_mode": analysis.analysis_mode,
                    "text_preview": analysis.original_text[:100]
                    + ("..." if len(analysis.original_text) > 100 else ""),
                    "video_id": analysis.video_id,
                    "total_words": analysis.total_words,
                    "sentiment_label": analysis.sentiment_label,
                    "complexity_score": analysis.complexity_score,
                }
            )

        # Statistiques globales
        stats = get_analysis_stats()

        return jsonify(success=True, history=history, stats=stats)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique: {e}")
        return jsonify(success=False, error="Erreur interne du serveur"), 500


@bp.route("/history/<int:analysis_id>", methods=["GET"])
def get_analysis_details(analysis_id: int) -> ResponseReturnValue:
    """Récupère les détails d'une analyse spécifique"""
    try:
        analysis = get_analysis_by_id(analysis_id)

        if not analysis:
            return jsonify(success=False, error="Analyse introuvable"), 404

        details = {
            "id": analysis.id,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            "analysis_mode": analysis.analysis_mode,
            "original_text": analysis.original_text,
            "video_id": analysis.video_id,
            "video_url": analysis.video_url,
            # Résultats d'analyse
            "word_frequency": analysis.word_frequency,
            "concepts_detected": analysis.concepts_detected,
            # Statistiques
            "total_words": analysis.total_words,
            "unique_words": analysis.unique_words,
            "sentences": analysis.sentences,
            "vocabulary_richness": analysis.vocabulary_richness,
            "reading_time_minutes": analysis.reading_time_minutes,
            "complexity_score": analysis.complexity_score,
            # Sentiment
            "sentiment_polarity": analysis.sentiment_polarity,
            "sentiment_subjectivity": analysis.sentiment_subjectivity,
            "sentiment_label": analysis.sentiment_label,
            "emotions_detected": analysis.emotions_detected,
            # Lisibilité
            "flesch_reading_ease": analysis.flesch_reading_ease,
            "flesch_kincaid_grade": analysis.flesch_kincaid_grade,
            # Résumé
            "summary_text": analysis.summary_text,
            "summary_compression_ratio": analysis.summary_compression_ratio,
        }

        return jsonify(success=True, analysis=details)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'analyse {analysis_id}: {e}")
        return jsonify(success=False, error="Erreur interne du serveur"), 500


@bp.route("/history/search", methods=["GET"])
def search_history() -> ResponseReturnValue:
    """Recherche dans l'historique des analyses"""
    try:
        query = request.args.get("q", "").strip()
        if not query:
            return jsonify(success=False, error="Requête de recherche vide")

        analyses = search_analyses(query)

        results = []
        for analysis in analyses:
            results.append(
                {
                    "id": analysis.id,
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
                    "analysis_mode": analysis.analysis_mode,
                    "text_preview": analysis.original_text[:150]
                    + ("..." if len(analysis.original_text) > 150 else ""),
                    "video_id": analysis.video_id,
                    "total_words": analysis.total_words,
                    "sentiment_label": analysis.sentiment_label,
                }
            )

        return jsonify(success=True, results=results, query=query)

    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {e}")
        return jsonify(success=False, error="Erreur interne du serveur"), 500


# === ROUTES DASHBOARD ANALYTICS (PHASE 6) ===


@bp.route("/dashboard")
def dashboard() -> ResponseReturnValue:
    """Page du dashboard analytics"""
    return render_template("dashboard.html")


@bp.route("/api/dashboard/data", methods=["GET"])
def get_dashboard_data() -> ResponseReturnValue:
    """API pour récupérer toutes les données du dashboard"""
    try:
        days = request.args.get("days", 30, type=int)

        dashboard_data = dashboard_service.generate_comprehensive_dashboard(days=days)

        if dashboard_data:
            return jsonify(success=True, data=dashboard_data)
        else:
            return jsonify(success=False, error="Impossible de générer les données du dashboard")

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données dashboard: {e}")
        return jsonify(success=False, error="Erreur interne du serveur"), 500


@bp.route("/api/dashboard/kpis", methods=["GET"])
def get_dashboard_kpis() -> ResponseReturnValue:
    """API pour récupérer les KPIs uniquement"""
    try:
        days = request.args.get("days", 30, type=int)

        kpis = dashboard_service.get_global_kpis(days=days)

        if kpis:
            return jsonify(success=True, kpis=kpis)
        else:
            return jsonify(success=False, error="Impossible de calculer les KPIs")

    except Exception as e:
        logger.error(f"Erreur lors du calcul des KPIs: {e}")
        return jsonify(success=False, error="Erreur interne du serveur"), 500


@bp.route("/api/dashboard/trends", methods=["GET"])
def get_dashboard_trends() -> ResponseReturnValue:
    """API pour récupérer les tendances temporelles"""
    try:
        days = request.args.get("days", 30, type=int)

        trends = dashboard_service.get_temporal_trends(days=days)

        if trends:
            return jsonify(success=True, trends=trends)
        else:
            return jsonify(success=False, error="Impossible de calculer les tendances")

    except Exception as e:
        logger.error(f"Erreur lors du calcul des tendances: {e}")
        return jsonify(success=False, error="Erreur interne du serveur"), 500


@bp.route("/api/dashboard/insights", methods=["GET"])
def get_dashboard_insights() -> ResponseReturnValue:
    """API pour récupérer les insights sur le contenu"""
    try:
        limit = request.args.get("limit", 100, type=int)

        insights = dashboard_service.get_content_insights(limit=limit)

        if insights:
            return jsonify(success=True, insights=insights)
        else:
            return jsonify(success=False, error="Impossible de calculer les insights")

    except Exception as e:
        logger.error(f"Erreur lors du calcul des insights: {e}")
        return jsonify(success=False, error="Erreur interne du serveur"), 500


@bp.route("/api/dashboard/export/<format_type>", methods=["GET"])
def export_dashboard_report(format_type: str) -> ResponseReturnValue:
    """Export du rapport dashboard en PDF ou Excel"""
    try:
        days = request.args.get("days", 30, type=int)

        if format_type.lower() not in ["pdf", "excel"]:
            return jsonify(success=False, error="Format non supporté. Utilisez 'pdf' ou 'excel'.")

        # Générer le rapport
        report_buffer = report_export_service.generate_dashboard_report(
            days=days, format_type=format_type
        )

        # Préparer la réponse
        filename = f"rapport_dashboard_{days}j_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if format_type.lower() == "pdf":
            filename += ".pdf"
            mimetype = "application/pdf"
        else:
            filename += ".xlsx"
            mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        return current_app.response_class(
            report_buffer.getvalue(),
            mimetype=mimetype,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(report_buffer.getvalue())),
            },
        )

    except Exception as e:
        logger.error(f"Erreur lors de l'export du rapport: {e}")
        return jsonify(success=False, error="Erreur interne du serveur"), 500
