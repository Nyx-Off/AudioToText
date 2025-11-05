#!/bin/bash
# Script to easily configure HuggingFace token

echo "=========================================="
echo "HuggingFace Token Configuration"
echo "=========================================="
echo ""
echo "This script will help you configure your HuggingFace token"
echo "to enable speaker detection for multiple speakers."
echo ""
echo "If you don't have a token yet:"
echo "1. Create an account: https://huggingface.co/join"
echo "2. Accept the model: https://huggingface.co/pyannote/speaker-diarization-3.1"
echo "3. Get a token: https://huggingface.co/settings/tokens"
echo ""
read -p "Do you already have a HuggingFace token? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Steps to follow:"
    echo "1. Go to https://huggingface.co/join"
    echo "2. Create your account"
    echo "3. Go to https://huggingface.co/pyannote/speaker-diarization-3.1"
    echo "4. Click on 'Agree and access repository'"
    echo "5. Go to https://huggingface.co/settings/tokens"
    echo "6. Create a new token (type: Read)"
    echo "7. Run this script again"
    echo ""
    exit 0
fi

echo ""
echo "Paste your HuggingFace token (it starts with 'hf_'):"
read -r HF_TOKEN

# Trim whitespace
HF_TOKEN=$(echo "$HF_TOKEN" | xargs)

# Validate token format
if [[ ! $HF_TOKEN =~ ^hf_ ]]; then
    echo ""
    echo "⚠️  WARNING: The token should start with 'hf_'"
    echo "Do you want to continue anyway? (y/n)"
    read -p "" -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Configuration cancelled."
        exit 1
    fi
fi

# Save token to file
echo "$HF_TOKEN" > hf_token.txt

echo ""
echo "✅ Token saved in hf_token.txt"
echo ""
echo "To test:"
echo "  ./run.sh --web"
echo ""
echo "Upload an audio file with multiple voices and check"
echo "that multiple speakers are detected in the logs."
echo ""
echo "Good luck! 🎙️"
