#!/bin/bash

# =============================================================================
# Script de lancement - YouTube Transcript Analyzer
# =============================================================================

# Configuration
APP_NAME="YouTube Transcript Analyzer"
APP_DIR="/home/gduval/dev/yt_transcript"
APP_FILE="app.py"
LOG_FILE="app.log"
PID_FILE="app.pid"
PORT=5001

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
LIGHT_BLUE='\033[1;34m'
ORANGE='\033[0;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
LIGHT_GRAY='\033[0;37m'
DARK_GRAY='\033[1;30m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages colorés
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date '+%H:%M:%S')] ${message}${NC}"
}

print_info() { print_message "$BLUE" "ℹ️  $1"; }
print_success() { print_message "$GREEN" "✅ $1"; }
print_warning() { print_message "$YELLOW" "⚠️  $1"; }
print_error() { print_message "$RED" "❌ $1"; }

# Fonction pour afficher l'aide
show_help() {
    echo -e "${BLUE}=== $APP_NAME - Script de lancement ===${NC}"
    echo
    echo "Usage: $0 [OPTION]"
    echo
    echo "Options:"
    echo "  start     Démarre l'application"
    echo "  stop      Arrête l'application"
    echo "  restart   Redémarre l'application"
    echo "  status    Affiche le statut de l'application"
    echo "  logs [N]  Affiche les N dernières lignes de log (défaut: 10) et suit en temps réel"
    echo "  tail [N]  Affiche seulement les N dernières lignes de log sans suivi (défaut: 20)"
    echo "  clean     Nettoie les processus zombies et les fichiers temporaires"
    echo "  install   Installe/met à jour les dépendances"
    echo "  help      Affiche cette aide"
    echo
}

# Fonction pour changer vers le répertoire de l'app
cd_to_app() {
    if [ ! -d "$APP_DIR" ]; then
        print_error "Répertoire de l'application non trouvé: $APP_DIR"
        exit 1
    fi
    cd "$APP_DIR" || exit 1
}

# Fonction pour vérifier si le port est libre
check_port() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        local pid=$(lsof -Pi :$PORT -sTCP:LISTEN -t)
        print_warning "Le port $PORT est déjà utilisé par le processus PID: $pid"
        
        # Demander si on veut arrêter le processus
        read -p "Voulez-vous arrêter ce processus ? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Arrêt du processus $pid..."
            kill -TERM "$pid" 2>/dev/null
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                print_warning "Processus résistant, force l'arrêt..."
                kill -KILL "$pid" 2>/dev/null
            fi
            print_success "Processus arrêté"
        else
            print_error "Impossible de démarrer l'application"
            return 1
        fi
    fi
    return 0
}

# Fonction pour nettoyer les processus zombies
clean_processes() {
    print_info "Nettoyage des processus zombies..."
    
    # Trouver et tuer les processus Python liés à l'app
    local zombie_pids=$(ps aux | grep "[p]ython.*app.py" | awk '{print $2}')
    
    if [ -n "$zombie_pids" ]; then
        print_info "Processus trouvés: $zombie_pids"
        for pid in $zombie_pids; do
            print_info "Arrêt du processus $pid..."
            kill -TERM "$pid" 2>/dev/null
            sleep 1
            if kill -0 "$pid" 2>/dev/null; then
                kill -KILL "$pid" 2>/dev/null
            fi
        done
        print_success "Processus nettoyés"
    else
        print_info "Aucun processus zombie trouvé"
    fi
    
    # Nettoyer le fichier PID s'il existe
    if [ -f "$PID_FILE" ]; then
        rm -f "$PID_FILE"
        print_info "Fichier PID supprimé"
    fi
}

# Fonction pour vérifier les dépendances Python
check_dependencies() {
    print_info "Vérification des dépendances Python..."
    
    if [ ! -f "requirements.txt" ]; then
        print_warning "Fichier requirements.txt non trouvé"
        return 1
    fi
    
    # Vérifier si pip est disponible
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 n'est pas installé"
        return 1
    fi
    
    # Vérifier les dépendances critiques avec le bon nom d'import
    local critical_imports=("flask" "youtube_transcript_api" "flask_restx" "flask_cors" "nltk" "textblob")
    local missing_deps=()
    
    for import_name in "${critical_imports[@]}"; do
        if ! python3 -c "import $import_name" 2>/dev/null; then
            missing_deps+=("$import_name")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        print_warning "Dépendances manquantes: ${missing_deps[*]}"
        return 1
    fi
    
    print_success "Toutes les dépendances sont installées"
    return 0
}

# Fonction pour installer les dépendances
install_dependencies() {
    print_info "Installation/mise à jour des dépendances..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "Fichier requirements.txt non trouvé"
        return 1
    fi
    
    # Mettre à jour pip
    python3 -m pip install --upgrade pip
    
    # Installer les dépendances
    if python3 -m pip install -r requirements.txt; then
        print_success "Dépendances installées avec succès"
        return 0
    else
        print_error "Échec de l'installation des dépendances"
        return 1
    fi
}

