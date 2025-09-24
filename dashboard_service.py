import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
from database import get_recent_analyses, get_analysis_by_id, get_db_session, Analysis
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

class DashboardService:
    def __init__(self):
        pass
    
    def get_global_kpis(self, days=30):
        """Récupère les KPIs globaux sur une période donnée"""
        try:
            db = get_db_session()
            
            # Date de référence
            since_date = datetime.now() - timedelta(days=days)
            
            # Requêtes pour les KPIs
            total_analyses = db.query(Analysis).filter(
                Analysis.created_at >= since_date
            ).count()
            
            total_analyses_ever = db.query(Analysis).count()
            
            # Mots totaux analysés
            words_result = db.query(func.sum(Analysis.total_words)).filter(
                Analysis.created_at >= since_date,
                Analysis.total_words.isnot(None)
            ).scalar() or 0
            
            # Temps de lecture total
            reading_time_result = db.query(func.sum(Analysis.reading_time_minutes)).filter(
                Analysis.created_at >= since_date,
                Analysis.reading_time_minutes.isnot(None)
            ).scalar() or 0
            
            # Moyenne de complexité
            avg_complexity = db.query(func.avg(Analysis.complexity_score)).filter(
                Analysis.created_at >= since_date,
                Analysis.complexity_score.isnot(None)
            ).scalar() or 0
            
            # Moyenne de sentiment
            avg_sentiment = db.query(func.avg(Analysis.sentiment_polarity)).filter(
                Analysis.created_at >= since_date,
                Analysis.sentiment_polarity.isnot(None)
            ).scalar() or 0
            
            # Distribution des sentiments
            sentiment_counts = db.query(
                Analysis.sentiment_label, 
                func.count(Analysis.id)
            ).filter(
                Analysis.created_at >= since_date,
                Analysis.sentiment_label.isnot(None)
            ).group_by(Analysis.sentiment_label).all()
            
            sentiment_distribution = {label: count for label, count in sentiment_counts}
            
            # Analyses par mode
            mode_counts = db.query(
                Analysis.analysis_mode, 
                func.count(Analysis.id)
            ).filter(
                Analysis.created_at >= since_date
            ).group_by(Analysis.analysis_mode).all()
            
            mode_distribution = {mode: count for mode, count in mode_counts}
            
            db.close()
            
            kpis = {
                'period': {
                    'days': days,
                    'start_date': since_date.isoformat(),
                    'end_date': datetime.now().isoformat()
                },
                'totals': {
                    'analyses_period': total_analyses,
                    'analyses_ever': total_analyses_ever,
                    'words_analyzed': int(words_result),
                    'reading_time_hours': round(reading_time_result / 60, 2) if reading_time_result else 0
                },
                'averages': {
                    'complexity_score': round(float(avg_complexity), 3),
                    'sentiment_polarity': round(float(avg_sentiment), 3),
                    'analyses_per_day': round(total_analyses / days, 2) if days > 0 else 0
                },
                'distributions': {
                    'sentiment': sentiment_distribution,
                    'analysis_mode': mode_distribution
                }
            }
            
            return kpis
            
        except Exception as e:
            logger.error(f"Erreur calcul KPIs: {e}")
            return None
    
    def get_temporal_trends(self, days=30):
        """Analyse les tendances temporelles"""
        try:
            since_date = datetime.now() - timedelta(days=days)
            analyses = get_recent_analyses(limit=1000)
            
            # Filtrer par période
            period_analyses = [
                a for a in analyses 
                if a.created_at and a.created_at >= since_date
            ]
            
            if not period_analyses:
                return {'message': 'Aucune donnée disponible pour la période'}
            
            # Grouper par jour
            daily_data = defaultdict(lambda: {
                'analyses_count': 0,
                'words_total': 0,
                'complexity_scores': [],
                'sentiment_scores': [],
                'reading_times': []
            })
            
            for analysis in period_analyses:
                day_key = analysis.created_at.strftime('%Y-%m-%d')
                daily_data[day_key]['analyses_count'] += 1
                
                if analysis.total_words:
                    daily_data[day_key]['words_total'] += analysis.total_words
                
                if analysis.complexity_score:
                    daily_data[day_key]['complexity_scores'].append(analysis.complexity_score)
                
                if analysis.sentiment_polarity is not None:
                    daily_data[day_key]['sentiment_scores'].append(analysis.sentiment_polarity)
                
                if analysis.reading_time_minutes:
                    daily_data[day_key]['reading_times'].append(analysis.reading_time_minutes)
            
            # Construire les séries temporelles
            trends = {
                'daily_analyses': [],
                'daily_words': [],
                'complexity_trend': [],
                'sentiment_trend': [],
                'reading_time_trend': []
            }
            
            # Trier les dates
            sorted_dates = sorted(daily_data.keys())
            
            for date in sorted_dates:
                day_data = daily_data[date]
                
                trends['daily_analyses'].append({
                    'date': date,
                    'count': day_data['analyses_count']
                })
                
                trends['daily_words'].append({
                    'date': date,
                    'words': day_data['words_total']
                })
                
                # Moyennes pour les métriques
                if day_data['complexity_scores']:
                    avg_complexity = np.mean(day_data['complexity_scores'])
                    trends['complexity_trend'].append({
                        'date': date,
                        'average': round(avg_complexity, 3)
                    })
                
                if day_data['sentiment_scores']:
                    avg_sentiment = np.mean(day_data['sentiment_scores'])
                    trends['sentiment_trend'].append({
                        'date': date,
                        'average': round(avg_sentiment, 3)
                    })
                
                if day_data['reading_times']:
                    avg_reading_time = np.mean(day_data['reading_times'])
                    trends['reading_time_trend'].append({
                        'date': date,
                        'average': round(avg_reading_time, 2)
                    })
            
            return trends
            
        except Exception as e:
            logger.error(f"Erreur calcul tendances: {e}")
            return None
    
    def get_content_insights(self, limit=100):
        """Analyse les insights sur le contenu"""
        try:
            analyses = get_recent_analyses(limit=limit)
            
            if not analyses:
                return {'message': 'Aucune analyse disponible'}
            
            # Métriques de base
            total_words = [a.total_words for a in analyses if a.total_words]
            unique_words = [a.unique_words for a in analyses if a.unique_words]
            vocab_richness = [a.vocabulary_richness for a in analyses if a.vocabulary_richness]
            complexities = [a.complexity_score for a in analyses if a.complexity_score]
            sentiments = [a.sentiment_polarity for a in analyses if a.sentiment_polarity is not None]
            
            insights = {
                'content_metrics': {
                    'avg_words_per_analysis': round(np.mean(total_words), 0) if total_words else 0,
                    'avg_unique_words': round(np.mean(unique_words), 0) if unique_words else 0,
                    'avg_vocabulary_richness': round(np.mean(vocab_richness), 2) if vocab_richness else 0,
                    'avg_complexity': round(np.mean(complexities), 3) if complexities else 0,
                    'avg_sentiment': round(np.mean(sentiments), 3) if sentiments else 0
                },
                'distributions': {
                    'word_count_ranges': self._get_word_count_distribution(total_words),
                    'complexity_ranges': self._get_complexity_distribution(complexities),
                    'sentiment_ranges': self._get_sentiment_distribution(sentiments)
                },
                'top_analyses': self._get_top_analyses(analyses),
                'content_patterns': self._analyze_content_patterns(analyses)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Erreur calcul insights: {e}")
            return None
    
    def _get_word_count_distribution(self, word_counts):
        """Distribue les comptes de mots par ranges"""
        if not word_counts:
            return {}
        
        ranges = {
            '0-500': 0,
            '501-1000': 0,
            '1001-2000': 0,
            '2001-5000': 0,
            '5000+': 0
        }
        
        for count in word_counts:
            if count <= 500:
                ranges['0-500'] += 1
            elif count <= 1000:
                ranges['501-1000'] += 1
            elif count <= 2000:
                ranges['1001-2000'] += 1
            elif count <= 5000:
                ranges['2001-5000'] += 1
            else:
                ranges['5000+'] += 1
        
        return ranges
    
    def _get_complexity_distribution(self, complexities):
        """Distribue les scores de complexité par ranges"""
        if not complexities:
            return {}
        
        ranges = {
            'Très faible (0-0.2)': 0,
            'Faible (0.2-0.4)': 0,
            'Modérée (0.4-0.6)': 0,
            'Élevée (0.6-0.8)': 0,
            'Très élevée (0.8-1.0)': 0
        }
        
        for score in complexities:
            if score <= 0.2:
                ranges['Très faible (0-0.2)'] += 1
            elif score <= 0.4:
                ranges['Faible (0.2-0.4)'] += 1
            elif score <= 0.6:
                ranges['Modérée (0.4-0.6)'] += 1
            elif score <= 0.8:
                ranges['Élevée (0.6-0.8)'] += 1
            else:
                ranges['Très élevée (0.8-1.0)'] += 1
        
        return ranges
    
    def _get_sentiment_distribution(self, sentiments):
        """Distribue les sentiments par ranges"""
        if not sentiments:
            return {}
        
        ranges = {
            'Très négatif (-1 à -0.5)': 0,
            'Négatif (-0.5 à -0.1)': 0,
            'Neutre (-0.1 à 0.1)': 0,
            'Positif (0.1 à 0.5)': 0,
            'Très positif (0.5 à 1)': 0
        }
        
        for score in sentiments:
            if score <= -0.5:
                ranges['Très négatif (-1 à -0.5)'] += 1
            elif score <= -0.1:
                ranges['Négatif (-0.5 à -0.1)'] += 1
            elif score <= 0.1:
                ranges['Neutre (-0.1 à 0.1)'] += 1
            elif score <= 0.5:
                ranges['Positif (0.1 à 0.5)'] += 1
            else:
                ranges['Très positif (0.5 à 1)'] += 1
        
        return ranges
    
    def _get_top_analyses(self, analyses):
        """Identifie les analyses les plus remarquables"""
        if not analyses:
            return {}
        
        # Tri par différents critères
        by_words = sorted([a for a in analyses if a.total_words], 
                         key=lambda x: x.total_words, reverse=True)[:3]
        
        by_complexity = sorted([a for a in analyses if a.complexity_score], 
                              key=lambda x: x.complexity_score, reverse=True)[:3]
        
        by_vocabulary = sorted([a for a in analyses if a.vocabulary_richness], 
                              key=lambda x: x.vocabulary_richness, reverse=True)[:3]
        
        return {
            'most_words': [{'id': a.id, 'words': a.total_words, 'created_at': a.created_at.isoformat()} 
                          for a in by_words],
            'most_complex': [{'id': a.id, 'complexity': a.complexity_score, 'created_at': a.created_at.isoformat()} 
                            for a in by_complexity],
            'richest_vocabulary': [{'id': a.id, 'richness': a.vocabulary_richness, 'created_at': a.created_at.isoformat()} 
                                  for a in by_vocabulary]
        }
    
    def _analyze_content_patterns(self, analyses):
        """Analyse les patterns dans le contenu"""
        try:
            # Analyse des modes d'analyse les plus utilisés
            mode_counts = Counter([a.analysis_mode for a in analyses])
            
            # Analyse des jours de la semaine
            weekday_counts = defaultdict(int)
            for analysis in analyses:
                if analysis.created_at:
                    weekday = analysis.created_at.strftime('%A')
                    weekday_counts[weekday] += 1
            
            # Analyse des heures de pic
            hour_counts = defaultdict(int)
            for analysis in analyses:
                if analysis.created_at:
                    hour = analysis.created_at.hour
                    hour_counts[hour] += 1
            
            return {
                'preferred_modes': dict(mode_counts),
                'active_weekdays': dict(weekday_counts),
                'peak_hours': dict(hour_counts),
                'total_patterns_analyzed': len(analyses)
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse patterns: {e}")
            return {}
    
    def generate_comprehensive_dashboard(self, days=30):
        """Génère un dashboard complet"""
        try:
            dashboard = {
                'generated_at': datetime.now().isoformat(),
                'period_days': days,
                'kpis': self.get_global_kpis(days),
                'trends': self.get_temporal_trends(days),
                'insights': self.get_content_insights(200)
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Erreur génération dashboard: {e}")
            return None

# Instance globale
dashboard_service = DashboardService()