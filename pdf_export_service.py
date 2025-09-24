from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import io
import base64
import logging
from database import get_analysis_by_id, get_recent_analyses

logger = logging.getLogger(__name__)

class PDFExportService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Configure les styles personnalisés pour le PDF"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkgreen
        ))
        
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        ))
    
    def create_sentiment_chart(self, analysis):
        """Crée un graphique en secteurs pour les sentiments"""
        try:
            fig, ax = plt.subplots(figsize=(6, 4))
            
            # Données de sentiment
            sentiment_data = {
                'Polarité': analysis.sentiment_polarity or 0,
                'Subjectivité': analysis.sentiment_subjectivity or 0
            }
            
            if analysis.sentiment_label:
                colors_map = {'positive': 'green', 'negative': 'red', 'neutral': 'gray'}
                color = colors_map.get(analysis.sentiment_label.lower(), 'blue')
            else:
                color = 'blue'
            
            # Graphique en barres pour sentiment
            labels = list(sentiment_data.keys())
            values = list(sentiment_data.values())
            
            bars = ax.bar(labels, values, color=[color, 'lightblue'])
            ax.set_title(f'Analyse de Sentiment - {analysis.sentiment_label or "Non défini"}')
            ax.set_ylabel('Score')
            ax.set_ylim(-1, 1)
            
            # Ajouter les valeurs sur les barres
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                       f'{value:.2f}', ha='center', va='bottom')
            
            plt.tight_layout()
            
            # Sauvegarder en bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer
            
        except Exception as e:
            logger.error(f"Erreur création graphique sentiment: {e}")
            return None
    
    def create_metrics_chart(self, analysis):
        """Crée un graphique des métriques principales"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Graphique 1: Métriques textuelles
            metrics = {
                'Mots totaux': analysis.total_words or 0,
                'Mots uniques': analysis.unique_words or 0,
                'Phrases': analysis.sentences or 0
            }
            
            ax1.bar(metrics.keys(), metrics.values(), color=['skyblue', 'lightgreen', 'coral'])
            ax1.set_title('Métriques Textuelles')
            ax1.set_ylabel('Nombre')
            
            # Ajouter les valeurs sur les barres
            for i, (key, value) in enumerate(metrics.items()):
                ax1.text(i, value + max(metrics.values()) * 0.01, 
                        str(value), ha='center', va='bottom')
            
            # Graphique 2: Scores de qualité
            scores = {
                'Richesse vocab.': analysis.vocabulary_richness or 0,
                'Complexité': analysis.complexity_score or 0,
                'Flesch Ease': (analysis.flesch_reading_ease or 0) / 100  # Normaliser sur 1
            }
            
            bars = ax2.bar(scores.keys(), scores.values(), 
                          color=['gold', 'orange', 'lightcoral'])
            ax2.set_title('Scores de Qualité')
            ax2.set_ylabel('Score (normalisé)')
            ax2.set_ylim(0, 1)
            
            # Ajouter les valeurs
            for bar, (key, value) in zip(bars, scores.items()):
                height = bar.get_height()
                if key == 'Flesch Ease':
                    display_value = f'{value * 100:.1f}'
                else:
                    display_value = f'{value:.2f}'
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        display_value, ha='center', va='bottom')
            
            plt.tight_layout()
            
            # Sauvegarder en bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer
            
        except Exception as e:
            logger.error(f"Erreur création graphique métriques: {e}")
            return None
    
    def export_analysis_to_pdf(self, analysis_id, output_path=None):
        """Exporte une analyse vers un fichier PDF professionnel"""
        try:
            analysis = get_analysis_by_id(analysis_id)
            if not analysis:
                logger.error(f"Analyse {analysis_id} introuvable")
                return None
            
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"/tmp/analysis_{analysis_id}_{timestamp}.pdf"
            
            # Créer le document PDF
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            
            # 1. Titre principal
            title = Paragraph(
                f"Rapport d'Analyse - ID #{analysis.id}",
                self.styles['CustomTitle']
            )
            story.append(title)
            story.append(Spacer(1, 20))
            
            # 2. Informations générales
            info_data = [
                ['Date d\'analyse', analysis.created_at.strftime('%d/%m/%Y %H:%M') if analysis.created_at else 'N/A'],
                ['Mode d\'analyse', analysis.analysis_mode.title()],
                ['URL vidéo', analysis.video_url or 'N/A'],
                ['Longueur du texte', f"{analysis.text_length:,} caractères"]
            ]
            
            info_table = Table(info_data, colWidths=[2.5*inch, 3.5*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(Paragraph("Informations générales", self.styles['SectionHeader']))
            story.append(info_table)
            story.append(Spacer(1, 20))
            
            # 3. Métriques principales
            story.append(Paragraph("Métriques d'analyse", self.styles['SectionHeader']))
            
            metrics_data = [
                ['Mots totaux', f"{analysis.total_words or 0:,}"],
                ['Mots uniques', f"{analysis.unique_words or 0:,}"],
                ['Phrases', f"{analysis.sentences or 0}"],
                ['Richesse vocabulaire', f"{analysis.vocabulary_richness or 0:.2f}%"],
                ['Temps de lecture', f"{analysis.reading_time_minutes or 0:.1f} min"],
                ['Score de complexité', f"{analysis.complexity_score or 0:.2f}"]
            ]
            
            metrics_table = Table(metrics_data, colWidths=[2.5*inch, 1.5*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(metrics_table)
            story.append(Spacer(1, 20))
            
            # 4. Graphique des métriques
            metrics_chart = self.create_metrics_chart(analysis)
            if metrics_chart:
                story.append(Paragraph("Visualisation des métriques", self.styles['SectionHeader']))
                img = Image(metrics_chart, width=6*inch, height=2.5*inch)
                story.append(img)
                story.append(Spacer(1, 20))
            
            # 5. Analyse de sentiment
            if analysis.sentiment_polarity is not None:
                story.append(Paragraph("Analyse de sentiment", self.styles['SectionHeader']))
                
                sentiment_data = [
                    ['Polarité', f"{analysis.sentiment_polarity:.3f}"],
                    ['Subjectivité', f"{analysis.sentiment_subjectivity:.3f}"],
                    ['Classification', analysis.sentiment_label or 'Non défini']
                ]
                
                sentiment_table = Table(sentiment_data, colWidths=[2*inch, 2*inch])
                sentiment_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(sentiment_table)
                
                # Graphique de sentiment
                sentiment_chart = self.create_sentiment_chart(analysis)
                if sentiment_chart:
                    story.append(Spacer(1, 12))
                    img = Image(sentiment_chart, width=4*inch, height=2.5*inch)
                    story.append(img)
                
                story.append(Spacer(1, 20))
            
            # 6. Métriques de lisibilité
            if analysis.flesch_reading_ease is not None:
                story.append(Paragraph("Lisibilité du texte", self.styles['SectionHeader']))
                
                readability_data = [
                    ['Flesch Reading Ease', f"{analysis.flesch_reading_ease:.1f}"],
                    ['Flesch-Kincaid Grade', f"{analysis.flesch_kincaid_grade:.1f}"]
                ]
                
                readability_table = Table(readability_data, colWidths=[2.5*inch, 1.5*inch])
                readability_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightyellow),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(readability_table)
                story.append(Spacer(1, 20))
            
            # 7. Résumé du texte (si disponible)
            if analysis.summary_text:
                story.append(Paragraph("Résumé automatique", self.styles['SectionHeader']))
                
                summary_text = analysis.summary_text[:1000] + ('...' if len(analysis.summary_text) > 1000 else '')
                summary_para = Paragraph(summary_text, self.styles['Normal'])
                story.append(summary_para)
                
                if analysis.summary_compression_ratio:
                    compression_info = Paragraph(
                        f"<i>Taux de compression: {analysis.summary_compression_ratio:.1f}%</i>",
                        self.styles['Normal']
                    )
                    story.append(compression_info)
                
                story.append(Spacer(1, 20))
            
            # 8. Footer avec timestamp
            story.append(PageBreak())
            footer = Paragraph(
                f"<i>Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</i>",
                self.styles['Normal']
            )
            story.append(footer)
            
            # Construire le PDF
            doc.build(story)
            
            logger.info(f"PDF généré avec succès: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur génération PDF: {e}")
            return None

# Instance globale
pdf_export_service = PDFExportService()