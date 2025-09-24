# 🚀 Script de Lancement - YouTube Transcript Analyzer

## 📋 Vue d'ensemble

Ce script bash facilite la gestion de votre application YouTube Transcript Analyzer avec toutes les fonctionnalités nécessaires pour un déploiement robuste.

## 🔧 Installation

Le script est déjà configuré et prêt à l'usage ! Il se trouve dans :
- Script principal : `./launch.sh`
- Raccourci global : `~/ytanalyzer`

## 📖 Utilisation

### Commandes disponibles

```bash
# Démarrer l'application
./launch.sh start
# ou depuis n'importe où :
~/ytanalyzer start

# Arrêter l'application
./launch.sh stop

# Redémarrer l'application
./launch.sh restart

# Voir le statut de l'application
./launch.sh status

# Voir les logs en temps réel
./launch.sh logs

# Nettoyer les processus zombies
./launch.sh clean

# Installer/mettre à jour les dépendances
./launch.sh install

# Afficher l'aide
./launch.sh help
```

### Exemples d'utilisation typiques

#### 🎯 Premier lancement
```bash
# 1. Installer les dépendances si nécessaire
./launch.sh install

# 2. Démarrer l'application
./launch.sh start
```

#### 🔄 Usage quotidien
```bash
# Vérifier si l'app est en cours
./launch.sh status

# Redémarrer après des modifications
./launch.sh restart

# Voir les logs si il y a des problèmes
./launch.sh logs
```

#### 🧹 Résolution de problèmes
```bash
# Nettoyer les processus zombies
./launch.sh clean

# Forcer un redémarrage propre
./launch.sh stop
./launch.sh clean
./launch.sh start
```

## ✨ Fonctionnalités du script

### 🛡️ Sécurité et robustesse
- ✅ Vérification des processus existants
- ✅ Gestion des processus zombies
- ✅ Arrêt gracieux avec fallback forcé
- ✅ Vérification des ports occupés
- ✅ Gestion des fichiers PID

### 📊 Monitoring
- ✅ Messages colorés et horodatés
- ✅ Statut détaillé avec utilisation mémoire
- ✅ Logs en temps réel avec `tail -f`
- ✅ Vérification des dépendances Python

### 🔧 Maintenance
- ✅ Installation automatique des dépendances
- ✅ Nettoyage des fichiers temporaires
- ✅ Détection et résolution des conflits de port

## 📁 Fichiers créés/gérés

Le script crée et gère automatiquement ces fichiers :

- `app.pid` : Stocke le PID de l'application en cours
- `app.log` : Logs de l'application (créé par nohup)

## 🌐 Accès à l'application

Une fois démarrée, l'application est accessible sur :

- **Interface web** : http://localhost:5001
- **API REST** : http://localhost:5001/api/docs/

## ⚙️ Configuration

Vous pouvez modifier ces variables dans le script si nécessaire :

```bash
APP_NAME="YouTube Transcript Analyzer"
APP_DIR="/home/gduval/dev/yt_transcript_analyzer"
APP_FILE="app.py"
LOG_FILE="app.log"
PID_FILE="app.pid"
PORT=5001
```

## 🚨 Résolution des problèmes courants

### Port déjà utilisé
Le script détecte automatiquement si le port 5001 est utilisé et propose de l'arrêter.

### Processus zombie
```bash
./launch.sh clean
```

### Dépendances manquantes
```bash
./launch.sh install
```

### Application qui ne démarre pas
```bash
# Voir les logs pour diagnostiquer
./launch.sh logs

# Ou vérifier le statut détaillé
./launch.sh status
```

### Redémarrage complet
```bash
./launch.sh stop
./launch.sh clean
./launch.sh start
```

## 🎨 Messages colorés

Le script utilise des couleurs pour faciliter la lecture :
- 🔵 **Bleu** : Informations
- 🟢 **Vert** : Succès
- 🟡 **Jaune** : Avertissements
- 🔴 **Rouge** : Erreurs

## 📞 Support

Si vous rencontrez des problèmes :
1. Vérifiez les logs avec `./launch.sh logs`
2. Vérifiez le statut avec `./launch.sh status`
3. Essayez un nettoyage avec `./launch.sh clean`
4. Redémarrez avec `./launch.sh restart`

---

🎉 **Bon usage de votre YouTube Transcript Analyzer !**