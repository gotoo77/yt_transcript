# 🎬 YouTube Transcript Analyzer

Un analyseur intelligent de transcriptions YouTube avec fonctionnalités avancées d'analyse textuelle, de sentiment et de visualisation de données.

## ✨ Nouvelles fonctionnalités (Version actuelle)

### 🎯 **Contrôleur de mots personnalisable**
- **Slider interactif** : Choisissez de 1 à 200 mots les plus fréquents
- **Synchronisation temps réel** : Slider et input synchronisés
- **Validation intelligente** : Limites automatiques et gestion d'erreurs
- **Interface adaptive** : Visible uniquement en mode "Style"

### 🧼 **Filtrage intelligent amélioré**
- **+500 mots vides exclus** : Liste exhaustive de mots non-informatifs
- **Gestion des contractions** : "c'est", "j'ai", "n'est", etc. automatiquement filtrés
- **Toutes les conjugaisons** : Verbes être, avoir, faire, aller, dire complètement gérés
- **75.6% de filtrage** : Taux de suppression des mots parasites
- **Mots techniques** : Exclusion des interjections et expressions orales

### 🔄 **API YouTube Transcript 1.2.2**
- **Système de fallback robuste** : Essai intelligent de toutes les langues disponibles
- **Priorité linguistique** : Français et anglais en priorité, puis autres langues
- **Gestion d'échec** : Récupération automatique sur échec de langue spécifique

## ✨ Fonctionnalités

### 🔧 Fonctionnalités de base
- **Extraction de transcriptions** : Support automatique français/anglais
- **Interface web moderne** : Design responsive avec Bootstrap et FontAwesome
- **Téléchargement** : Export des transcriptions en format texte
- **Mise en forme** : Amélioration automatique du formatage du texte

### 📊 Analyses avancées
- **Mode Style** : Analyse de fréquence des mots avec filtrage intelligent
- **Mode Concepts** : Détection automatique de thèmes (technologie, économie, social, santé, environnement)
- **Graphiques interactifs** : Visualisations Chart.js avec graphiques en barres et camembert
- **Statistiques détaillées** : Métriques avancées (complexité, temps de lecture, richesse vocabulaire)
- **Résumé automatique** : Génération intelligente de résumés basée sur la fréquence
- **Nuage de mots** : Représentation visuelle colorée des termes les plus importants
- **Recherche temps réel** : Fonction de recherche dans les transcriptions

### 🛡️ Robustesse
- **Gestion d'erreurs complète** : Messages informatifs et logging détaillé
- **Sessions Flask** : Pas de variables globales, architecture thread-safe
- **Validation d'entrée** : Vérification des URLs et IDs YouTube
- **Fallback multilingue** : Essai automatique de plusieurs langues

## 🚀 Installation

### Prérequis
```bash
Python 3.7+
```

### Installation des dépendances
```bash
pip install -r requirements.txt
```

### Lancement de l'application
```bash
python3 app.py
```

L'application sera accessible à l'adresse : `http://localhost:5000`

## 📝 Utilisation

1. **Transcription**
   - Collez une URL YouTube complète ou juste l'ID de la vidéo
   - Cliquez sur "Transcrire" 
   - Le système essaiera automatiquement le français puis l'anglais

2. **Analyse**
   - Choisissez le mode d'analyse :
     - **Style** : Analyse des mots les plus fréquents
     - **Concepts** : Détection de thèmes conceptuels
   - Cliquez sur "Analyser"
   - Les résultats s'affichent avec visualisations

3. **Export**
   - Utilisez "Mise en forme" pour améliorer la structure du texte
   - "Télécharger" pour sauvegarder en fichier .txt

## 🏗️ Architecture

```
yt_transcript_analyzer/
├── app.py                 # Application Flask principale
├── transcript_analyzer.py # Logique d'analyse NLP
├── requirements.txt       # Dépendances Python
├── README.md             # Documentation
├── templates/
│   └── index.html        # Interface utilisateur
└── static/
    └── app.js           # Logique JavaScript
```

## 🔧 Améliorations récentes

### ✨ Phase 2 - Fonctionnalités avancées (NOUVEAU!)

#### 📊 Visualisations interactives
- **Graphiques Chart.js** : Histogrammes de fréquence et graphiques en secteurs
- **Graphique concepts** : Visualisation de la répartition thématique
- **Nuage de mots coloré** : Représentation visuelle avec tailles dynamiques
- **Interface responsive** : Optimisation mobile et tablette

#### 🧠 Intelligence textuelle
- **Résumé automatique** : Algorithme de sélection des phrases importantes
- **Statistiques détaillées** : Métriques de complexité, temps de lecture, richesse
- **Recherche temps réel** : Fonction de recherche intégrée dans les transcriptions
- **Analyse de longueur** : Classification des mots par taille

#### 🎨 Améliorations UI/UX
- **Animations fluides** : Transitions CSS et effets visuels
- **Design cards** : Présentation moderne des statistiques
- **Sections dédiées** : Organisation claire des résultats
- **Optimisation mobile** : Interface complètement responsive

### ✅ Phase 1 - Corrections techniques
- **Sessions Flask** : Remplacement des variables globales pour une architecture thread-safe
- **Gestion d'erreurs** : Logging complet et messages informatifs
- **Validation robuste** : Vérification des entrées utilisateur
- **Mode Concepts** : Détection automatique de 5 catégories thématiques
- **Interface moderne** : Design avec icônes FontAwesome et Bootstrap

## 🐛 Résolution de problèmes

### Erreur "Pas de transcription disponible"
- Vérifiez que la vidéo a des sous-titres activés
- Certaines vidéos n'ont pas de transcriptions automatiques

### Erreur "ID vidéo invalide"
- Vérifiez le format de l'URL ou de l'ID (11 caractères)
- Exemples valides : `dQw4w9WgXcQ` ou `https://www.youtube.com/watch?v=dQw4w9WgXcQ`

## 📈 Prochaines étapes (Phases 3-4)

- **Phase 3** : Analyse de sentiment avec spaCy, base de données SQLite, historique des analyses
- **Phase 4** : Comparaisons entre vidéos, API REST, export PDF/Word, application mobile

### 🚀 Nouvelles idées
- **Analyse temporelle** : Détection de l'évolution des thèmes dans le temps
- **Clustering automatique** : Regroupement intelligent des sujets
- **Export avancé** : Génération de rapports PDF avec graphiques
- **Mode collaboration** : Partage et annotation des analyses

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir des issues ou proposer des pull requests.

## 📄 Licence

Ce projet est sous licence MIT.