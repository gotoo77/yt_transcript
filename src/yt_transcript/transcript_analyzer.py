from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)

# Mots vides français étendus et améliorés
EXCLUDED_WORDS_FR = {
    # === CONTRACTIONS ET ÉLISIONS ===
    "c'est",
    "c'était",
    "j'ai",
    "j'avais",
    "j'étais",
    "n'est",
    "n'était",
    "n'ai",
    "n'avais",
    "l'on",
    "l'a",
    "l'ai",
    "l'avait",
    "l'était",
    "d'un",
    "d'une",
    "d'être",
    "d'avoir",
    "qu'on",
    "qu'il",
    "qu'elle",
    "qu'ils",
    "qu'elles",
    "s'il",
    "s'ils",
    "t'es",
    "t'as",
    "m'a",
    "m'as",
    # === INTERJECTIONS ET EXPRESSIONS ORALES ===
    "euh",
    "donc",
    "voilà",
    "hein",
    "bah",
    "ben",
    "alors",
    "quoi",
    "oui",
    "non",
    "si",
    "ah",
    "oh",
    "hop",
    "allez",
    "bon",
    "bien",
    "enfin",
    "bref",
    "voici",
    "tiens",
    "dis",
    "disons",
    "genre",
    "franchement",
    "carrément",
    "vraiment",
    "clairement",
    "effectivement",
    "exactement",
    # === MOTS TRÈS COMMUNS MAIS PEU INFORMATIFS ===
    "coup",
    "truc",
    "trucs",
    "chose",
    "choses",
    "machin",
    "bidule",
    "etc",
    "cetera",
    "quelque",
    "fois",
    "tout",
    "toute",
    "tous",
    "toutes",
    "chaque",
    "autre",
    "autres",
    "point",
    "pas",
    "peu",
    "beaucoup",
    "même",
    "cas",
    "ça",
    "cela",
    "ceci",
    "celle",
    "celui",
    "cette",
    "ces",
    "ce",
    "cet",
    "tel",
    "telle",
    "tels",
    "telles",
    "ainsi",
    "comme",
    "comment",
    "où",
    "quand",
    "pourquoi",
    "que",
    "qui",
    "dont",
    "lequel",
    "laquelle",
    "lesquels",
    "lesquelles",
    # === ARTICLES ET PRÉPOSITIONS ===
    "le",
    "la",
    "les",
    "un",
    "une",
    "des",
    "du",
    "de",
    "dans",
    "sur",
    "avec",
    "pour",
    "par",
    "sans",
    "sous",
    "vers",
    "chez",
    "depuis",
    "pendant",
    "avant",
    "après",
    "entre",
    "parmi",
    "selon",
    "contre",
    "malgré",
    "sauf",
    "hormis",
    "outre",
    "moyennant",
    # === PRONOMS ===
    "je",
    "tu",
    "il",
    "elle",
    "nous",
    "vous",
    "ils",
    "elles",
    "on",
    "se",
    "me",
    "te",
    "lui",
    "leur",
    "leurs",
    "y",
    "en",
    "moi",
    "toi",
    "soi",
    "eux",
    "mon",
    "ma",
    "mes",
    "ton",
    "ta",
    "tes",
    "son",
    "sa",
    "ses",
    "notre",
    "nos",
    "votre",
    "vos",
    "celui-ci",
    "celle-ci",
    # === VERBE ÊTRE (TOUTES LES FORMES) ===
    "être",
    "suis",
    "es",
    "est",
    "sommes",
    "êtes",
    "sont",
    "étais",
    "était",
    "étions",
    "étiez",
    "étaient",
    "fus",
    "fut",
    "fûmes",
    "fûtes",
    "furent",
    "serai",
    "seras",
    "sera",
    "serons",
    "serez",
    "seront",
    "serais",
    "serait",
    "serions",
    "seriez",
    "seraient",
    "sois",
    "soit",
    "soyons",
    "soyez",
    "soient",
    "fusse",
    "fusses",
    "fût",
    "fussions",
    "fussiez",
    "fussent",
    "été",
    "étant",
    # === VERBE AVOIR (TOUTES LES FORMES) ===
    "avoir",
    "ai",
    "as",
    "a",
    "avons",
    "avez",
    "ont",
    "avais",
    "avait",
    "avions",
    "aviez",
    "avaient",
    "eus",
    "eut",
    "eûmes",
    "eûtes",
    "eurent",
    "aurai",
    "auras",
    "aura",
    "aurons",
    "aurez",
    "auront",
    "aurais",
    "aurait",
    "aurions",
    "auriez",
    "auraient",
    "aie",
    "aies",
    "ait",
    "ayons",
    "ayez",
    "aient",
    "eusse",
    "eusses",
    "eût",
    "eussions",
    "eussiez",
    "eussent",
    "eu",
    "ayant",
    # === AUTRES VERBES TRÈS FRÉQUENTS ===
    # FAIRE
    "faire",
    "fais",
    "fait",
    "faisons",
    "faites",
    "font",
    "faisais",
    "faisait",
    "faisions",
    "faisiez",
    "faisaient",
    "fis",
    "fit",
    "fîmes",
    "fîtes",
    "firent",
    "ferai",
    "feras",
    "fera",
    "ferons",
    "ferez",
    "feront",
    "ferais",
    "ferait",
    "ferions",
    "feriez",
    "feraient",
    "fasse",
    "fasses",
    "fassions",
    "fassiez",
    "fassent",
    "fisse",
    "fisses",
    "fît",
    "fissions",
    "fissiez",
    "fissent",
    "faite",
    "faites",
    "faisant",
    # ALLER
    "aller",
    "vais",
    "va",
    "allons",
    "allez",
    "vont",
    "allais",
    "allait",
    "allions",
    "alliez",
    "allaient",
    "allai",
    "allas",
    "alla",
    "allâmes",
    "allâtes",
    "allèrent",
    "irai",
    "iras",
    "ira",
    "irons",
    "irez",
    "iront",
    "irais",
    "irait",
    "irions",
    "iriez",
    "iraient",
    "aille",
    "ailles",
    "allions",
    "alliez",
    "aillent",
    "allasse",
    "allasses",
    "allât",
    "allassions",
    "allassiez",
    "allassent",
    "allé",
    "allée",
    "allés",
    "allées",
    "allant",
    # DIRE
    "dire",
    "dis",
    "dit",
    "disons",
    "dites",
    "disent",
    "disais",
    "disait",
    "disions",
    "disiez",
    "disaient",
    "dirai",
    "diras",
    "dira",
    "dirons",
    "direz",
    "diront",
    "dirais",
    "dirait",
    "dirions",
    "diriez",
    "diraient",
    "dise",
    "dises",
    "disions",
    "disiez",
    "disent",
    "dite",
    "disant",
    # AUTRES VERBES MODAUX ET AUXILIAIRES TRÈS FRÉQUENTS
    "falloir",
    "faut",
    "faudra",
    "faudrait",
    "fallait",
    "fallu",
    "savoir",
    "sais",
    "sait",
    "savons",
    "savez",
    "savent",
    "savais",
    "savait",
    "savions",
    "saviez",
    "savaient",
    "su",
    "sachant",
    "vouloir",
    "veux",
    "veut",
    "voulons",
    "voulez",
    "veulent",
    "voulais",
    "voulait",
    "voulions",
    "vouliez",
    "voulaient",
    "voulu",
    "voulant",
    "pouvoir",
    "peux",
    "peut",
    "pouvons",
    "pouvez",
    "peuvent",
    "pouvais",
    "pouvait",
    "pouvions",
    "pouviez",
    "pouvaient",
    "pourrai",
    "pourras",
    "pourra",
    "pourrons",
    "pourrez",
    "pourront",
    "pourrais",
    "pourrait",
    "pourrions",
    "pourriez",
    "pourraient",
    "pu",
    "puisse",
    "puisses",
    "puissions",
    "puissiez",
    "puissent",
    "pouvant",
    # === ADVERBES TRÈS COMMUNS ===
    "très",
    "plus",
    "moins",
    "aussi",
    "encore",
    "déjà",
    "jamais",
    "toujours",
    "souvent",
    "parfois",
    "quelquefois",
    "maintenant",
    "hier",
    "demain",
    "aujourd hui",
    "aujourd'hui",
    "puis",
    "ensuite",
    "enfin",
    "alors",
    "donc",
    "ainsi",
    "aussi",
    "autant",
    "tant",
    "assez",
    "trop",
    "fort",
    "peu",
    "beaucoup",
    "bien",
    "mal",
    "mieux",
    "pire",
    "plutôt",
    "surtout",
    "notamment",
    "particulièrement",
    # === CONJONCTIONS ===
    "et",
    "ou",
    "mais",
    "donc",
    "or",
    "ni",
    "car",
    "si",
    "que",
    "quand",
    "comme",
    "lorsque",
    "puisque",
    "quoique",
    "bien que",
    "afin que",
    "pour que",
    "tandis que",
    "pendant que",
    "dès que",
    "aussitôt que",
    "depuis que",
    "parce que",
    "étant donné",
    # === MOTS DE LIAISON ===
    "par exemple",
    "exemple",
    "cependant",
    "néanmoins",
    "toutefois",
    "pourtant",
    "malgré",
    "en effet",
    "effet",
    "en fait",
    "fait",
    "en réalité",
    "réalité",
    "en revanche",
    "revanche",
    "au contraire",
    "contraire",
    "par contre",
    "contre",
    "par ailleurs",
    "ailleurs",
    "de plus",
    "en outre",
    "outre",
    "de même",
    "même",
    "également",
    "aussi",
    "pareillement",
    "similairement",
    "finalement",
    "enfin",
    "bref",
    "en somme",
    "somme",
    "en résumé",
    "résumé",
    "pour conclure",
    "conclure",
    # === AUTRES MOTS FRÉQUENTS MAIS PEU INFORMATIFS ===
    "rien",
    "quelque",
    "chaque",
    "plusieurs",
    "certains",
    "certaines",
    "quelques",
    "divers",
    "diverses",
    "différent",
    "différente",
    "différents",
    "différentes",
    "premier",
    "première",
    "premiers",
    "premières",
    "dernier",
    "dernière",
    "derniers",
    "dernières",
    "seul",
    "seule",
    "seuls",
    "seules",
    "unique",
    "grand",
    "grande",
    "grands",
    "grandes",
    "petit",
    "petite",
    "petits",
    "petites",
    "nouveau",
    "nouvelle",
    "nouveaux",
    "nouvelles",
    "ancien",
    "ancienne",
    "anciens",
    "anciennes",
    "jeune",
    "jeunes",
    "vieux",
    "vieille",
    "vieilles",
    # === NOMBRES ===
    "un",
    "une",
    "deux",
    "trois",
    "quatre",
    "cinq",
    "six",
    "sept",
    "huit",
    "neuf",
    "dix",
    "onze",
    "douze",
    "treize",
    "quatorze",
    "quinze",
    "seize",
    "vingt",
    "trente",
    "quarante",
    "cinquante",
    "soixante",
    "cent",
    "mille",
    "premier",
    "première",
    "deuxième",
    "second",
    "seconde",
    "troisième",
    # === MOTS TECHNIQUES/PARASITES FRANÇAIS ===
    "hum",
    "hmm",
    "euh",
    "beh",
    "pfff",
    "ouais",
    "mouais",
    "nan",
    "nope",
    "ok",
    "okay",
    "d accord",
    "d'accord",
    "accord",
    "voilà",
    "là",
    "ici",
    "par",
    "sans",
    "avec",
    "pour",
    "sur",
    "sous",
    "dans",
    "vers",
    "chez",
    "durant",
    "matin",
    "soir",
    "jour",
    "nuit",
    "semaine",
    "mois",
    "année",
    "an",
    "ans",
    "heure",
    "heures",
    "minute",
    "minutes",
    "seconde",
    "secondes",
    "temps",
    "moment",
    "moments",
    "instant",
    "instants",
    "période",
    "périodes",
}

