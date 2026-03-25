# Polymarket RBI Bot — Travail accompli

## Vue d'ensemble

Projet de trading automatise complet pour Polymarket, construit de zero avec Python et FastAPI.
3 bots independants, 3 strategies, interface web, backtesting, gestion des risques.

---

## Structure du projet

```
TRADING BOT/
├── api/                    # Serveur FastAPI + orchestrateur de bots
│   ├── server.py           # Routes API REST (port 1818)
│   └── bot_manager.py      # Gestion des bots en threads background
├── bot/                    # Logique d'execution
│   ├── trader.py           # Boucle principale : signal → risk → execute
│   ├── risk_manager.py     # Limites de position, perte journaliere, stop-loss
│   ├── order_manager.py    # Gestion des limit orders + anti-doublons
│   └── position_tracker.py # Suivi des positions et PnL
├── strategies/             # Les 3 strategies de trading
│   ├── base_strategy.py    # Classe abstraite (BUY/SELL/HOLD)
│   ├── macd_strategy.py    # MACD Histogram (3/15/3) — momentum
│   ├── rsi_mean_reversion.py # RSI(14) + VWAP — mean reversion
│   └── cvd_strategy.py     # Cumulative Volume Delta — divergence
├── backtesting/            # Moteur de test historique
│   ├── engine.py           # Simulateur avec stop-loss/take-profit
│   ├── metrics.py          # Win rate, Sharpe, drawdown, profit factor
│   └── runner.py           # Execution parallele multi-strategies
├── data/                   # Acces aux donnees
│   ├── downloader.py       # Telechargement OHLCV via ccxt (Binance)
│   ├── polymarket_client.py # Client CLOB API Polymarket (limit orders)
│   └── storage.py          # SQLite pour les trades + CSV pour les candles
├── incubation/             # Monitoring et scaling progressif
│   ├── monitor.py          # Dashboard console temps reel
│   ├── scaler.py           # Scaling $1 → $5 → $10 → $50 → $100
│   └── logger.py           # Logs structures JSONL + fichiers
├── dashboard/              # Interface web
│   ├── index.html          # Dashboard principal (theme gris clair)
│   ├── docs.html           # Documentation complete du projet
│   └── i18n.json           # Textes et tooltips en francais (externalises)
├── deploy/                 # Scripts de lancement
│   ├── run_backtest.py     # Lancer le backtest des 3 strategies
│   ├── run_bot.py          # Lancer un bot en ligne de commande
│   └── run_monitor.py      # Lancer le monitoring console
├── config/                 # Configuration
│   ├── settings.py         # Parametres globaux (risk, strategies, API)
│   └── accounts.py         # Multi-comptes Polymarket
├── tests/                  # Tests unitaires
│   ├── test_strategies.py  # Tests des 3 strategies
│   ├── test_backtesting.py # Tests du moteur de backtest
│   └── test_risk_manager.py # Tests du risk manager
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
| **CVD Divergence** | Volume Delta | Divergence prix/volume | lookback=20 candles |

### 2. Moteur de backtesting

- Telecharge les donnees historiques via ccxt (Binance)
- Execute les strategies sur les donnees avec stop-loss et take-profit
- Calcule : win rate, profit factor, max drawdown, Sharpe ratio
- Execution parallele multi-strategies
- Commande : `python deploy/run_backtest.py`

### 3. Systeme de trading live

- **Trader** : boucle signal → verification risque → execution ordre
- **Risk Manager** : limite de taille, positions max, perte journaliere max, stop-loss/take-profit
- **Order Manager** : limit orders uniquement (0 frais Polymarket), anti-doublons
- **Position Tracker** : suivi positions ouvertes, PnL realise/non realise
- Mode **DRY_RUN** par defaut (aucun ordre reel)

### 4. Incubation et scaling

- Echelle progressive : $1 → $5 → $10 → $50 → $100
- Conditions pour monter de niveau : 20 trades min, win rate > 55%, profit factor > 1.3
- Monitoring continu avec logs structures (JSONL)

### 5. API REST (FastAPI)

| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/bots` | Etat des 3 bots |
| POST | `/api/bots/{key}/start` | Demarrer un bot |
| POST | `/api/bots/{key}/stop` | Arreter un bot |
| POST | `/api/bots/kill-all` | Arret d'urgence |
| GET | `/api/metrics` | Metriques globales |
| GET | `/api/trades?limit=50` | Journal des trades |
| GET | `/api/risk` | Etat du risk manager |
| GET | `/api/settings` | Parametres actuels |
| PUT | `/api/settings` | Modifier les parametres |

Documentation Swagger : http://localhost:1818/docs

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
- Liens Docs et API (ouverture nouvel onglet)

### 7. Documentation

- Page HTML complete (`dashboard/docs.html`)
- Couvre : architecture, installation, strategies, backtesting, risk manager, incubation, API, risques
- Accessible depuis le dashboard via le bouton "Docs"

### 8. Lanceur Windows

- `start.bat` : double-clic pour tout lancer
- Cree le venv, installe les dependances, copie .env, lance le serveur, ouvre le navigateur
- Console noire avec texte vert

---

## Configuration

### Variables d'environnement (.env)

| Variable | Description | Defaut |
|----------|-------------|--------|
| `POLYMARKET_PRIVATE_KEY` | Cle privee du wallet Polygon | — |
| `POLYMARKET_FUNDER_ADDRESS` | Adresse du wallet | — |
| `MAX_POSITION_SIZE` | Taille max par position ($) | 10 |
| `MAX_DAILY_LOSS` | Perte journaliere max ($) | 50 |
| `MAX_OPEN_POSITIONS` | Nombre max de positions ouvertes | 3 |
| `DRY_RUN` | Mode simulation | true |

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
cd "C:\DEV POWERSHELL\TRADING BOT"
.venv\Scripts\activate
python api/server.py
# → http://localhost:1818
```

---

## Securite

- Mode DRY_RUN active par defaut
- Cles privees dans .env (jamais versionne)
- Limit orders uniquement (0 frais)
- Risk manager bloque les trades hors limites
- Bouton arret d'urgence sur le dashboard
