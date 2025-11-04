# AudioToText

Convertir des voix, des paroles en Texte, même s'il y a plusieurs interlocuteurs.

## Installation

```bash
./run.sh --install
```

## Utilisation

### Interface Web
```bash
./run.sh --web
```
Puis ouvrir http://localhost:8000

### Ligne de commande
```bash
source venv/bin/activate
python cli.py transcribe fichier.mp3 --speakers
```

## ⚠️ Détection de plusieurs interlocuteurs

Pour détecter correctement plusieurs speakers, vous devez configurer un token HuggingFace (gratuit).

**Solution rapide (5 minutes):**
```bash
./setup_token.sh
```

**Ou manuellement:**
1. Créez un compte: https://huggingface.co/join
2. Acceptez: https://huggingface.co/pyannote/speaker-diarization-3.1
3. Token: https://huggingface.co/settings/tokens
4. Créez le fichier: `echo "hf_VOTRE_TOKEN" > hf_token.txt`

📖 Voir **ACTIVER_SPEAKERS.md** pour le guide complet

## Corrections

Cette version corrige :
- ✅ Case à cocher "Détecter les interlocuteurs" bien affichée
- ✅ Boutons Copier, Télécharger, Nouvelle transcription fonctionnels
- ✅ Format de sortie (JSON/TXT/SRT) correctement appliqué
- ✅ Support du token HuggingFace pour détection speakers

## Formats supportés

MP3, WAV, M4A, FLAC, OGG, WebM
