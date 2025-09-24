import json
import csv
from datetime import datetime
from io import StringIO, BytesIO
import logging
from database import get_analysis_by_id, get_recent_analyses

logger = logging.getLogger(__name__)

class ExportService:
    def __init__(self):
        pass
    
    def export_analysis_json(self, analysis_id):
        """Exporte une analyse au format JSON structuré"""
        try:
            analysis = get_analysis_by_id(analysis_id)
            if not analysis:
                return None
                
            export_data = {
                'metadata': {
                    'analysis_id': analysis.id,
                    'export_date': datetime.now().isoformat(),
                    'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
                    'analysis_mode': analysis.analysis_mode,
                    'video_info': {
                        'video_id': analysis.video_id,
                        'video_url': analysis.video_url
                    }
                },
                'content': {
                    'original_text': analysis.original_text,
                    'text_length': analysis.text_length
                },
                'analysis_results': {
                    'word_frequency': analysis.word_frequency,
                    'concepts_detected': analysis.concepts_detected
                },
                'statistics': {
                    'total_words': analysis.total_words,
                    'unique_words': analysis.unique_words,
                    'sentences': analysis.sentences,
                    'vocabulary_richness': analysis.vocabulary_richness,
                    'reading_time_minutes': analysis.reading_time_minutes,
                    'complexity_score': analysis.complexity_score
                },
                'sentiment_analysis': {
                    'polarity': analysis.sentiment_polarity,
                    'subjectivity': analysis.sentiment_subjectivity,
                    'label': analysis.sentiment_label,
                    'emotions': analysis.emotions_detected
                },
                'readability_metrics': {
                    'flesch_reading_ease': analysis.flesch_reading_ease,
                    'flesch_kincaid_grade': analysis.flesch_kincaid_grade
                },
                'summary': {
                    'text': analysis.summary_text,
                    'compression_ratio': analysis.summary_compression_ratio
                }
            }
            
            return json.dumps(export_data, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Erreur export JSON: {e}")
            return None
    
    def export_analysis_csv(self, analysis_ids):
        """Exporte plusieurs analyses au format CSV"""
        try:
            output = StringIO()
            writer = csv.writer(output)
            
            # En-têtes
            headers = [
                'ID', 'Date Création', 'Mode Analyse', 'ID Vidéo', 'URL Vidéo',
                'Longueur Texte', 'Mots Total', 'Mots Uniques', 'Phrases',
                'Richesse Vocabulaire (%)', 'Temps Lecture (min)', 'Score Complexité',
                'Sentiment Polarité', 'Sentiment Subjectivité', 'Label Sentiment',
                'Flesch Reading Ease', 'Flesch-Kincaid Grade',
                'Texte Résumé', 'Ratio Compression (%)'
            ]
            writer.writerow(headers)
            
            # Données
            for analysis_id in analysis_ids:
                analysis = get_analysis_by_id(analysis_id)
                if analysis:
                    row = [
                        analysis.id,
                        analysis.created_at.strftime('%Y-%m-%d %H:%M:%S') if analysis.created_at else '',
                        analysis.analysis_mode,
                        analysis.video_id or '',
                        analysis.video_url or '',
                        analysis.text_length,
                        analysis.total_words or 0,
                        analysis.unique_words or 0,
                        analysis.sentences or 0,
                        analysis.vocabulary_richness or 0,
                        analysis.reading_time_minutes or 0,
                        analysis.complexity_score or 0,
                        analysis.sentiment_polarity or 0,
                        analysis.sentiment_subjectivity or 0,
                        analysis.sentiment_label or '',
                        analysis.flesch_reading_ease or 0,
                        analysis.flesch_kincaid_grade or 0,
                        (analysis.summary_text or '')[:100] + '...' if analysis.summary_text and len(analysis.summary_text) > 100 else analysis.summary_text or '',
                        analysis.summary_compression_ratio or 0
                    ]
                    writer.writerow(row)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Erreur export CSV: {e}")
            return None
    
    def create_dashboard_data(self, limit=50):
        """Crée des données pour le dashboard analytique"""
        try:
            analyses = get_recent_analyses(limit=limit)
            
            dashboard_data = {
                'summary': {
                    'total_analyses': len(analyses),
                    'total_words_analyzed': sum([a.total_words or 0 for a in analyses]),
                    'average_complexity': sum([a.complexity_score or 0 for a in analyses]) / len(analyses) if analyses else 0,
                    'sentiment_distribution': {}
                },
                'trends': {
                    'analyses_per_day': {},
                    'complexity_over_time': [],
                    'sentiment_over_time': []
                },
                'top_metrics': {
                    'most_complex': None,
                    'longest_text': None,
                    'richest_vocabulary': None
                }
            }
            
            # Distribution des sentiments
            sentiment_counts = {}
            for analysis in analyses:
                if analysis.sentiment_label:
                    sentiment_counts[analysis.sentiment_label] = sentiment_counts.get(analysis.sentiment_label, 0) + 1
            dashboard_data['summary']['sentiment_distribution'] = sentiment_counts
            
            # Tendances temporelles
            for analysis in analyses:
                if analysis.created_at:
                    date_str = analysis.created_at.strftime('%Y-%m-%d')
                    dashboard_data['trends']['analyses_per_day'][date_str] = dashboard_data['trends']['analyses_per_day'].get(date_str, 0) + 1
                    
                    dashboard_data['trends']['complexity_over_time'].append({
                        'date': analysis.created_at.isoformat(),
                        'complexity': analysis.complexity_score or 0
                    })
                    
                    if analysis.sentiment_polarity is not None:
                        dashboard_data['trends']['sentiment_over_time'].append({
                            'date': analysis.created_at.isoformat(),
                            'polarity': analysis.sentiment_polarity
                        })
            
            # Top métriques
            if analyses:
                dashboard_data['top_metrics']['most_complex'] = {
                    'id': max(analyses, key=lambda x: x.complexity_score or 0).id,
                    'score': max([a.complexity_score or 0 for a in analyses])
                }
                dashboard_data['top_metrics']['longest_text'] = {
                    'id': max(analyses, key=lambda x: x.total_words or 0).id,
                    'words': max([a.total_words or 0 for a in analyses])
                }
                dashboard_data['top_metrics']['richest_vocabulary'] = {
                    'id': max(analyses, key=lambda x: x.vocabulary_richness or 0).id,
                    'richness': max([a.vocabulary_richness or 0 for a in analyses])
                }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Erreur création dashboard: {e}")
            return None

# Instance globale
export_service = ExportService()