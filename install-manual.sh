#!/bin/bash

# Script d'installation manuel pour Python 3.13
# Évite les problèmes de compatibilité avec Whisper

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "${GREEN}🎙️  Installation AudioToText pour Python 3.13${NC}"
echo "================================================"

# Activer l'environnement virtuel
source venv/bin/activate

echo "${YELLOW}📦 Installation des paquets de base...${NC}"
pip install --upgrade pip setuptools wheel
pip install fastapi uvicorn python-multipart aiofiles jinja2 python-magic

echo "${YELLOW}🤖 Installation de PyTorch (CPU)...${NC}"
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

echo "${YELLOW}🎤 Installation de Whisper (version compatible)...${NC}"
# Essayer plusieurs versions de Whisper
for version in "20240927" "20240930" "20231117"; do
    echo "Tentative avec openai-whisper==$version..."
    if pip install "openai-whisper==$version" --no-deps; then
        echo "✅ Whisper $version installé avec succès"
        break
    else
        echo "❌ Échec avec $version"
    fi
done

echo "${YELLOW}👥 Installation de pyannote.audio...${NC}"
pip install pyannote.audio

echo "${GREEN}✅ Installation terminée!${NC}"
echo ""
echo "Pour démarrer l'application:"
echo "./run.sh --web"