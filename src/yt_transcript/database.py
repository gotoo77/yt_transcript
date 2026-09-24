from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, cast

from flask import Flask, current_app
from sqlalchemy import JSON, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    scoped_session,
    sessionmaker,
)

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class Analysis(Base):
    """Modèle pour stocker les analyses de transcriptions"""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Métadonnées de base
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    video_id: Mapped[str | None] = mapped_column(String, nullable=True)  # ID YouTube si applicable
    video_url: Mapped[str | None] = mapped_column(String, nullable=True)  # URL complète
    analysis_mode: Mapped[str] = mapped_column(String, nullable=False)  # "style" ou "concepts"

    # Contenu
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    text_length: Mapped[int] = mapped_column(Integer, nullable=False)

    # Résultats d'analyse
    word_frequency: Mapped[Any] = mapped_column(JSON, nullable=True)  # Résultats mode "style"
    concepts_detected: Mapped[Any] = mapped_column(JSON, nullable=True)  # Résultats mode "concepts"

    # Statistiques textuelles
    total_words: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unique_words: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sentences: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vocabulary_richness: Mapped[float | None] = mapped_column(Float, nullable=True)
    reading_time_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    complexity_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Analyse de sentiment (Phase 3)
    sentiment_polarity: Mapped[float | None] = mapped_column(Float, nullable=True)  # -1 à 1
    sentiment_subjectivity: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0 à 1
    sentiment_label: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # positive/negative/neutral
    emotions_detected: Mapped[Any] = mapped_column(JSON, nullable=True)  # Distribution des émotions

    # Métriques de lisibilité
    flesch_reading_ease: Mapped[float | None] = mapped_column(Float, nullable=True)
    flesch_kincaid_grade: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Résumé automatique
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_compression_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:
        return f"<Analysis(id={self.id}, mode={self.analysis_mode}, created_at={self.created_at})>"


def init_database(app: Flask) -> None:
    """Create tables and own one session registry per application."""
    url = app.config["DATABASE_URL"]
    engine = create_engine(url, echo=False)
    Base.metadata.create_all(bind=engine)
    factory = scoped_session(sessionmaker(bind=engine, expire_on_commit=False))
    app.extensions["database_engine"] = engine
    app.extensions["database_sessions"] = factory

    @app.teardown_appcontext
    def close_sessions(error: BaseException | None) -> None:
        factory.remove()


def get_db_session() -> Session:
    factory = cast(scoped_session[Session], current_app.extensions["database_sessions"])
    return factory()


def save_analysis(
    original_text: str,
    analysis_mode: str,
    results: list[Any],
    statistics: dict[str, Any],
    video_id: str | None = None,
    video_url: str | None = None,
    sentiment_data: dict[str, Any] | None = None,
    summary_data: dict[str, Any] | None = None,
    readability_metrics: dict[str, Any] | None = None,
) -> int | None:
    """Sauvegarde une analyse en base de données"""
    try:
        db = get_db_session()

        # Préparation des données selon le mode
        word_frequency = None
        concepts_detected = None

        if analysis_mode == "style":
            word_frequency = results
        elif analysis_mode == "concepts":
            concepts_detected = results

        # Création de l'enregistrement
        analysis = Analysis(
            video_id=video_id,
            video_url=video_url,
            analysis_mode=analysis_mode,
            original_text=original_text,
            text_length=len(original_text),
            # Résultats
            word_frequency=word_frequency,
            concepts_detected=concepts_detected,
            # Statistiques
            total_words=statistics.get("total_words"),
            unique_words=statistics.get("unique_words"),
            sentences=statistics.get("sentences"),
            vocabulary_richness=statistics.get("vocabulary_richness"),
            reading_time_minutes=statistics.get("reading_time_minutes"),
            complexity_score=statistics.get("complexity_score"),
            # Sentiment (si fourni)
            sentiment_polarity=sentiment_data.get("polarity") if sentiment_data else None,
            sentiment_subjectivity=sentiment_data.get("subjectivity") if sentiment_data else None,
            sentiment_label=sentiment_data.get("label") if sentiment_data else None,
            emotions_detected=sentiment_data.get("emotions") if sentiment_data else None,
            # Métriques de lisibilité
            flesch_reading_ease=readability_metrics.get("flesch_ease")
            if readability_metrics
            else None,
            flesch_kincaid_grade=readability_metrics.get("flesch_kincaid")
            if readability_metrics
            else None,
            # Résumé
            summary_text=summary_data.get("text") if summary_data else None,
            summary_compression_ratio=summary_data.get("compression_ratio")
            if summary_data
            else None,
        )

        db.add(analysis)
        db.commit()

        analysis_id = analysis.id
        db.close()

        logger.info(f"Analyse sauvegardée avec l'ID {analysis_id}")
        return analysis_id

    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde: {e}")
        if "db" in locals():
            db.rollback()
            db.close()
        return None


def get_recent_analyses(limit: int = 10, offset: int = 0) -> list[Analysis]:
    """Récupère les analyses récentes avec support de pagination"""
    try:
        db = get_db_session()
        analyses = (
            db.query(Analysis)
            .order_by(Analysis.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        db.close()
        return analyses
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des analyses: {e}")
        return []


def get_analysis_by_id(analysis_id: int) -> Analysis | None:
    """Récupère une analyse par son ID"""
    try:
        db = get_db_session()
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        db.close()
        return analysis
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'analyse {analysis_id}: {e}")
        return None


def search_analyses(query: str, limit: int = 20) -> list[Analysis]:
    """Recherche dans les analyses par contenu"""
    try:
        db = get_db_session()
        analyses = (
            db.query(Analysis)
            .filter(Analysis.original_text.contains(query) | Analysis.video_id.contains(query))
            .order_by(Analysis.created_at.desc())
            .limit(limit)
            .all()
        )
        db.close()
        return analyses
    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {e}")
        return []


def get_analysis_stats() -> dict[str, int | float]:
    """Récupère des statistiques globales sur les analyses"""
    try:
        db = get_db_session()

        total_analyses = db.query(Analysis).count()
        total_words_analyzed = db.query(Analysis.total_words).all()
        total_words = sum([w[0] for w in total_words_analyzed if w[0]])

        stats = {
            "total_analyses": total_analyses,
            "total_words_analyzed": total_words,
            "average_text_length": total_words / total_analyses if total_analyses > 0 else 0,
        }

        db.close()
        return stats

    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques: {e}")
        return {"total_analyses": 0, "total_words_analyzed": 0, "average_text_length": 0}
