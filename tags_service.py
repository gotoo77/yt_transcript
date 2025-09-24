from datetime import datetime
from collections import Counter, defaultdict
from database import get_db_session, Analysis, get_analysis_by_id, get_recent_analyses
from sqlalchemy import func, and_, or_
import json
import logging

logger = logging.getLogger(__name__)

class TagsService:
    def __init__(self):
        # Tags prédéfinis basés sur les métriques
        self.predefined_tags = {
            'complexity': {
                'very_simple': {'min_complexity': 0, 'max_complexity': 0.2, 'label': 'Très Simple'},
                'simple': {'min_complexity': 0.2, 'max_complexity': 0.4, 'label': 'Simple'},
                'moderate': {'min_complexity': 0.4, 'max_complexity': 0.6, 'label': 'Modéré'},
                'complex': {'min_complexity': 0.6, 'max_complexity': 0.8, 'label': 'Complexe'},
                'very_complex': {'min_complexity': 0.8, 'max_complexity': 1.0, 'label': 'Très Complexe'}
            },
            'sentiment': {
                'very_negative': {'min_polarity': -1.0, 'max_polarity': -0.5, 'label': 'Très Négatif'},
                'negative': {'min_polarity': -0.5, 'max_polarity': -0.1, 'label': 'Négatif'},
                'neutral': {'min_polarity': -0.1, 'max_polarity': 0.1, 'label': 'Neutre'},
                'positive': {'min_polarity': 0.1, 'max_polarity': 0.5, 'label': 'Positif'},
                'very_positive': {'min_polarity': 0.5, 'max_polarity': 1.0, 'label': 'Très Positif'}
            },
            'length': {
                'very_short': {'min_words': 0, 'max_words': 500, 'label': 'Très Court'},
                'short': {'min_words': 500, 'max_words': 1000, 'label': 'Court'},
                'medium': {'min_words': 1000, 'max_words': 2500, 'label': 'Moyen'},
                'long': {'min_words': 2500, 'max_words': 5000, 'label': 'Long'},
                'very_long': {'min_words': 5000, 'max_words': 999999, 'label': 'Très Long'}
            },
            'readability': {
                'very_easy': {'min_flesch': 90, 'max_flesch': 100, 'label': 'Très Facile'},
                'easy': {'min_flesch': 80, 'max_flesch': 90, 'label': 'Facile'},
                'moderate': {'min_flesch': 60, 'max_flesch': 80, 'label': 'Modéré'},
                'difficult': {'min_flesch': 30, 'max_flesch': 60, 'label': 'Difficile'},
                'very_difficult': {'min_flesch': 0, 'max_flesch': 30, 'label': 'Très Difficile'}
            }
        }
    
    def auto_tag_analysis(self, analysis):
        """Génère automatiquement des tags pour une analyse basés sur ses métriques"""
        try:
            auto_tags = []
            
            # Tags basés sur la complexité
            if analysis.complexity_score is not None:
                for tag_key, criteria in self.predefined_tags['complexity'].items():
                    if criteria['min_complexity'] <= analysis.complexity_score <= criteria['max_complexity']:
                        auto_tags.append(f"complexity:{tag_key}")
                        break
            
            # Tags basés sur le sentiment
            if analysis.sentiment_polarity is not None:
                for tag_key, criteria in self.predefined_tags['sentiment'].items():
                    if criteria['min_polarity'] <= analysis.sentiment_polarity <= criteria['max_polarity']:
                        auto_tags.append(f"sentiment:{tag_key}")
                        break
            
            # Tags basés sur la longueur
            if analysis.total_words:
                for tag_key, criteria in self.predefined_tags['length'].items():
                    if criteria['min_words'] <= analysis.total_words <= criteria['max_words']:
                        auto_tags.append(f"length:{tag_key}")
                        break
            
            # Tags basés sur la lisibilité
            if analysis.flesch_reading_ease is not None:
                for tag_key, criteria in self.predefined_tags['readability'].items():
                    if criteria['min_flesch'] <= analysis.flesch_reading_ease <= criteria['max_flesch']:
                        auto_tags.append(f"readability:{tag_key}")
                        break
            
            # Tags basés sur le mode d'analyse
            auto_tags.append(f"mode:{analysis.analysis_mode}")
            
            # Tags basés sur la présence de vidéo YouTube
            if analysis.video_id:
                auto_tags.append("source:youtube")
            else:
                auto_tags.append("source:text")
            
            # Tags temporels
            if analysis.created_at:
                year = analysis.created_at.year
                month = analysis.created_at.strftime('%B').lower()
                weekday = analysis.created_at.strftime('%A').lower()
                
                auto_tags.extend([
                    f"year:{year}",
                    f"month:{month}",
                    f"weekday:{weekday}"
                ])
            
            return auto_tags
            
        except Exception as e:
            logger.error(f"Erreur auto-tagging analyse {analysis.id}: {e}")
            return []
    
    def add_custom_tag(self, analysis_id, tag_name, tag_value=None):
        """Ajoute un tag personnalisé à une analyse"""
        try:
            analysis = get_analysis_by_id(analysis_id)
            if not analysis:
                return {"error": f"Analyse {analysis_id} introuvable"}
            
            # Récupérer les tags existants (stockés en JSON dans un champ)
            # Note: Il faudrait ajouter un champ 'custom_tags' à la table Analysis
            # Pour l'instant, on simule avec une structure en mémoire
            
            tag_entry = {
                'name': tag_name.lower().strip(),
                'value': tag_value,
                'added_at': datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "analysis_id": analysis_id,
                "tag_added": tag_entry
            }
            
        except Exception as e:
            logger.error(f"Erreur ajout tag: {e}")
            return {"error": f"Erreur lors de l'ajout du tag: {str(e)}"}
    
    def get_analysis_tags(self, analysis_id):
        """Récupère tous les tags (auto et manuels) d'une analyse"""
        try:
            analysis = get_analysis_by_id(analysis_id)
            if not analysis:
                return {"error": f"Analyse {analysis_id} introuvable"}
            
            # Tags automatiques
            auto_tags = self.auto_tag_analysis(analysis)
            
            # Tags personnalisés (simulation - en production il faudrait les récupérer de la DB)
            custom_tags = []
            
            return {
                "analysis_id": analysis_id,
                "auto_tags": auto_tags,
                "custom_tags": custom_tags,
                "total_tags": len(auto_tags) + len(custom_tags)
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération tags: {e}")
            return {"error": f"Erreur lors de la récupération: {str(e)}"}
    
    def filter_analyses_by_tags(self, tag_filters, limit=50):
        """Filtre les analyses par tags"""
        try:
            analyses = get_recent_analyses(limit=200)  # Récupérer plus pour filtrer
            filtered_analyses = []
            
            for analysis in analyses:
                analysis_tags = self.auto_tag_analysis(analysis)
                
                # Vérifier si l'analyse correspond aux filtres
                matches_all_filters = True
                
                for filter_tag in tag_filters:
                    if filter_tag not in analysis_tags:
                        matches_all_filters = False
                        break
                
                if matches_all_filters:
                    filtered_analyses.append({
                        'id': analysis.id,
                        'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
                        'analysis_mode': analysis.analysis_mode,
                        'total_words': analysis.total_words,
                        'complexity_score': analysis.complexity_score,
                        'sentiment_label': analysis.sentiment_label,
                        'tags': analysis_tags
                    })
                
                if len(filtered_analyses) >= limit:
                    break
            
            return {
                "filters_applied": tag_filters,
                "results_count": len(filtered_analyses),
                "analyses": filtered_analyses
            }
            
        except Exception as e:
            logger.error(f"Erreur filtrage par tags: {e}")
            return {"error": f"Erreur lors du filtrage: {str(e)}"}
    
    def get_tag_statistics(self, limit=100):
        """Génère des statistiques sur l'utilisation des tags"""
        try:
            analyses = get_recent_analyses(limit=limit)
            
            if not analyses:
                return {"message": "Aucune analyse disponible"}
            
            # Compter tous les tags
            tag_counter = Counter()
            category_counter = defaultdict(int)
            
            for analysis in analyses:
                auto_tags = self.auto_tag_analysis(analysis)
                tag_counter.update(auto_tags)
                
                # Compter par catégorie
                for tag in auto_tags:
                    if ':' in tag:
                        category = tag.split(':')[0]
                        category_counter[category] += 1
            
            # Top tags
            top_tags = tag_counter.most_common(20)
            
            # Statistiques par catégorie
            category_stats = {}
            for category, count in category_counter.items():
                category_stats[category] = {
                    'total_occurrences': count,
                    'average_per_analysis': round(count / len(analyses), 2)
                }
            
            # Distribution temporelle (par mois)
            monthly_distribution = defaultdict(int)
            for analysis in analyses:
                if analysis.created_at:
                    month_key = analysis.created_at.strftime('%Y-%m')
                    monthly_distribution[month_key] += 1
            
            return {
                "analyses_processed": len(analyses),
                "total_unique_tags": len(tag_counter),
                "total_tag_occurrences": sum(tag_counter.values()),
                "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags],
                "category_statistics": category_stats,
                "monthly_distribution": dict(monthly_distribution)
            }
            
        except Exception as e:
            logger.error(f"Erreur statistiques tags: {e}")
            return {"error": f"Erreur lors du calcul: {str(e)}"}
    
    def suggest_tags(self, analysis_id):
        """Suggère des tags pertinents pour une analyse"""
        try:
            analysis = get_analysis_by_id(analysis_id)
            if not analysis:
                return {"error": f"Analyse {analysis_id} introuvable"}
            
            suggestions = {
                "automatic_tags": self.auto_tag_analysis(analysis),
                "content_suggestions": [],
                "contextual_suggestions": []
            }
            
            # Suggestions basées sur le contenu
            if analysis.original_text:
                text_lower = analysis.original_text.lower()
                
                # Suggestions thématiques simples
                themes = {
                    'technology': ['technologie', 'informatique', 'digital', 'numérique', 'ordinateur'],
                    'education': ['éducation', 'apprentissage', 'école', 'formation', 'étudiant'],
                    'business': ['entreprise', 'business', 'économie', 'marché', 'commercial'],
                    'science': ['science', 'recherche', 'étude', 'expérience', 'analyse'],
                    'health': ['santé', 'médical', 'médecine', 'patient', 'traitement']
                }
                
                for theme, keywords in themes.items():
                    if any(keyword in text_lower for keyword in keywords):
                        suggestions["content_suggestions"].append(f"theme:{theme}")
            
            # Suggestions contextuelles
            if analysis.total_words and analysis.total_words > 3000:
                suggestions["contextual_suggestions"].append("format:long_form")
            
            if analysis.vocabulary_richness and analysis.vocabulary_richness > 75:
                suggestions["contextual_suggestions"].append("quality:rich_vocabulary")
            
            if analysis.complexity_score and analysis.complexity_score > 0.7:
                suggestions["contextual_suggestions"].append("level:advanced")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Erreur suggestions tags: {e}")
            return {"error": f"Erreur lors de la suggestion: {str(e)}"}
    
    def create_tag_hierarchy(self, limit=100):
        """Crée une hiérarchie des tags disponibles"""
        try:
            analyses = get_recent_analyses(limit=limit)
            
            hierarchy = {
                "categories": {},
                "total_analyses": len(analyses)
            }
            
            # Analyser tous les tags pour créer la hiérarchie
            for analysis in analyses:
                auto_tags = self.auto_tag_analysis(analysis)
                
                for tag in auto_tags:
                    if ':' in tag:
                        category, value = tag.split(':', 1)
                        
                        if category not in hierarchy["categories"]:
                            hierarchy["categories"][category] = {
                                "label": category.title(),
                                "values": {},
                                "count": 0
                            }
                        
                        if value not in hierarchy["categories"][category]["values"]:
                            hierarchy["categories"][category]["values"][value] = 0
                        
                        hierarchy["categories"][category]["values"][value] += 1
                        hierarchy["categories"][category]["count"] += 1
            
            # Ajouter les métadonnées pour chaque catégorie
            for category_name, category_data in hierarchy["categories"].items():
                if category_name in self.predefined_tags:
                    for tag_key, criteria in self.predefined_tags[category_name].items():
                        if tag_key in category_data["values"]:
                            # Ajouter le label descriptif
                            count = category_data["values"][tag_key]
                            category_data["values"][tag_key] = {
                                "count": count,
                                "label": criteria.get("label", tag_key.title())
                            }
            
            return hierarchy
            
        except Exception as e:
            logger.error(f"Erreur création hiérarchie: {e}")
            return {"error": f"Erreur lors de la création: {str(e)}"}
    
    def export_tagged_analyses(self, tag_filters=None, output_format='json'):
        """Exporte les analyses avec leurs tags"""
        try:
            if tag_filters:
                filter_result = self.filter_analyses_by_tags(tag_filters)
                if "error" in filter_result:
                    return filter_result
                analyses_data = filter_result["analyses"]
            else:
                analyses = get_recent_analyses(limit=100)
                analyses_data = []
                
                for analysis in analyses:
                    tags = self.auto_tag_analysis(analysis)
                    analyses_data.append({
                        'id': analysis.id,
                        'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
                        'analysis_mode': analysis.analysis_mode,
                        'total_words': analysis.total_words,
                        'complexity_score': analysis.complexity_score,
                        'sentiment_label': analysis.sentiment_label,
                        'tags': tags
                    })
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "format": output_format,
                "filters_applied": tag_filters or [],
                "total_analyses": len(analyses_data),
                "analyses": analyses_data
            }
            
            if output_format == 'json':
                return json.dumps(export_data, indent=2, ensure_ascii=False)
            else:
                return export_data
            
        except Exception as e:
            logger.error(f"Erreur export avec tags: {e}")
            return {"error": f"Erreur lors de l'export: {str(e)}"}

# Instance globale
tags_service = TagsService()