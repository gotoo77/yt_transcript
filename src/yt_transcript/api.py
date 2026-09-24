from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from flask import Flask, abort, make_response, request
from flask.typing import ResponseReturnValue
from flask_restx import Api, Namespace, Resource, fields
from werkzeug.exceptions import HTTPException

from .database import get_analysis_by_id, get_recent_analyses, search_analyses
from .export_service import export_service

logger = logging.getLogger(__name__)

# Modèles de données pour Swagger
analysis_model = {
    "id": fields.Integer(required=True, description="ID unique de l'analyse"),
    "created_at": fields.DateTime(description="Date de création"),
    "analysis_mode": fields.String(description="Mode d'analyse utilisé"),
    "video_id": fields.String(description="ID de la vidéo YouTube"),
    "video_url": fields.String(description="URL de la vidéo"),
    "text_length": fields.Integer(description="Longueur du texte analysé"),
    "total_words": fields.Integer(description="Nombre total de mots"),
    "unique_words": fields.Integer(description="Nombre de mots uniques"),
    "vocabulary_richness": fields.Float(description="Richesse du vocabulaire (%)"),
    "sentiment_polarity": fields.Float(description="Polarité du sentiment (-1 à 1)"),
    "sentiment_subjectivity": fields.Float(description="Subjectivité (0 à 1)"),
    "sentiment_label": fields.String(description="Label du sentiment"),
    "complexity_score": fields.Float(description="Score de complexité"),
    "summary_text": fields.String(description="Résumé du texte"),
}

dashboard_model = {
    "summary": fields.Raw(description="Statistiques générales"),
    "trends": fields.Raw(description="Tendances temporelles"),
    "top_metrics": fields.Raw(description="Métriques importantes"),
}


