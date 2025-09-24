from textblob import TextBlob
import re
import math
import logging
from collections import Counter
from transcript_analyzer import extract_words

logger = logging.getLogger(__name__)

def analyze_sentiment(text):
    """
    Analyse de sentiment avancée avec TextBlob
    Retourne la polarité, subjectivité et label
    """
    try:
        if not text or not text.strip():
            return None
            
        blob = TextBlob(text)
        
        # Analyse de base
        polarity = blob.sentiment.polarity  # -1 (négatif) à 1 (positif)
        subjectivity = blob.sentiment.subjectivity  # 0 (objectif) à 1 (subjectif)
        
        # Classification du sentiment
        if polarity > 0.1:
            label = "positive"
        elif polarity < -0.1:
            label = "negative"
        else:
            label = "neutral"
            
        # Analyse par phrases pour plus de détail
        sentences_sentiments = []
        for sentence in blob.sentences:
            if len(str(sentence).strip()) > 10:  # Ignorer les phrases trop courtes
                sent_polarity = sentence.sentiment.polarity
                sent_subjectivity = sentence.sentiment.subjectivity
                sentences_sentiments.append({
                    'text': str(sentence)[:100] + ('...' if len(str(sentence)) > 100 else ''),
                    'polarity': round(sent_polarity, 3),
                    'subjectivity': round(sent_subjectivity, 3)
                })
        
        # Statistiques sur les phrases
        positive_sentences = len([s for s in sentences_sentiments if s['polarity'] > 0.1])
        negative_sentences = len([s for s in sentences_sentiments if s['polarity'] < -0.1])
        neutral_sentences = len(sentences_sentiments) - positive_sentences - negative_sentences
        
        return {
            'polarity': round(polarity, 3),
            'subjectivity': round(subjectivity, 3),
            'label': label,
            'confidence': abs(polarity),  # Plus c'est éloigné de 0, plus c'est sûr
            'sentences_analysis': {
                'positive_count': positive_sentences,
                'negative_count': negative_sentences,
                'neutral_count': neutral_sentences,
                'total_sentences': len(sentences_sentiments),
                'details': sentences_sentiments[:10]  # Top 10 pour l'interface
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de sentiment: {e}")
        return None

def detect_emotions(text):
    """
    Détection basique d'émotions basée sur des mots-clés
    """
    try:
        if not text:
            return None
            
        text_lower = text.lower()
        
        # Dictionnaires d'émotions (français et anglais)
        emotion_words = {
            'joie': {
                'fr': ['heureux', 'joie', 'bonheur', 'content', 'ravi', 'enchanté', 'joyeux', 'satisfait', 'plaisir', 'sourire'],
                'en': ['happy', 'joy', 'pleasure', 'glad', 'cheerful', 'delighted', 'satisfied', 'smile', 'laugh', 'excited']
            },
            'tristesse': {
                'fr': ['triste', 'tristesse', 'chagrin', 'mélancolie', 'peine', 'déprime', 'malheureux', 'douleur'],
                'en': ['sad', 'sadness', 'sorrow', 'grief', 'melancholy', 'unhappy', 'depressed', 'pain', 'hurt']
            },
            'colère': {
                'fr': ['colère', 'énervé', 'furieux', 'rage', 'irrité', 'fâché', 'en colère', 'agacé'],
                'en': ['angry', 'anger', 'furious', 'rage', 'mad', 'annoyed', 'irritated', 'frustrated']
            },
            'peur': {
                'fr': ['peur', 'angoisse', 'anxieux', 'inquiet', 'terrifié', 'effrayé', 'stress', 'crainte'],
                'en': ['fear', 'afraid', 'scared', 'anxious', 'worried', 'terrified', 'stress', 'panic']
            },
            'surprise': {
                'fr': ['surpris', 'surprise', 'étonnant', 'inattendu', 'choqué', 'stupéfait'],
                'en': ['surprised', 'surprise', 'amazing', 'unexpected', 'shocked', 'astonished', 'wow']
            },
            'dégoût': {
                'fr': ['dégoût', 'dégoûtant', 'répugnant', 'écœurant', 'horrible'],
                'en': ['disgusting', 'disgusted', 'repulsive', 'revolting', 'horrible', 'awful']
            }
        }
        
        # Comptage des mots par émotions
        emotion_scores = {}
        total_emotion_words = 0
        
        for emotion, languages in emotion_words.items():
            score = 0
            for lang, words in languages.items():
                for word in words:
                    count = text_lower.count(word)
                    score += count
                    total_emotion_words += count
            emotion_scores[emotion] = score
        
        # Calcul des pourcentages
        if total_emotion_words > 0:
            emotion_percentages = {
                emotion: round((score / total_emotion_words) * 100, 1)
                for emotion, score in emotion_scores.items()
                if score > 0
            }
        else:
            emotion_percentages = {}
        
        # Émotion dominante
        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1]) if total_emotion_words > 0 else None
        
        return {
            'emotions': emotion_percentages,
            'dominant_emotion': dominant_emotion[0] if dominant_emotion and dominant_emotion[1] > 0 else None,
            'total_emotion_words': total_emotion_words,
            'emotional_intensity': round(total_emotion_words / len(text.split()) * 100, 1) if text else 0
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la détection d'émotions: {e}")
        return None

def calculate_readability_metrics(text):
    """
    Calcule diverses métriques de lisibilité
    """
    try:
        if not text or not text.strip():
            return None
            
        # Nettoyage du texte
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        words = extract_words(text)
        
        if not sentences or not words:
            return None
            
        # Statistiques de base
        num_sentences = len(sentences)
        num_words = len(words)
        num_syllables = estimate_syllables(' '.join(words))
        
        # Éviter la division par zéro
        if num_sentences == 0 or num_words == 0:
            return None
            
        # Moyennes
        avg_sentence_length = num_words / num_sentences
        avg_syllables_per_word = num_syllables / num_words
        
        # Flesch Reading Ease
        # Score = 206.835 - (1.015 × ASL) - (84.6 × ASW)
        # ASL = Average Sentence Length (mots par phrase)
        # ASW = Average Syllables per Word
        flesch_ease = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        
        # Flesch-Kincaid Grade Level
        # Grade = (0.39 × ASL) + (11.8 × ASW) - 15.59
        flesch_kincaid = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
        
        # Interprétation du Flesch Reading Ease
        if flesch_ease >= 90:
            ease_level = "Très facile"
        elif flesch_ease >= 80:
            ease_level = "Facile"
        elif flesch_ease >= 70:
            ease_level = "Assez facile"
        elif flesch_ease >= 60:
            ease_level = "Standard"
        elif flesch_ease >= 50:
            ease_level = "Assez difficile"
        elif flesch_ease >= 30:
            ease_level = "Difficile"
        else:
            ease_level = "Très difficile"
            
        # Statistiques supplémentaires
        word_lengths = [len(word) for word in words]
        avg_word_length = sum(word_lengths) / len(word_lengths)
        
        # Complexité lexicale (pourcentage de mots longs)
        long_words = len([w for w in words if len(w) > 6])
        lexical_complexity = (long_words / num_words) * 100
        
        return {
            'flesch_ease': round(flesch_ease, 1),
            'flesch_kincaid': round(flesch_kincaid, 1),
            'ease_level': ease_level,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'avg_syllables_per_word': round(avg_syllables_per_word, 2),
            'avg_word_length': round(avg_word_length, 1),
            'lexical_complexity': round(lexical_complexity, 1),
            'statistics': {
                'sentences': num_sentences,
                'words': num_words,
                'syllables': num_syllables,
                'long_words': long_words
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul des métriques de lisibilité: {e}")
        return None

def estimate_syllables(text):
    """
    Estimation du nombre de syllabes dans un texte
    Algorithme simplifié pour le français et l'anglais
    """
    if not text:
        return 0
        
    words = text.lower().split()
    total_syllables = 0
    
    for word in words:
        # Supprime les caractères non alphabétiques
        word = re.sub(r'[^a-záàâäéèêëíìîïóòôöúùûüýÿç]', '', word)
        if not word:
            continue
            
        # Compte les voyelles consécutives comme une syllabe
        vowels = 'aeiouyáàâäéèêëíìîïóòôöúùûüýÿ'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel
            
        # Règles spéciales
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1  # Le 'e' muet final
            
        if syllable_count == 0:
            syllable_count = 1  # Chaque mot a au moins une syllabe
            
        total_syllables += syllable_count
        
    return total_syllables

def get_comprehensive_analysis(text):
    """
    Analyse complète combinant sentiment, émotions et lisibilité
    """
    try:
        results = {}
        
        # Analyse de sentiment
        sentiment = analyze_sentiment(text)
        if sentiment:
            results['sentiment'] = sentiment
            
        # Détection d'émotions
        emotions = detect_emotions(text)
        if emotions:
            results['emotions'] = emotions
            
        # Métriques de lisibilité
        readability = calculate_readability_metrics(text)
        if readability:
            results['readability'] = readability
            
        logger.info(f"Analyse complète terminée pour un texte de {len(text)} caractères")
        return results
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse complète: {e}")
        return {}