# Mots vides anglais étendus
EXCLUDED_WORDS_EN = {
    # Interjections
    "oh",
    "ah",
    "um",
    "uh",
    "okay",
    "hey",
    "yeah",
    "yes",
    "no",
    "well",
    # Articles et prépositions
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "up",
    "about",
    "into",
    "through",
    "during",
    # Pronoms
    "i",
    "you",
    "he",
    "she",
    "it",
    "we",
    "they",
    "me",
    "him",
    "her",
    "us",
    "them",
    "my",
    "your",
    "his",
    "their",
    "our",
    # Verbes auxiliaires et communs
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "get",
    "got",
    "go",
    "goes",
    "went",
    "come",
    "came",
    "take",
    "took",
    "make",
    "made",
    "see",
    "saw",
    "know",
    "knew",
    # Adverbes communs
    "so",
    "just",
    "now",
    "then",
    "here",
    "there",
    "where",
    "when",
    "what",
    "how",
    "why",
    "who",
    "which",
    "very",
    "really",
    "quite",
    "more",
    "most",
    "much",
    "many",
    "some",
    "any",
    "all",
    "both",
    "each",
    "every",
    # Mots techniques/parasites
    "one",
    "two",
    "man",
    "__",
    "toss",
    "guys",
    "like",
    "thing",
    "things",
    "way",
    "time",
    "good",
    "bad",
    "right",
    "wrong",
}

