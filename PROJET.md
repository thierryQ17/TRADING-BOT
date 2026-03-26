# Polymarket RBI Bot — Documentation projet

## Vue d'ensemble

Projet de trading automatise complet pour Polymarket, construit de zero avec Python et FastAPI.
3 bots independants, 3 strategies, interface web, backtesting, gestion des risques.

---

## Structure du projet

```
TRADING BOT/
├── api/                    # Serveur FastAPI + orchestrateur de bots
│   ├── server.py           # Routes API REST (port 1818) + lifespan shutdown
│   └── bot_manager.py      # Gestion des bots en threads background
├── bot/                    # Logique d'execution
│   ├── trader.py           # Boucle principale : signal → risk → execute
│   ├── risk_manager.py     # Limites de position, perte journaliere, stop-loss
│   ├── order_manager.py    # Gestion des limit orders + anti-doublons
│   └── position_tracker.py # Suivi des positions et PnL (calcul documente)
├── strategies/             # Les 3 strategies de trading
│   ├── base_strategy.py    # Classe abstraite (BUY/SELL/HOLD)
│   ├── macd_strategy.py    # MACD Histogram (3/15/3) — momentum
│   ├── rsi_mean_reversion.py # RSI(14) + VWAP — mean reversion
│   └── cvd_strategy.py     # Cumulative Volume Delta — divergence + qualite approx
├── backtesting/            # Moteur de test historique
│   ├── engine.py           # Simulateur avec stop-loss intra-bougie (high/low)
│   ├── metrics.py          # Win rate, Sharpe, drawdown, profit factor
│   └── runner.py           # Execution parallele multi-strategies
├── data/                   # Acces aux donnees
│   ├── downloader.py       # Telechargement OHLCV via ccxt (Binance)
│   ├── polymarket_client.py # Client CLOB API Polymarket (limit orders)
│   └── storage.py          # SQLite thread-safe (singleton + lock) + CSV
├── incubation/             # Monitoring et scaling progressif
│   ├── monitor.py          # Dashboard console temps reel
│   ├── scaler.py           # Scaling $1 → $100 avec level-up ET level-down
│   └── logger.py           # Logs structures JSONL + fichiers
├── dashboard/              # Interface web
│   ├── index.html          # Dashboard principal (theme gris clair)
│   ├── audit.html          # Rapport d'audit de code (15 points)
│   ├── docs.html           # Documentation complete du projet
│   ├── guide.html          # Guide utilisateur
│   └── i18n.json           # Textes et tooltips en francais (externalises)
├── deploy/                 # Scripts de lancement
│   ├── run_backtest.py     # Lancer le backtest des 3 strategies
│   ├── run_bot.py          # Lancer un bot en ligne de commande (live data)
│   └── run_monitor.py      # Lancer le monitoring console
├── config/                 # Configuration
│   ├── settings.py         # Settings dataclass thread-safe + constantes
│   └── accounts.py         # Multi-comptes Polymarket
├── tests/                  # Tests unitaires + integration
│   ├── test_strategies.py  # Tests des 3 strategies
│   ├── test_backtesting.py # Tests du moteur de backtest
│   ├── test_risk_manager.py # Tests du risk manager
│   ├── test_api_integration.py # Tests integration API FastAPI (16 tests)
│   └── test_storage.py     # Tests SQLite concurrent (3 tests)
├── start.bat               # Lanceur Windows (double-clic)
├── requirements.txt        # Dependances Python
├── .env.example            # Template des variables d'environnement
├── .env                    # Cles privees (non versionne)
└── .gitignore              # Fichiers exclus du versionning
```

---

## Ce qui a ete construit

### 1. Trois strategies de trading

| Strategie | Type | Signal d'entree | Parametres |
|-----------|------|-----------------|------------|
| **MACD (3/15/3)** | Momentum / Trend | Croisement MACD au-dessus du signal | fast=3, slow=15, signal=3 |
| **RSI + VWAP** | Mean Reversion | RSI < 30 + prix sous VWAP | RSI period=14, oversold=30 |
| **CVD Divergence** | Volume Delta | Divergence prix/volume + qualite approx | lookback=20 candles |

### 2. Moteur de backtesting

- Telecharge les donnees historiques via ccxt (Binance)
- Execute les strategies sur les donnees avec stop-loss et take-profit
- **Stop-loss intra-bougie** : verifie sur high/low (pas seulement close) — approche conservatrice
- Calcule : win rate, profit factor, max drawdown, Sharpe ratio (par trade, non annualise)
- Execution parallele multi-strategies
- Commande : `python deploy/run_backtest.py`

### 3. Systeme de trading live

- **Trader** : boucle signal → verification risque → execution ordre
  - Mode live : `data_fetcher` callable pour donnees temps reel
  - Mode replay : DataFrame statique pour dev/backtest
  - Callback `on_trade` pour reporter les events au BotManager
- **Risk Manager** : limite de taille, positions max, perte journaliere max, stop-loss/take-profit
- **Order Manager** : limit orders uniquement (0 frais Polymarket), anti-doublons
- **Position Tracker** : suivi positions ouvertes, PnL realise/non realise
  - Calcul PnL documente : `_compute_pnl()` avec docstring explicative
- Mode **DRY_RUN** par defaut (aucun ordre reel)

### 4. Incubation et scaling

