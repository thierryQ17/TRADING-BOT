#!/bin/bash
# =============================================================================
# Script de deploiement - Trading Bot
# Usage: ssh Qiou17@37.59.123.9 "~/projects/trading-bot/scripts/deploy.sh"
# =============================================================================
set -e

echo "=============================================="
echo "   DEPLOIEMENT TRADING BOT"
echo "   $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="

# Repertoire du projet
PROJECT_DIR=~/projects/trading-bot

# Verifier que le repertoire existe
if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERREUR: Repertoire $PROJECT_DIR non trouve"
    echo ""
    echo "Premier deploiement ? Executer ces commandes :"
    echo "  mkdir -p ~/projects/trading-bot"
    echo "  cd ~/projects/trading-bot"
    echo "  git clone -b main https://github.com/thierryQ17/TRADING-BOT.git ."
    echo "  cp .env.example .env"
    echo "  nano .env  # remplir les secrets"
    exit 1
fi

cd "$PROJECT_DIR"

echo ""
echo "[1/5] Recuperation des dernieres modifications..."
git fetch origin
git reset --hard origin/main
echo "    Branche: $(git branch --show-current)"
echo "    Commit: $(git log -1 --format='%h - %s')"

echo ""
echo "[2/5] Verification du fichier .env..."
if [ ! -f .env ]; then
    echo "    .env manquant — copie du template"
    cp .env.example .env
    echo "    ATTENTION: editer .env avec les vrais secrets avant de continuer"
    echo "    nano $PROJECT_DIR/.env"
    exit 1
fi

echo ""
echo "[3/5] Arret des containers existants..."
docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true

echo ""
echo "[4/5] Build et demarrage..."
docker compose up -d --build 2>/dev/null || docker-compose up -d --build

echo ""
echo "[5/5] Verification de sante..."
sleep 10

HEALTH_URL="http://localhost:8818/api/bots"
if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    HEALTH_STATUS="OK"
else
    HEALTH_STATUS="FAIL"
fi

echo ""
echo "=============================================="
if [ "$HEALTH_STATUS" = "OK" ]; then
    echo "  DEPLOIEMENT REUSSI"
    echo "=============================================="
    echo ""
    echo "  URL: https://trading.youpiare.fr"
    echo "  API: https://trading.youpiare.fr/docs"
    echo ""
    echo "  Container:"
    docker ps --format "    - {{.Names}}: {{.Status}}" | grep "trading"
else
    echo "  ERREUR DEPLOIEMENT"
    echo "=============================================="
    echo ""
    echo "  Health check: $HEALTH_STATUS"
    echo ""
    echo "  Logs:"
    docker compose logs --tail=30 2>/dev/null || docker-compose logs --tail=30
    exit 1
fi