EXCLUDED_WORDS_ALL = EXCLUDED_WORDS_FR | EXCLUDED_WORDS_EN

# Catégories de concepts pour l'analyse conceptuelle
CONCEPT_CATEGORIES = {
    "technologie": {
        "fr": [
            "technologie",
            "numérique",
            "ordinateur",
            "intelligence",
            "artificielle",
            "ia",
            "algorithme",
            "données",
            "internet",
            "réseau",
            "logiciel",
            "application",
            "programme",
            "code",
            "développement",
            "innovation",
            "smartphone",
            "téléphone",
            "mobile",
            "digital",
            "web",
            "site",
            "plateforme",
            "système",
        ],
        "en": [
            "technology",
            "digital",
            "computer",
            "artificial",
            "intelligence",
            "ai",
            "algorithm",
            "data",
            "internet",
            "network",
            "software",
            "application",
            "program",
            "code",
            "development",
            "innovation",
            "smartphone",
            "phone",
            "mobile",
            "web",
            "website",
            "platform",
            "system",
        ],
    },
    "économie": {
        "fr": [
            "économie",
            "marché",
            "entreprise",
            "business",
            "argent",
            "prix",
            "coût",
            "vente",
            "achat",
            "investissement",
            "profit",
            "bénéfice",
            "client",
            "consommateur",
            "produit",
            "service",
            "commercial",
            "marketing",
            "pub",
            "publicité",
        ],
        "en": [
            "economy",
            "market",
            "business",
            "company",
            "money",
            "price",
            "cost",
            "sale",
            "buy",
            "investment",
            "profit",
            "benefit",
            "customer",
            "consumer",
            "product",
            "service",
            "commercial",
            "marketing",
            "advertising",
        ],
    },
    "social": {
        "fr": [
            "social",
            "société",
            "communauté",
            "groupe",
            "famille",
            "ami",
            "relation",
            "humain",
            "personne",
            "gens",
            "éducation",
            "école",
            "université",
            "étudiant",
            "apprentissage",
            "culture",
            "art",
            "politique",
            "gouvernement",
        ],
        "en": [
            "social",
            "society",
            "community",
            "group",
            "family",
            "friend",
            "relationship",
            "human",
            "person",
            "people",
            "education",
            "school",
            "university",
            "student",
            "learning",
            "culture",
            "art",
            "politics",
            "government",
        ],
    },
    "santé": {
        "fr": [
            "santé",
            "médecine",
            "médical",
            "docteur",
            "médecin",
            "hôpital",
            "traitement",
            "maladie",
            "symptôme",
            "corps",
            "physique",
            "mental",
            "psychologie",
            "bien-être",
            "sport",
            "exercice",
            "nutrition",
            "alimentation",
        ],
        "en": [
            "health",
            "medicine",
            "medical",
            "doctor",
            "physician",
            "hospital",
            "treatment",
            "disease",
            "symptom",
            "body",
            "physical",
            "mental",
            "psychology",
            "wellness",
            "sport",
            "exercise",
            "nutrition",
            "food",
        ],
    },
    "environnement": {
        "fr": [
            "environnement",
            "nature",
            "climat",
            "écologie",
            "écologique",
            "vert",
            "durable",
            "pollution",
            "énergie",
            "renouvelable",
            "solaire",
            "éolien",
            "carbone",
            "émission",
            "réchauffement",
            "planète",
            "terre",
        ],
        "en": [
            "environment",
            "nature",
            "climate",
            "ecology",
            "ecological",
            "green",
            "sustainable",
            "pollution",
            "energy",
            "renewable",
            "solar",
            "wind",
            "carbon",
            "emission",
            "warming",
            "planet",
            "earth",
        ],
    },
}