def create_api_routes(app: Flask) -> Api:
    """Configure les routes de l'API REST"""

    api = Api(
        app,
        version="1.0",
        title="YouTube Transcript Analyzer API",
        description="API REST pour l'analyseur de transcriptions YouTube avec analyse de sentiment et métriques avancées",
        doc="/api/docs/",
        prefix="/api/v1",
    )

    # Namespace pour les analyses
    analyses_ns = Namespace("analyses", description="Opérations sur les analyses de transcriptions")
    api.add_namespace(analyses_ns)

    # Namespace pour les exports
    export_ns = Namespace("export", description="Export des analyses en différents formats")
    api.add_namespace(export_ns)

    # Namespace pour le dashboard
    dashboard_ns = Namespace("dashboard", description="Données analytiques et dashboard")
    api.add_namespace(dashboard_ns)

    # Modèles Swagger
    analysis_swagger = api.model("Analysis", analysis_model)
    dashboard_swagger = api.model("Dashboard", dashboard_model)

    @analyses_ns.route("/")
    class AnalysesList(Resource):
        @api.doc("list_analyses")
        @api.param("limit", "Nombre d'analyses à retourner (défaut: 20)", type=int)
        @api.param("offset", "Décalage pour la pagination (défaut: 0)", type=int)
        @api.marshal_list_with(analysis_swagger)
        def get(self) -> ResponseReturnValue:
            """Récupère la liste des analyses récentes"""
            try:
                limit = min(int(request.args.get("limit", 20)), 100)  # Max 100
                offset = int(request.args.get("offset", 0))

                analyses = get_recent_analyses(limit=limit, offset=offset)

                result = []
                for analysis in analyses:
                    result.append(
                        {
                            "id": analysis.id,
                            "created_at": analysis.created_at,
                            "analysis_mode": analysis.analysis_mode,
                            "video_id": analysis.video_id,
                            "video_url": analysis.video_url,
                            "text_length": analysis.text_length,
                            "total_words": analysis.total_words,
                            "unique_words": analysis.unique_words,
                            "vocabulary_richness": analysis.vocabulary_richness,
                            "sentiment_polarity": analysis.sentiment_polarity,
                            "sentiment_subjectivity": analysis.sentiment_subjectivity,
                            "sentiment_label": analysis.sentiment_label,
                            "complexity_score": analysis.complexity_score,
                            "summary_text": analysis.summary_text[:200] + "..."
                            if analysis.summary_text and len(analysis.summary_text) > 200
                            else analysis.summary_text,
                        }
                    )

                return result, 200

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Erreur API list analyses: {e}")
                abort(500, "Erreur interne du serveur")

    @analyses_ns.route("/<int:analysis_id>")
    class Analysis(Resource):
        @api.doc("get_analysis")
        @api.marshal_with(analysis_swagger)
        def get(self, analysis_id: int) -> ResponseReturnValue:
            """Récupère une analyse spécifique par son ID"""
            try:
                analysis = get_analysis_by_id(analysis_id)
                if not analysis:
                    abort(404, f"Analyse {analysis_id} non trouvée")

                return {
                    "id": analysis.id,
                    "created_at": analysis.created_at,
                    "analysis_mode": analysis.analysis_mode,
                    "video_id": analysis.video_id,
                    "video_url": analysis.video_url,
                    "text_length": analysis.text_length,
                    "total_words": analysis.total_words,
                    "unique_words": analysis.unique_words,
                    "vocabulary_richness": analysis.vocabulary_richness,
                    "sentiment_polarity": analysis.sentiment_polarity,
                    "sentiment_subjectivity": analysis.sentiment_subjectivity,
                    "sentiment_label": analysis.sentiment_label,
                    "complexity_score": analysis.complexity_score,
                    "summary_text": analysis.summary_text,
                }, 200

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Erreur API get analysis: {e}")
                abort(500, "Erreur interne du serveur")

    @analyses_ns.route("/search")
    class AnalysesSearch(Resource):
        @api.doc("search_analyses")
        @api.param("query", "Terme de recherche", required=True)
        @api.param("limit", "Nombre de résultats (défaut: 10)", type=int)
        @api.marshal_list_with(analysis_swagger)
        def get(self) -> ResponseReturnValue:
            """Recherche dans les analyses"""
            try:
                query = request.args.get("query", "").strip()
                if not query:
                    abort(400, "Paramètre 'query' requis")

                limit = min(int(request.args.get("limit", 10)), 50)
                analyses = search_analyses(query, limit=limit)

                result = []
                for analysis in analyses:
                    result.append(
                        {
                            "id": analysis.id,
                            "created_at": analysis.created_at,
                            "analysis_mode": analysis.analysis_mode,
                            "video_id": analysis.video_id,
                            "video_url": analysis.video_url,
                            "text_length": analysis.text_length,
                            "total_words": analysis.total_words,
                            "sentiment_label": analysis.sentiment_label,
                            "complexity_score": analysis.complexity_score,
                            "summary_text": analysis.summary_text[:150] + "..."
                            if analysis.summary_text and len(analysis.summary_text) > 150
                            else analysis.summary_text,
                        }
                    )

                return result, 200

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Erreur API search: {e}")
                abort(500, "Erreur interne du serveur")

    @export_ns.route("/json/<int:analysis_id>")
    class ExportJSON(Resource):
        @api.doc("export_json")
        def get(self, analysis_id: int) -> ResponseReturnValue:
            """Exporte une analyse au format JSON structuré"""
            try:
                json_data = export_service.export_analysis_json(analysis_id)
                if not json_data:
                    abort(404, f"Analyse {analysis_id} non trouvée ou erreur d'export")

                response = make_response(json_data)
                response.headers["Content-Type"] = "application/json; charset=utf-8"
                response.headers["Content-Disposition"] = (
                    f"attachment; filename=analysis_{analysis_id}.json"
                )
                return response

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Erreur export JSON: {e}")
                abort(500, "Erreur interne du serveur")

    @export_ns.route("/csv")
    class ExportCSV(Resource):
        @api.doc("export_csv")
        @api.param("ids", "IDs des analyses séparés par des virgules", required=True)
        def get(self) -> ResponseReturnValue:
            """Exporte plusieurs analyses au format CSV"""
            try:
                ids_param = request.args.get("ids", "")
                if not ids_param:
                    abort(400, "Paramètre 'ids' requis (ex: ids=1,2,3)")

                try:
                    analysis_ids = [
                        int(x.strip()) for x in ids_param.split(",") if x.strip().isdigit()
                    ]
                except ValueError:
                    abort(
                        400, "Format 'ids' invalide - utilisez des entiers séparés par des virgules"
                    )

                if not analysis_ids:
                    abort(400, "Aucun ID valide fourni")

                if len(analysis_ids) > 50:
                    abort(400, "Maximum 50 analyses par export CSV")

                csv_data = export_service.export_analysis_csv(analysis_ids)
                if not csv_data:
                    abort(500, "Erreur lors de la génération du CSV")

                response = make_response(csv_data)
                response.headers["Content-Type"] = "text/csv; charset=utf-8"
                response.headers["Content-Disposition"] = (
                    f"attachment; filename=analyses_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
                return response

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Erreur export CSV: {e}")
                abort(500, "Erreur interne du serveur")

    @dashboard_ns.route("/")
    class Dashboard(Resource):
        @api.doc("get_dashboard")
        @api.param("limit", "Nombre d'analyses à inclure (défaut: 50)", type=int)
        @api.marshal_with(dashboard_swagger)
        def get(self) -> ResponseReturnValue:
            """Récupère les données analytiques pour le dashboard"""
            try:
                limit = min(int(request.args.get("limit", 50)), 200)
                dashboard_data = export_service.create_dashboard_data(limit=limit)

                if not dashboard_data:
                    abort(500, "Erreur lors de la génération des données dashboard")

                return dashboard_data, 200

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Erreur API dashboard: {e}")
                abort(500, "Erreur interne du serveur")

    @dashboard_ns.route("/stats")
    class DashboardStats(Resource):
        @api.doc("get_stats")
        def get(self) -> ResponseReturnValue:
            """Récupère des statistiques rapides"""
            try:
                analyses = get_recent_analyses(limit=100)

                if not analyses:
                    return {
                        "total_analyses": 0,
                        "total_words": 0,
                        "average_sentiment": 0,
                        "average_complexity": 0,
                    }, 200

                total_words = sum([a.total_words or 0 for a in analyses])
                sentiments = [
                    a.sentiment_polarity for a in analyses if a.sentiment_polarity is not None
                ]
                complexities = [
                    a.complexity_score for a in analyses if a.complexity_score is not None
                ]

                stats: dict[str, Any] = {
                    "total_analyses": len(analyses),
                    "total_words": total_words,
                    "average_sentiment": sum(sentiments) / len(sentiments) if sentiments else 0,
                    "average_complexity": sum(complexities) / len(complexities)
                    if complexities
                    else 0,
                    "sentiment_distribution": {},
                }

                # Distribution des sentiments
                for analysis in analyses:
                    if analysis.sentiment_label:
                        label = analysis.sentiment_label
                        stats["sentiment_distribution"][label] = (
                            stats["sentiment_distribution"].get(label, 0) + 1
                        )

                return stats, 200

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Erreur API stats: {e}")
                abort(500, "Erreur interne du serveur")

    return api
