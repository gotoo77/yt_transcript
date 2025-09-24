from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

# Configuration de la base de données
DATABASE_URL = "sqlite:///yt_analyzer.db"
engine = create_engine(DATABASE_URL, echo=False)

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class Analysis(Base):
    """Modèle pour stocker les analyses de transcriptions"""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Métadonnées de base
    created_at = Column(DateTime, default=datetime.utcnow)
    video_id = Column(String, nullable=True)  # ID YouTube si applicable
    video_url = Column(String, nullable=True)  # URL complète
    analysis_mode = Column(String, nullable=False)  # "style" ou "concepts"
    
    # Contenu
    original_text = Column(Text, nullable=False)
    text_length = Column(Integer, nullable=False)
    
    # Résultats d'analyse
    word_frequency = Column(JSON, nullable=True)  # Résultats mode "style"
    concepts_detected = Column(JSON, nullable=True)  # Résultats mode "concepts"
    
    # Statistiques textuelles
    total_words = Column(Integer, nullable=True)
    unique_words = Column(Integer, nullable=True)
    sentences = Column(Integer, nullable=True)
    vocabulary_richness = Column(Float, nullable=True)
    reading_time_minutes = Column(Float, nullable=True)
    complexity_score = Column(Float, nullable=True)
    
    # Analyse de sentiment (Phase 3)
    sentiment_polarity = Column(Float, nullable=True)  # -1 à 1
    sentiment_subjectivity = Column(Float, nullable=True)  # 0 à 1
    sentiment_label = Column(String, nullable=True)  # positive/negative/neutral
    emotions_detected = Column(JSON, nullable=True)  # Distribution des émotions
    
    # Métriques de lisibilité
    flesch_reading_ease = Column(Float, nullable=True)
    flesch_kincaid_grade = Column(Float, nullable=True)
    
    # Résumé automatique
    summary_text = Column(Text, nullable=True)
    summary_compression_ratio = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, mode={self.analysis_mode}, created_at={self.created_at})>"

def init_database():
    """Initialise la base de données en créant toutes les tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Base de données initialisée avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
        return False

def get_db_session():
    """Retourne une session de base de données"""
    return SessionLocal()

def save_analysis(
    original_text, analysis_mode, results, statistics, 
    video_id=None, video_url=None, sentiment_data=None, 
    summary_data=None, readability_metrics=None
):
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
            total_words=statistics.get('total_words'),
            unique_words=statistics.get('unique_words'),
            sentences=statistics.get('sentences'),
            vocabulary_richness=statistics.get('vocabulary_richness'),
            reading_time_minutes=statistics.get('reading_time_minutes'),
            complexity_score=statistics.get('complexity_score'),
            
            # Sentiment (si fourni)
            sentiment_polarity=sentiment_data.get('polarity') if sentiment_data else None,
            sentiment_subjectivity=sentiment_data.get('subjectivity') if sentiment_data else None,
            sentiment_label=sentiment_data.get('label') if sentiment_data else None,
            emotions_detected=sentiment_data.get('emotions') if sentiment_data else None,
            
            # Métriques de lisibilité
            flesch_reading_ease=readability_metrics.get('flesch_ease') if readability_metrics else None,
            flesch_kincaid_grade=readability_metrics.get('flesch_kincaid') if readability_metrics else None,
            
            # Résumé
            summary_text=summary_data.get('text') if summary_data else None,
            summary_compression_ratio=summary_data.get('compression_ratio') if summary_data else None
        )
        
        db.add(analysis)
        db.commit()
        
        analysis_id = analysis.id
        db.close()
        
        logger.info(f"Analyse sauvegardée avec l'ID {analysis_id}")
        return analysis_id
        
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return None

def get_recent_analyses(limit=10, offset=0):
    """Récupère les analyses récentes avec support de pagination"""
    try:
        db = get_db_session()
        analyses = db.query(Analysis).order_by(Analysis.created_at.desc()).offset(offset).limit(limit).all()
        db.close()
        return analyses
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des analyses: {e}")
        return []

def get_analysis_by_id(analysis_id):
    """Récupère une analyse par son ID"""
    try:
        db = get_db_session()
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        db.close()
        return analysis
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'analyse {analysis_id}: {e}")
        return None

def search_analyses(query, limit=20):
    """Recherche dans les analyses par contenu"""
    try:
        db = get_db_session()
        analyses = db.query(Analysis).filter(
            Analysis.original_text.contains(query) | 
            Analysis.video_id.contains(query)
        ).order_by(Analysis.created_at.desc()).limit(limit).all()
        db.close()
        return analyses
    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {e}")
        return []

def get_analysis_stats():
    """Récupère des statistiques globales sur les analyses"""
    try:
        db = get_db_session()
        
        total_analyses = db.query(Analysis).count()
        total_words_analyzed = db.query(Analysis.total_words).all()
        total_words = sum([w[0] for w in total_words_analyzed if w[0]])
        
        stats = {
            'total_analyses': total_analyses,
            'total_words_analyzed': total_words,
            'average_text_length': total_words / total_analyses if total_analyses > 0 else 0
        }
        
        db.close()
        return stats
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques: {e}")
        return {'total_analyses': 0, 'total_words_analyzed': 0, 'average_text_length': 0}