def extract_words(text: str) -> list[str]:
    """Extrait et nettoie les mots d'un texte avec traitement amélioré"""
    # Normalisation du texte (minuscules)
    text = text.lower()

    # Nettoyage préalable : suppression de la ponctuation excessive
    text = re.sub(r"[.!?]{2,}", ".", text)  # Réduire les ponctuations multiples
    text = re.sub(r"\s+", " ", text)  # Réduire les espaces multiples

    # Extraction des mots incluant les contractions avec apostrophes
    # Pattern amélioré pour capturer les mots avec apostrophes, accents, traits d'union
    words = re.findall(r"\b[\w'éèêàâôîùûç-]+\b", text)

    # Filtrage intelligent des mots
    filtered_words = []

    for word in words:
        # Ignorer les mots trop courts (moins de 3 caractères)
        if len(word) < 3:
            continue

        # Ignorer les mots qui sont uniquement des chiffres
        if word.isdigit():
            continue

        # Ignorer les mots avec trop de caractères répétés (bruit)
        if re.match(r"^(..)\1{2,}", word):  # ex: "hahaha", "nonono"
            continue

        # Vérifier si le mot est dans la liste des mots vides
        if word in EXCLUDED_WORDS_ALL:
            continue

        # Traitement spécial pour les contractions
        # Si le mot contient une apostrophe, vérifier s'il faut le garder
        if "'" in word:
            # Garder les contractions qui ne sont pas dans les mots vides
            # mais exclure celles qui le sont (déjà géré par la vérification précédente)
            pass

        # Filtrer les mots avec des motifs répétitifs peu informatifs
        if re.match(r"^(.)\1{3,}", word):  # ex: "aaaaa", "mmmmm"
            continue

        filtered_words.append(word)

    return filtered_words


