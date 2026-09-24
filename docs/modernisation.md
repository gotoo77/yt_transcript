# Modernisation Windows / Linux

Périmètre validé : conserver l'interface et les fonctionnalités Flask, distribuer
un package Python avec ses ressources, proposer un lancement natif sous Windows 11
et Linux, des contrôles Ruff/mypy et de vrais tests hors réseau, et un DevMenu.

## Architecture

- `src/yt_transcript/` : modules métier existants, templates et JavaScript embarqués.
- `create_app(config)` : application configurable, SQLite par application et sans
  création de base à l'import. Données dans le répertoire utilisateur configurable.
- CLI `yt-transcript` : serveur Waitress local, développement explicite et
  administration du processus avec vérification de son identité.
- `pyproject.toml` et `uv.lock` : métadonnées, dépendances, outils et versions résolues.
- `tests/` : unités métier, erreurs et repli YouTube simulés, intégration HTTP,
  persistance SQLite temporaire, exports et administration.
- CI Windows/Linux : lint, format, types, tests, construction et test du wheel.

## Plan d'exécution

1. Capturer les comportements métier et régressions dans des tests ; exécuter le
   socle avant migration. Corriger l'exclusion Git des tests.
2. Déplacer les modules et ressources dans le package, déclarer dépendances et
   configuration des outils. Tester `uv sync` et les imports.
3. Introduire la fabrique Flask, configuration portable et stockage isolé ; tester
   deux applications simultanées, JSON invalide, URL trompeuse, absence de vidéo,
   transcription et analyse sauvegardée. Garder les URL publiques existantes.
4. Ajouter la CLI et l'administration : démarrage/arrêt/statut/logs, validation du
   port et identité PID + date de création + commande. Tester processus périmé et
   port occupé sans arrêter de processus étranger.
5. Annoter les fonctions, corriger les erreurs Ruff/mypy et les régressions exports.
   Tester fréquences exactes, résumés, bornes, données vides, PDF et Excel réels.
6. Ajouter DevMenu, documentation et CI ; construire wheel/sdist puis installer le
   wheel hors dépôt dans un environnement propre et vérifier HTTP et ressources.

## Critères d'acceptation

`uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`,
`uv run pytest`, `uv build` passent. Le wheel démarre sans le répertoire source.
Les TU n'appellent jamais YouTube et les tests n'écrivent jamais dans la base réelle.
Les vérifications Linux sont définies en CI ; seules les exécutions réellement
réalisées localement seront annoncées comme vérifiées.

## Décisions

- Exécution dans le dépôt courant, sans commit/push automatique, pour laisser les
  changements directement révisables par l'utilisateur.
- Python >=3.11 ; environnement de développement 3.13 disponible sur cette machine.
- Pas de téléchargement de corpus au démarrage ; segmentation locale des phrases.
- Les payloads JSON hétérogènes des services historiques utilisent des dictionnaires
  typés avec `Any` aux frontières ; les entrées métier et modèles SQL sont annotés.
