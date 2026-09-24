# Lancement et administration

Installer avec `uv sync --locked`. Python 3.11+ 64 bits ; `.python-version`
sélectionne Python 3.13 pour le développement.

| Action | Commande Windows / Linux |
| --- | --- |
| Lancer dans le terminal | `uv run yt-transcript serve` |
| Lancer en arrière-plan | `uv run yt-transcript start` |
| Arrêter | `uv run yt-transcript stop` |
| Redémarrer | `uv run yt-transcript restart` |
| Statut | `uv run yt-transcript status` |
| Derniers logs | `uv run yt-transcript logs --lines 50` |
| Suivre les logs | `uv run yt-transcript logs --follow` |
| Informations et chemins | `uv run yt-transcript info` |
| Développement | `uv run yt-transcript dev` |
| Contrôles complets | `uv run python scripts/check.py` |

Interface : http://127.0.0.1:5001 ; API : http://127.0.0.1:5001/api/docs/ .
`serve` utilise Waitress sans debug. Ctrl+C arrête le serveur dans le terminal ;
`stop` concerne celui lancé par `start`.

Raccourcis : `./launch.ps1 start` (PowerShell), `./launch.sh start` (Bash).
`install` synchronise l'environnement, `help` affiche l'aide. Si PowerShell bloque
le script, utiliser directement `uv run` sans changer la politique d'exécution.

## Configuration et données existantes

```powershell
uv run yt-transcript --data-dir 'I:\mes donnees\transcriptions' start --port 5002
uv run yt-transcript --data-dir 'I:\mes donnees\transcriptions' stop
```

Utiliser le même `--data-dir` pour administrer une instance. Sinon,
`YT_TRANSCRIPT_DATA_DIR` puis le dossier utilisateur sont utilisés : généralement
`%LOCALAPPDATA%\yt-transcript` sous Windows, `~/.local/share/yt-transcript` sous Linux.
`info` donne le chemin exact.

Variables : `YT_TRANSCRIPT_HOST` (127.0.0.1), `YT_TRANSCRIPT_PORT` (5001),
`YT_TRANSCRIPT_DATA_DIR`, `DATABASE_URL` (URL SQLAlchemy), `SECRET_KEY`.
Une clé de session aléatoire persistante est créée dans `secret.key` si nécessaire.
`server.json` identifie le processus et `server.log` contient les logs.
Un PID réutilisé ou une commande différente ne sont jamais arrêtés.

Pour reprendre une ancienne base `yt_analyzer.db` à la racine du dépôt : arrêter
l'ancien serveur, puis `uv run yt-transcript --data-dir . start`.
On peut aussi copier la base, serveur arrêté, vers le nouveau dossier de données.
Aucune migration ni suppression automatique des données existantes.

## DevMenu

`.devmenu.json` reprend la structure `project`, `i18n`, `menus` du menu TerraCycle.
Ouvrir ce dépôt avec ton outil DevMenu existant. Les actions utilisent `uv` et les
mêmes contrôles que la CI, sans activation manuelle du venv. Le moteur DevMenu est
externe au projet.

## Installation du wheel sans uv

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install dist\yt_transcript_analyzer-1.0.0-py3-none-any.whl
.venv\Scripts\yt-transcript serve
```

Sous Linux : `python3 -m venv .venv`, `.venv/bin/python -m pip install ...`,
puis `.venv/bin/yt-transcript serve`. Les dépendances sont téléchargées à
l'installation. Le wheel embarque les templates et ressources statiques.