def analyze_style(words: list[str], max_words: int = 30) -> list[tuple[str, int]]:
    """Analyse de style : fréquence des mots

    Args:
        words (list): Liste des mots à analyser
        max_words (int): Nombre maximum de mots à retourner (1-200)

    Returns:
        list: Liste des tuples (mot, fréquence) triés par fréquence décroissante
    """
    # Validation du paramètre max_words
    max_words = max(1, min(200, int(max_words)))  # Entre 1 et 200

    counter = Counter(words)
    top_words = counter.most_common(max_words)
    return top_words


def analyze_concepts(words: list[str]) -> list[tuple[str, dict[str, Any]]]:
    """Analyse conceptuelle : détection de thèmes et concepts"""
    concept_scores: dict[str, dict[str, Any]] = {}
    word_set = set(words)

    # Comptage des concepts par catégorie
    for category, languages in CONCEPT_CATEGORIES.items():
        score = 0
        matched_words = []

        # Vérification pour chaque langue
        for lang, concept_words in languages.items():
            for concept_word in concept_words:
                if concept_word in word_set:
                    # Plus le mot apparaît souvent, plus le score est élevé
                    word_count = words.count(concept_word)
                    score += word_count
                    matched_words.extend([concept_word] * word_count)

        if score > 0:
            concept_scores[category] = {
                "score": score,
                "words": matched_words,
                "percentage": round((score / len(words)) * 100, 1),
            }

    # Tri par score décroissant
    sorted_concepts = sorted(concept_scores.items(), key=lambda x: x[1]["score"], reverse=True)

    return sorted_concepts


def get_text_statistics(words: list[str], original_text: str) -> dict[str, int | float]:
    """Calcule des statistiques détaillées sur le texte"""
    total_chars = len(original_text)
    total_words = len(words)
    unique_words = len(set(words))
    avg_word_length = sum(len(word) for word in words) / total_words if total_words > 0 else 0

    # Statistiques avancées
    sentences = len([s for s in original_text.split(".") if s.strip()])
    avg_sentence_length = total_words / sentences if sentences > 0 else 0

    # Analyse de la longueur des mots
    word_lengths = [len(word) for word in words]
    short_words = len([w for w in word_lengths if w <= 4])
    medium_words = len([w for w in word_lengths if 5 <= w <= 8])
    long_words = len([w for w in word_lengths if w >= 9])

    # Calcul du temps de lecture estimé (250 mots/minute)
    reading_time = total_words / 250

    return {
        "total_characters": total_chars,
        "total_words": total_words,
        "unique_words": unique_words,
        "sentences": sentences,
        "vocabulary_richness": round(unique_words / total_words * 100, 1) if total_words > 0 else 0,
        "average_word_length": round(avg_word_length, 1),
        "average_sentence_length": round(avg_sentence_length, 1),
        "short_words_percentage": round(short_words / total_words * 100, 1)
        if total_words > 0
        else 0,
        "medium_words_percentage": round(medium_words / total_words * 100, 1)
        if total_words > 0
        else 0,
        "long_words_percentage": round(long_words / total_words * 100, 1) if total_words > 0 else 0,
        "reading_time_minutes": round(reading_time, 1),
        "complexity_score": round((avg_word_length * 10) + (unique_words / total_words * 50), 1)
        if total_words > 0
        else 0,
    }


