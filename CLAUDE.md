# CLAUDE.md — Instructions pour Claude Code

## Projet

Trading bot automatise pour Polymarket (Python 3.12 / FastAPI / Docker).
4 strategies : MACD, RSI+VWAP, CVD Divergence, Copy Trading.

## Regles critiques

### Bugs critiques = action immediate

Si une analyse ou une lecture de code revele un probleme critique (securite, protection du capital, perte de donnees, deadlock, etc.) :

1. **Signaler immediatement** le probleme a l'utilisateur avec son impact concret
2. **Proposer de corriger dans la foulee** sans attendre une demande explicite
3. Ne jamais se contenter de lister les problemes dans un rapport sans agir

Un parametre de configuration qui existe mais n'est jamais utilise dans le code (ex: stop-loss decoratif) est un **bug critique**, pas un detail.

### Protection du capital = priorite absolue

Tout ce qui touche a la gestion du risque en trading est critique :
- Stop-loss, take-profit, trailing TP doivent etre **executes**, pas juste calcules
- Le sizing dynamique doit etre base sur le capital reel, pas une valeur fixe
- Le scaler doit etre connecte au trader, pas isole

### Pas d'interruptions inutiles

Quand l'utilisateur donne une instruction d'implementation multi-fichiers, executer toutes les modifications sans demander de validation a chaque fichier. Demander confirmation uniquement pour les decisions d'architecture ambigues.

## Stack technique

- **Backend** : Python 3.12, FastAPI, uvicorn
- **Trading** : py-clob-client, ccxt (donnees Binance)
- **Data** : pandas, numpy, ta (indicateurs techniques)
- **Storage** : SQLite (trades), CSV (backtest)
- **Frontend** : HTML/CSS/JS vanilla, Chart.js
- **Infra** : Docker Compose, nginx, Let's Encrypt
- **Tests** : pytest (47 tests), les tests API echouent a cause de l'auth (preexistant)

## Conventions

- Code et commentaires en anglais, documentation utilisateur en francais
- Commits en anglais avec prefixe conventionnel (feat/fix/refactor)
- Limite orders uniquement sur Polymarket (0 frais vs 2% market orders)
- Dry-run active par defaut — jamais de vrais ordres sans configuration explicite