- Echelle progressive : $1 → $5 → $10 → $50 → $100
- Conditions pour monter de niveau : 20 trades min, win rate > 55%, profit factor > 1.3
- **Level-down automatique** : win rate < 40% ou 5 pertes consecutives → retour au niveau inferieur
- Monitoring continu avec logs structures (JSONL)

### 5. API REST (FastAPI)

| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/bots` | Etat des 3 bots |
| POST | `/api/bots/{key}/start?token_id=...` | Demarrer un bot (token_id optionnel) |
| POST | `/api/bots/{key}/stop` | Arreter un bot |
| POST | `/api/bots/kill-all` | Arret d'urgence |
| GET | `/api/metrics` | Metriques globales |
| GET | `/api/trades?limit=50` | Journal des trades |
| GET | `/api/risk` | Etat du risk manager |
| GET | `/api/settings` | Parametres actuels |
| PUT | `/api/settings` | Modifier les parametres (valide par Pydantic) |

- **Validation** : `position_size` (0-1000$), `stop_loss_pct` (0-100%), `take_profit_pct` (0-100%)
- **CORS** : restreint a localhost:1818 par defaut (configurable via `CORS_ORIGINS`)
- **Graceful shutdown** : lifespan FastAPI → kill_all() + close_db()
- Documentation Swagger : http://localhost:1818/docs

### 6. Dashboard web

- **3 cartes bot** avec toggle start/stop, sparklines, taux de reussite, PnL
- **4 metriques cles** : PnL total, meilleure strategie, total trades, Sharpe ratio
- **Courbe de capital** (equity curve) par strategie
- **Taux de reussite** comparatif (bar chart)
- **Gestion des risques** : barre de perte journaliere, positions ouvertes, bouton arret d'urgence
- **Journal des trades** triable (50 derniers trades)
- **Parametres** : taille de position, stop-loss, take-profit, mode simulation, compte
- Theme gris clair
- Tooltips explicatifs sur tous les elements
- Textes externalises dans `i18n.json`
- Heure locale (France)
- Rafraichissement automatique toutes les 3 secondes
- Liens Guide, Docs, Audit et API (ouverture nouvel onglet)

### 7. Documentation

- **docs.html** : documentation complete (architecture, installation, strategies, backtesting, risk manager, incubation, API, risques)
- **audit.html** : rapport d'audit de code (15 points classes par severite)
- **guide.html** : guide utilisateur
- Accessible depuis le dashboard via les boutons dans le header

### 8. Lanceur Windows

- `start.bat` : double-clic pour tout lancer
- Cree le venv, installe les dependances, copie .env, lance le serveur, ouvre le navigateur
- Gestion des chemins avec espaces
- Console noire avec texte vert

### 9. Tests

- **37 tests** au total (18 unitaires + 19 integration)
- Tests unitaires : strategies, backtest, risk manager
- Tests integration : API FastAPI (16 tests), SQLite concurrent (3 tests)
- Validation des rejets Pydantic (422 sur valeurs hors bornes)
- Commande : `python -m pytest tests/ -v`

---

## Architecture technique

### Configuration thread-safe

Les parametres mutables sont encapsules dans une dataclass `Settings` avec `threading.Lock`.
Les constantes (parametres de strategies, endpoints) restent en module-level.
Chaque bot recoit sa propre copie de `dry_run` a l'instanciation — pas de mutation globale.

### SQLite thread-safe

Connexion singleton avec `check_same_thread=False` et `threading.Lock` pour serialiser les ecritures.
Plus de `init_db()` a chaque trade. `close_db()` appele au shutdown.

---

## Configuration

### Variables d'environnement (.env)

| Variable | Description | Defaut |
|----------|-------------|--------|
| `POLYMARKET_PRIVATE_KEY` | Cle privee du wallet Polygon | — |
| `POLYMARKET_FUNDER_ADDRESS` | Adresse du wallet | — |
| `POLYMARKET_TOKEN_ID` | Token ID du marche a trader | — |
| `MAX_POSITION_SIZE` | Taille max par position ($) | 10 |
| `MAX_DAILY_LOSS` | Perte journaliere max ($) | 50 |
| `MAX_OPEN_POSITIONS` | Nombre max de positions ouvertes | 3 |
| `DRY_RUN` | Mode simulation | true |
| `CORS_ORIGINS` | Origines CORS autorisees (virgule) | localhost:1818 |
| `LOG_LEVEL` | Niveau de log | INFO |

---

## Dependances

- py-clob-client (API Polymarket)
- pandas, numpy (calculs)
- ta (indicateurs techniques)
- ccxt (donnees de marche)
- fastapi, uvicorn (serveur web)
- python-dotenv (configuration)
- Chart.js (graphiques dashboard — via CDN)

---

## Lancement

```bash
# Methode simple
double-clic sur start.bat

# Methode manuelle
cd "C:\DEV POWERSHELL\__Q17\TRADING BOT"
.venv\Scripts\activate
python api/server.py
# → http://localhost:1818
```

---

## Securite

- Mode DRY_RUN active par defaut
- Cles privees dans .env (jamais versionne)
- CORS restreint a localhost (configurable)
- Validation Pydantic sur tous les parametres modifiables
- Limit orders uniquement (0 frais)
- Risk manager bloque les trades hors limites
- Scaler level-down protege le capital
- Graceful shutdown sauvegarde l'etat
- Bouton arret d'urgence sur le dashboard