def generate_summary(text: str, num_sentences: int = 3) -> str:
    """Génère un résumé automatique basique"""
    if not text or not text.strip():
        return ""

    # Division en phrases
    sentences = [s.strip() for s in text.split(".") if s.strip() and len(s.strip()) > 10]

    if len(sentences) <= num_sentences:
        return text

    # Extraction des mots importants
    words = extract_words(text)
    word_freq = Counter(words)

    # Score de chaque phrase basé sur la fréquence des mots
    sentence_scores = []

    for i, sentence in enumerate(sentences):
        sentence_words = extract_words(sentence.lower())
        score = sum(word_freq.get(word, 0) for word in sentence_words)

        # Bonus pour les phrases ni trop courtes ni trop longues
        length_bonus = 1.0
        if 10 <= len(sentence_words) <= 25:
            length_bonus = 1.5

        # Bonus pour les premières et dernières phrases
        position_bonus = 1.0
        if i < 2 or i >= len(sentences) - 2:
            position_bonus = 1.2

        final_score = score * length_bonus * position_bonus
        sentence_scores.append((final_score, i, sentence))

    # Sélection des meilleures phrases
    best_sentences = sorted(sentence_scores, key=lambda x: x[0], reverse=True)[:num_sentences]
    best_sentences.sort(key=lambda x: x[1])  # Tri par ordre d'apparition

    summary = ". ".join([sentence[2] for sentence in best_sentences]) + "."
    return summary


def get_word_cloud_data(words: list[str], max_words: int = 50) -> list[dict[str, Any]]:
    """Prépare les données pour un nuage de mots"""
    counter = Counter(words)
    top_words = counter.most_common(max_words)

    # Calcul des tailles relatives (entre 1 et 5)
    if not top_words:
        return []

    max_count = top_words[0][1]
    min_count = top_words[-1][1] if len(top_words) > 1 else max_count

    word_cloud_data = []
    for word, count in top_words:
        # Calcul de la taille (entre 1 et 5)
        if max_count == min_count:
            size = 3.0
        else:
            size = 1 + 4 * (count - min_count) / (max_count - min_count)

        # Couleurs basées sur la fréquence
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8"]
        color = colors[hash(word) % len(colors)]

        word_cloud_data.append(
            {"word": word, "count": count, "size": round(size, 1), "color": color}
        )

    return word_cloud_data


def analyze_text(
    text: str, mode: str = "style", max_words: int = 30
) -> tuple[list[tuple[str, int]] | list[tuple[str, dict[str, Any]]], int]:
    """Fonction principale d'analyse de texte

    Args:
        text (str): Texte à analyser
        mode (str): Mode d'analyse ('style' ou 'concepts')
        max_words (int): Nombre maximum de mots pour l'analyse de style (1-200)

    Returns:
        tuple: (résultats, nombre_de_mots_total)
    """
    try:
        if not text or not text.strip():
            return [], 0

        logger.info(
            f"Début d'analyse en mode '{mode}' (max_words={max_words}) pour un texte de {len(text)} caractères"
        )

        # Extraction et nettoyage des mots
        words = extract_words(text)

        if len(words) == 0:
            logger.warning("Aucun mot significatif trouvé dans le texte")
            return [], 0

        # Analyse selon le mode
        result: list[tuple[str, int]] | list[tuple[str, dict[str, Any]]]
        if mode == "style":
            result = analyze_style(words, max_words)

        elif mode == "concepts":
            result = analyze_concepts(words)

        else:
            logger.warning(f"Mode d'analyse inconnu: {mode}, utilisation du mode 'style'")
            result = analyze_style(words, max_words)

        logger.info(f"Analyse terminée: {len(result)} éléments trouvés")
        return result, len(words)

    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du texte: {e}")
        raise
