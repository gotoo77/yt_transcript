from datetime import datetime
import numpy as np
from database import get_analysis_by_id
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class ComparisonService:
    def __init__(self):
        pass
    
    def compare_analyses(self, analysis_ids):
        """Compare plusieurs analyses et génère des métriques différentielles"""
        try:
            if len(analysis_ids) < 2:
                return {"error": "Au moins 2 analyses sont nécessaires pour une comparaison"}
            
            if len(analysis_ids) > 5:
                return {"error": "Maximum 5 analyses peuvent être comparées simultanément"}
            
            # Récupérer les analyses
            analyses = []
            for aid in analysis_ids:
                analysis = get_analysis_by_id(aid)
                if not analysis:
                    return {"error": f"Analyse {aid} introuvable"}
                analyses.append(analysis)
            
            comparison = {
                'comparison_id': f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'generated_at': datetime.now().isoformat(),
                'analyses_count': len(analyses),
                'analyses_overview': self._get_analyses_overview(analyses),
                'metrics_comparison': self._compare_metrics(analyses),
                'sentiment_comparison': self._compare_sentiment(analyses),
                'content_comparison': self._compare_content(analyses),
                'readability_comparison': self._compare_readability(analyses),
                'differential_insights': self._generate_differential_insights(analyses)
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Erreur comparaison analyses: {e}")
            return {"error": f"Erreur lors de la comparaison: {str(e)}"}
    
    def _get_analyses_overview(self, analyses):
        """Vue d'ensemble des analyses comparées"""
        overview = []
        
        for analysis in analyses:
            overview.append({
                'id': analysis.id,
                'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
                'analysis_mode': analysis.analysis_mode,
                'video_id': analysis.video_id,
                'video_url': analysis.video_url,
                'text_length': analysis.text_length,
                'summary_preview': (analysis.summary_text or '')[:100] + ('...' if analysis.summary_text and len(analysis.summary_text) > 100 else '')
            })
        
        return overview
    
    def _compare_metrics(self, analyses):
        """Compare les métriques principales"""
        metrics = {
            'text_metrics': {
                'total_words': [],
                'unique_words': [],
                'sentences': [],
                'text_length': []
            },
            'quality_metrics': {
                'vocabulary_richness': [],
                'complexity_score': [],
                'reading_time_minutes': []
            },
            'statistics': {},
            'rankings': {}
        }
        
        # Collecter les données
        for analysis in analyses:
            metrics['text_metrics']['total_words'].append({
                'id': analysis.id,
                'value': analysis.total_words or 0
            })
            metrics['text_metrics']['unique_words'].append({
                'id': analysis.id,
                'value': analysis.unique_words or 0
            })
            metrics['text_metrics']['sentences'].append({
                'id': analysis.id,
                'value': analysis.sentences or 0
            })
            metrics['text_metrics']['text_length'].append({
                'id': analysis.id,
                'value': analysis.text_length or 0
            })
            
            metrics['quality_metrics']['vocabulary_richness'].append({
                'id': analysis.id,
                'value': analysis.vocabulary_richness or 0
            })
            metrics['quality_metrics']['complexity_score'].append({
                'id': analysis.id,
                'value': analysis.complexity_score or 0
            })
            metrics['quality_metrics']['reading_time_minutes'].append({
                'id': analysis.id,
                'value': analysis.reading_time_minutes or 0
            })
        
        # Calculer les statistiques
        for category in ['text_metrics', 'quality_metrics']:
            metrics['statistics'][category] = {}
            for metric_name, metric_data in metrics[category].items():
                values = [item['value'] for item in metric_data]
                metrics['statistics'][category][metric_name] = {
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0,
                    'avg': np.mean(values) if values else 0,
                    'std': np.std(values) if values else 0,
                    'range': max(values) - min(values) if values else 0
                }
        
        # Générer les classements
        for category in ['text_metrics', 'quality_metrics']:
            metrics['rankings'][category] = {}
            for metric_name, metric_data in metrics[category].items():
                # Trier par valeur décroissante
                sorted_data = sorted(metric_data, key=lambda x: x['value'], reverse=True)
                metrics['rankings'][category][metric_name] = [
                    {'rank': i+1, 'id': item['id'], 'value': item['value']}
                    for i, item in enumerate(sorted_data)
                ]
        
        return metrics
    
    def _compare_sentiment(self, analyses):
        """Compare les analyses de sentiment"""
        sentiment_comparison = {
            'sentiment_data': [],
            'distribution': {
                'positive': 0,
                'negative': 0,
                'neutral': 0
            },
            'statistics': {},
            'sentiment_spread': 0
        }
        
        polarities = []
        subjectivities = []
        
        for analysis in analyses:
            sentiment_info = {
                'id': analysis.id,
                'polarity': analysis.sentiment_polarity,
                'subjectivity': analysis.sentiment_subjectivity,
                'label': analysis.sentiment_label,
                'emotions': analysis.emotions_detected
            }
            sentiment_comparison['sentiment_data'].append(sentiment_info)
            
            if analysis.sentiment_polarity is not None:
                polarities.append(analysis.sentiment_polarity)
            if analysis.sentiment_subjectivity is not None:
                subjectivities.append(analysis.sentiment_subjectivity)
            
            # Distribution
            if analysis.sentiment_label:
                label = analysis.sentiment_label.lower()
                if label in sentiment_comparison['distribution']:
                    sentiment_comparison['distribution'][label] += 1
        
        # Statistiques
        if polarities:
            sentiment_comparison['statistics'] = {
                'polarity': {
                    'min': min(polarities),
                    'max': max(polarities),
                    'avg': np.mean(polarities),
                    'std': np.std(polarities)
                },
                'subjectivity': {
                    'min': min(subjectivities) if subjectivities else 0,
                    'max': max(subjectivities) if subjectivities else 0,
                    'avg': np.mean(subjectivities) if subjectivities else 0,
                    'std': np.std(subjectivities) if subjectivities else 0
                }
            }
            
            # Écart de sentiment (diversité)
            sentiment_comparison['sentiment_spread'] = max(polarities) - min(polarities)
        
        return sentiment_comparison
    
    def _compare_content(self, analyses):
        """Compare le contenu des analyses"""
        content_comparison = {
            'mode_distribution': defaultdict(int),
            'word_frequency_overlap': {},
            'concepts_overlap': {},
            'content_similarity': []
        }
        
        # Distribution des modes
        for analysis in analyses:
            content_comparison['mode_distribution'][analysis.analysis_mode] += 1
        
        content_comparison['mode_distribution'] = dict(content_comparison['mode_distribution'])
        
        # Analyser les chevauchements dans les résultats d'analyse
        word_frequencies = []
        concepts_lists = []
        
        for analysis in analyses:
            if analysis.word_frequency:
                word_frequencies.append({
                    'id': analysis.id,
                    'words': analysis.word_frequency
                })
            
            if analysis.concepts_detected:
                concepts_lists.append({
                    'id': analysis.id,
                    'concepts': analysis.concepts_detected
                })
        
        # Calculer les similitudes de contenu
        if len(analyses) >= 2:
            for i in range(len(analyses)):
                for j in range(i + 1, len(analyses)):
                    similarity = self._calculate_content_similarity(analyses[i], analyses[j])
                    content_comparison['content_similarity'].append({
                        'analysis_1': analyses[i].id,
                        'analysis_2': analyses[j].id,
                        'similarity_score': similarity
                    })
        
        return content_comparison
    
    def _compare_readability(self, analyses):
        """Compare les métriques de lisibilité"""
        readability_comparison = {
            'flesch_ease_data': [],
            'flesch_kincaid_data': [],
            'statistics': {},
            'readability_levels': {}
        }
        
        flesch_ease_scores = []
        flesch_kincaid_scores = []
        
        for analysis in analyses:
            readability_comparison['flesch_ease_data'].append({
                'id': analysis.id,
                'score': analysis.flesch_reading_ease,
                'level': self._get_readability_level(analysis.flesch_reading_ease) if analysis.flesch_reading_ease else 'Non défini'
            })
            
            readability_comparison['flesch_kincaid_data'].append({
                'id': analysis.id,
                'grade': analysis.flesch_kincaid_grade
            })
            
            if analysis.flesch_reading_ease is not None:
                flesch_ease_scores.append(analysis.flesch_reading_ease)
            if analysis.flesch_kincaid_grade is not None:
                flesch_kincaid_scores.append(analysis.flesch_kincaid_grade)
        
        # Statistiques
        if flesch_ease_scores:
            readability_comparison['statistics'] = {
                'flesch_ease': {
                    'min': min(flesch_ease_scores),
                    'max': max(flesch_ease_scores),
                    'avg': np.mean(flesch_ease_scores),
                    'range': max(flesch_ease_scores) - min(flesch_ease_scores)
                },
                'flesch_kincaid': {
                    'min': min(flesch_kincaid_scores) if flesch_kincaid_scores else 0,
                    'max': max(flesch_kincaid_scores) if flesch_kincaid_scores else 0,
                    'avg': np.mean(flesch_kincaid_scores) if flesch_kincaid_scores else 0
                }
            }
        
        return readability_comparison
    
    def _calculate_content_similarity(self, analysis1, analysis2):
        """Calcule la similarité entre deux analyses"""
        try:
            similarity_score = 0.0
            factors = 0
            
            # Similarité basée sur les métriques
            if analysis1.vocabulary_richness and analysis2.vocabulary_richness:
                vocab_diff = abs(analysis1.vocabulary_richness - analysis2.vocabulary_richness)
                vocab_similarity = max(0, 1 - vocab_diff / 100)  # Normaliser sur 100%
                similarity_score += vocab_similarity
                factors += 1
            
            if analysis1.complexity_score and analysis2.complexity_score:
                complexity_diff = abs(analysis1.complexity_score - analysis2.complexity_score)
                complexity_similarity = max(0, 1 - complexity_diff)
                similarity_score += complexity_similarity
                factors += 1
            
            if analysis1.sentiment_polarity is not None and analysis2.sentiment_polarity is not None:
                sentiment_diff = abs(analysis1.sentiment_polarity - analysis2.sentiment_polarity)
                sentiment_similarity = max(0, 1 - sentiment_diff / 2)  # Normaliser sur [-1,1]
                similarity_score += sentiment_similarity
                factors += 1
            
            # Similarité de longueur de texte
            if analysis1.total_words and analysis2.total_words:
                words_ratio = min(analysis1.total_words, analysis2.total_words) / max(analysis1.total_words, analysis2.total_words)
                similarity_score += words_ratio
                factors += 1
            
            return round(similarity_score / factors if factors > 0 else 0, 3)
            
        except Exception as e:
            logger.error(f"Erreur calcul similarité: {e}")
            return 0.0
    
    def _get_readability_level(self, flesch_score):
        """Convertit un score Flesch en niveau de lisibilité"""
        if flesch_score >= 90:
            return "Très facile"
        elif flesch_score >= 80:
            return "Facile"
        elif flesch_score >= 70:
            return "Assez facile"
        elif flesch_score >= 60:
            return "Standard"
        elif flesch_score >= 50:
            return "Assez difficile"
        elif flesch_score >= 30:
            return "Difficile"
        else:
            return "Très difficile"
    
    def _generate_differential_insights(self, analyses):
        """Génère des insights différentiels"""
        insights = {
            'key_differences': [],
            'patterns': [],
            'recommendations': []
        }
        
        try:
            # Identifier les différences clés
            words_values = [a.total_words or 0 for a in analyses]
            complexity_values = [a.complexity_score or 0 for a in analyses]
            sentiment_values = [a.sentiment_polarity or 0 for a in analyses if a.sentiment_polarity is not None]
            
            # Différence de longueur
            if words_values:
                word_range = max(words_values) - min(words_values)
                if word_range > 1000:
                    insights['key_differences'].append({
                        'type': 'content_length',
                        'description': f"Forte variation de longueur: {word_range:,} mots d'écart",
                        'impact': 'high'
                    })
            
            # Différence de complexité
            if complexity_values:
                complexity_range = max(complexity_values) - min(complexity_values)
                if complexity_range > 0.3:
                    insights['key_differences'].append({
                        'type': 'complexity',
                        'description': f"Grande différence de complexité: {complexity_range:.2f} d'écart",
                        'impact': 'medium'
                    })
            
            # Différence de sentiment
            if sentiment_values and len(sentiment_values) >= 2:
                sentiment_range = max(sentiment_values) - min(sentiment_values)
                if sentiment_range > 1.0:
                    insights['key_differences'].append({
                        'type': 'sentiment',
                        'description': f"Sentiments très contrastés: {sentiment_range:.2f} d'écart",
                        'impact': 'high'
                    })
            
            # Patterns
            modes = [a.analysis_mode for a in analyses]
            if len(set(modes)) == 1:
                insights['patterns'].append("Toutes les analyses utilisent le même mode d'analyse")
            else:
                insights['patterns'].append("Modes d'analyse variés utilisés")
            
            # Recommandations
            if len(insights['key_differences']) > 0:
                insights['recommendations'].append("Analyser les causes des différences importantes identifiées")
            
            if len(analyses) > 2:
                insights['recommendations'].append("Considérer une analyse de corrélation pour identifier les relations entre métriques")
            
        except Exception as e:
            logger.error(f"Erreur génération insights: {e}")
        
        return insights

# Instance globale
comparison_service = ComparisonService()