# Fonction pour démarrer l'application
start_app() {
    cd_to_app
    
    print_info "Démarrage de $APP_NAME..."
    
    # Vérifier si l'application est déjà en cours d'exécution
    if [ -f "$PID_FILE" ]; then
        local existing_pid=$(cat "$PID_FILE")
        if kill -0 "$existing_pid" 2>/dev/null; then
            print_warning "L'application est déjà en cours d'exécution (PID: $existing_pid)"
            return 1
        else
            print_info "Fichier PID obsolète supprimé"
            rm -f "$PID_FILE"
        fi
    fi
    
    # Vérifier le port
    if ! check_port; then
        return 1
    fi
    
    # Vérifier les dépendances
    if ! check_dependencies; then
        print_warning "Des dépendances manquent. Lancez '$0 install' pour les installer."
    fi
    
    # Vérifier que le fichier app.py existe
    if [ ! -f "$APP_FILE" ]; then
        print_error "Fichier $APP_FILE non trouvé"
        return 1
    fi
    
    # Démarrer l'application en arrière-plan
    print_info "Lancement de l'application sur le port $PORT..."
    nohup python3 "$APP_FILE" > "$LOG_FILE" 2>&1 &
    local app_pid=$!
    
    # Sauvegarder le PID
    echo "$app_pid" > "$PID_FILE"
    
    # Attendre un peu et vérifier que l'app démarre bien
    sleep 3
    
    if kill -0 "$app_pid" 2>/dev/null; then
        print_success "Application démarrée avec succès (PID: $app_pid)"
        print_info "Interface web disponible sur: http://localhost:$PORT"
        print_info "API REST disponible sur: http://localhost:$PORT/api/docs/"
        print_info "Logs disponibles dans: $LOG_FILE"
        print_info "Pour arrêter: $0 stop"
        print_info "Pour voir les logs: $0 logs"
        return 0
    else
        print_error "Échec du démarrage de l'application"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Fonction pour arrêter l'application
stop_app() {
    cd_to_app
    
    print_info "Arrêt de $APP_NAME..."
    
    if [ ! -f "$PID_FILE" ]; then
        print_warning "Fichier PID non trouvé. L'application n'est peut-être pas en cours d'exécution."
        clean_processes
        return 0
    fi
    
    local app_pid=$(cat "$PID_FILE")
    
    if ! kill -0 "$app_pid" 2>/dev/null; then
        print_warning "L'application ne semble pas être en cours d'exécution (PID: $app_pid)"
        rm -f "$PID_FILE"
        return 0
    fi
    
    # Arrêt gracieux
    print_info "Envoi du signal TERM au processus $app_pid..."
    kill -TERM "$app_pid"
    
    # Attendre l'arrêt
    local count=0
    while kill -0 "$app_pid" 2>/dev/null && [ $count -lt 10 ]; do
        sleep 1
        ((count++))
        echo -n "."
    done
    echo
    
    # Forcer l'arrêt si nécessaire
    if kill -0 "$app_pid" 2>/dev/null; then
        print_warning "Arrêt forcé du processus..."
        kill -KILL "$app_pid"
        sleep 1
    fi
    
    # Nettoyer
    rm -f "$PID_FILE"
    print_success "Application arrêtée"
}

# Fonction pour redémarrer l'application
restart_app() {
    print_info "Redémarrage de $APP_NAME..."
    stop_app
    sleep 2
    start_app
}

# Fonction pour afficher le statut
show_status() {
    cd_to_app
    
    print_info "Statut de $APP_NAME:"
    
    if [ -f "$PID_FILE" ]; then
        local app_pid=$(cat "$PID_FILE")
        if kill -0 "$app_pid" 2>/dev/null; then
            print_success "Application en cours d'exécution (PID: $app_pid)"
            
            # Afficher l'utilisation du port
            if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
                print_info "Port $PORT: UTILISÉ"
                print_info "Interface web: http://localhost:$PORT"
            else
                print_warning "Port $PORT: LIBRE (problème possible)"
            fi
            
            # Afficher l'utilisation mémoire
            local memory=$(ps -o pid,vsz,rss,comm -p "$app_pid" | tail -1)
            print_info "Mémoire: $memory"
            
        else
            print_error "Application non en cours d'exécution (PID obsolète: $app_pid)"
            rm -f "$PID_FILE"
        fi
    else
        print_warning "Application non en cours d'exécution (aucun fichier PID)"
    fi
    
    # Vérifier les logs récents
    if [ -f "$LOG_FILE" ]; then
        print_info "Dernières lignes du log:"
        tail -5 "$LOG_FILE" | while IFS= read -r line; do
            echo "  $line"
        done
    fi
}

# Fonction pour afficher les logs
show_logs() {
    cd_to_app
    
    local lines_count=${2:-10}  # Par défaut 10 lignes, ou paramètre fourni
    local follow_mode=${3:-true} # Par défaut suivre en temps réel
    
    if [ ! -f "$LOG_FILE" ]; then
        print_error "Fichier de log $LOG_FILE non trouvé"
        return 1
    fi
    
    if [ "$follow_mode" = "true" ]; then
        print_info "Logs de $APP_NAME (Ctrl+C pour quitter):"
    else
        print_info "Logs de $APP_NAME:"
    fi
    echo "----------------------------------------"
    echo -e "${LIGHT_BLUE}🔵 DEBUG   ${GREEN}🟢 INFO   ${ORANGE}🟡 WARNING   ${RED}🔴 ERROR   ${RED}💥 CRITICAL${NC}"
    echo "----------------------------------------"
    
    # Fonction pour colorer une ligne de log
    colorize_log() {
        local line="$1"
        
        # Coloration par niveau de log (priorité décroissante)
        if [[ "$line" =~ " - ERROR - " || "$line" =~ "ERROR" ]]; then
            echo -e "${RED}🔴 $line${NC}"
        elif [[ "$line" =~ "CRITICAL" || "$line" =~ "FATAL" ]]; then
            echo -e "${RED}💥 $line${NC}"
        elif [[ "$line" =~ " - WARNING - " || "$line" =~ "WARNING" ]]; then
            echo -e "${ORANGE}🟡 $line${NC}"
        elif [[ "$line" =~ " - INFO - " || "$line" =~ "INFO" ]]; then
            echo -e "${GREEN}🟢 $line${NC}"
        elif [[ "$line" =~ " - DEBUG - " || "$line" =~ "DEBUG" ]]; then
            echo -e "${LIGHT_BLUE}🔵 $line${NC}"
        
        # Cas spéciaux d'erreur
        elif [[ "$line" =~ "Traceback" || "$line" =~ "Exception" ]]; then
            echo -e "${RED}💥 $line${NC}"
        elif [[ "$line" =~ "Error:" || "$line" =~ "Failed" || "$line" =~ "Échec" ]]; then
            echo -e "${RED}❌ $line${NC}"
            
        # Succès et confirmations
        elif [[ "$line" =~ "✅" || "$line" =~ "SUCCESS" || "$line" =~ "réussie" || "$line" =~ "successfully" ]]; then
            echo -e "${GREEN}✅ $line${NC}"
        elif [[ "$line" =~ "Starting" || "$line" =~ "Démarrage" || "$line" =~ "Running on" ]]; then
            echo -e "${CYAN}🚀 $line${NC}"
            
        # Werkzeug/Flask spécifique
        elif [[ "$line" =~ "werkzeug" && "$line" =~ "INFO" ]]; then
            echo -e "${PURPLE}🌐 $line${NC}"
        elif [[ "$line" =~ "werkzeug" && "$line" =~ "WARNING" ]]; then
            echo -e "${YELLOW}⚠️ $line${NC}"
            
        # Base de données
        elif [[ "$line" =~ "database" || "$line" =~ "Base de données" ]]; then
            echo -e "${CYAN}🗄 $line${NC}"
            
        # Transcription
        elif [[ "$line" =~ "Transcription" || "$line" =~ "transcript" ]]; then
            echo -e "${BLUE}🎤 $line${NC}"
            
        # Analyse
        elif [[ "$line" =~ "Analyse" || "$line" =~ "analysis" ]]; then
            echo -e "${PURPLE}📈 $line${NC}"
            
        # Ligne normale (gris clair)
        else
            echo -e "${LIGHT_GRAY}$line${NC}"
        fi
    }
    
    # Afficher les dernières lignes avec coloration
    if [ -s "$LOG_FILE" ]; then
        print_info "Dernières $lines_count lignes:"
        tail -$lines_count "$LOG_FILE" | while IFS= read -r line; do
            colorize_log "$line"
        done
        echo "----------------------------------------"
    fi
    
    # Suivre le fichier en temps réel avec coloration seulement si demandé
    if [ "$follow_mode" = "true" ]; then
        print_info "Suivi en temps réel (nouvelles entrées uniquement):"
        # Utiliser tail -f --lines=0 pour ne pas re-afficher les lignes déjà vues
        tail -f --lines=0 "$LOG_FILE" | while IFS= read -r line; do
            colorize_log "$line"
        done
    fi
}

# Script principal
main() {
    case "${1:-help}" in
        "start")
            start_app
            ;;
        "stop")
            stop_app
            ;;
        "restart")
            restart_app
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$1" "$2" true
            ;;
        "tail")
            show_logs "$1" "${2:-20}" false
            ;;
        "clean")
            clean_processes
            ;;
        "install")
            cd_to_app
            install_dependencies
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Gestion des signaux
trap 'echo -e "\n${YELLOW}Script interrompu${NC}"; exit 130' INT

# Exécution
main "$@"
