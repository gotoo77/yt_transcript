# YouTube Transcript Analyzer

Application Flask d'extraction de transcriptions YouTube, analyse textuelle,
sentiment, statistiques, historique SQLite et exports PDF / Excel / JSON / CSV.
Windows 11 et Linux, Python 3.11+ 64 bits.

## Installation et lancement

Installer [uv](https://docs.astral.sh/uv/getting-started/installation/), puis :

```sh
uv sync --locked
uv run yt-transcript serve
```

Ouvrir http://127.0.0.1:5001. Le serveur utilise
[Waitress](https://flask.palletsprojects.com/en/stable/deploying/waitress/).
`uv run yt-transcript dev` active le rechargement et le debug de développement.

[Administration, configuration, ancienne base et DevMenu](README_LAUNCH.md).

## Qualité et tests

```sh
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest --cov --cov-report=html
uv run python scripts/check.py
uv build
uv run python scripts/smoke_wheel.py
```

`pyproject.toml` centralise dépendances, build et contrôles ; `uv.lock` fixe leurs
versions. Mypy analyse tous les modules applicatifs avec annotations obligatoires.
Les payloads historiques hétérogènes gardent des `dict[str, Any]` aux frontières ;
les fonctions métier et modèles SQL ont des types explicites.

Les tests vérifient des valeurs métier attendues, les entrées invalides, le repli
YouTube simulé, les bases SQLite isolées, les réponses HTTP, les exports réels et
le cycle démarrage/arrêt d'un serveur. Ils ne contactent pas YouTube.
Le test du wheel l'installe hors dépôt dans un environnement temporaire, puis
vérifie le serveur HTTP et ses ressources. Cette étape nécessite l'accès au registre
de packages. La CI est configurée pour Windows/Linux et Python 3.11/3.13.

## Structure

```text
src/yt_transcript/     application, services, CLI, templates et JavaScript
tests/                tests unitaires et d'intégration
scripts/              contrôles et vérification du wheel
.devmenu.json         configuration du moteur DevMenu externe
pyproject.toml        packaging et configuration des outils
uv.lock               dépendances résolues
```

La récupération des transcriptions nécessite YouTube et dépend de leur disponibilité.
Les analyses et TU fonctionnent hors réseau, sans téléchargement de corpus.
Le sentiment TextBlob est principalement adapté à l'anglais ; lisibilité et résumés
restent heuristiques. Les documents `PHASE*.md` décrivent l'historique du projet.
