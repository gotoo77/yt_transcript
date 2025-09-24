#!/bin/bash

# Script de test pour démontrer la coloration des logs

# Ajouter des logs de test à app.log
echo "2025-09-19 17:35:00,000 - test - DEBUG - Ceci est un message de débogage" >> app.log
echo "2025-09-19 17:35:01,000 - test - INFO - Ceci est un message d'information" >> app.log  
echo "2025-09-19 17:35:02,000 - test - WARNING - Ceci est un avertissement" >> app.log
echo "2025-09-19 17:35:03,000 - test - ERROR - Ceci est une erreur" >> app.log
echo "2025-09-19 17:35:04,000 - database - INFO - Base de données initialisée avec succès" >> app.log
echo "2025-09-19 17:35:05,000 - transcription - INFO - Transcription réussie en français" >> app.log
echo "2025-09-19 17:35:06,000 - analysis - INFO - Analyse terminée avec succès" >> app.log
echo "Traceback (most recent call last):" >> app.log
echo "    File app.py, line 42, in function" >> app.log
echo "ValueError: Something went wrong" >> app.log

echo "✨ Logs de test ajoutés ! Utilisez './launch.sh logs' pour les voir en couleur !"