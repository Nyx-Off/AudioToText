#!/bin/bash

# Script pour configurer facilement le token HuggingFace

echo "=========================================="
echo "Configuration du token HuggingFace"
echo "=========================================="
echo ""
echo "Ce script va vous aider à configurer votre token HuggingFace"
echo "pour activer la détection de plusieurs interlocuteurs."
echo ""
echo "Si vous n'avez pas encore de token:"
echo "1. Créez un compte: https://huggingface.co/join"
echo "2. Acceptez le modèle: https://huggingface.co/pyannote/speaker-diarization-3.1"
echo "3. Obtenez un token: https://huggingface.co/settings/tokens"
echo ""
read -p "Avez-vous déjà un token HuggingFace ? (o/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[OoYy]$ ]]; then
    echo ""
    echo "Étapes à suivre:"
    echo "1. Allez sur https://huggingface.co/join"
    echo "2. Créez votre compte"
    echo "3. Allez sur https://huggingface.co/pyannote/speaker-diarization-3.1"
    echo "4. Cliquez sur 'Agree and access repository'"
    echo "5. Allez sur https://huggingface.co/settings/tokens"
    echo "6. Créez un nouveau token (type: Read)"
    echo "7. Relancez ce script"
    echo ""
    exit 0
fi

echo ""
echo "Collez votre token HuggingFace (il commence par 'hf_'):"
read -r HF_TOKEN

# Trim whitespace
HF_TOKEN=$(echo "$HF_TOKEN" | xargs)

# Validate token format
if [[ ! $HF_TOKEN =~ ^hf_ ]]; then
    echo ""
    echo "⚠️  ATTENTION: Le token devrait commencer par 'hf_'"
    echo "Voulez-vous continuer quand même ? (o/n)"
    read -p "" -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[OoYy]$ ]]; then
        echo "Configuration annulée."
        exit 1
    fi
fi

# Save token to file
echo "$HF_TOKEN" > hf_token.txt

echo ""
echo "✅ Token sauvegardé dans hf_token.txt"
echo ""
echo "Pour tester:"
echo "  ./run.sh --web"
echo ""
echo "Uploadez un fichier audio avec plusieurs voix et vérifiez"
echo "que plusieurs speakers sont détectés dans les logs."
echo ""
echo "Bon test! 🎙️"
