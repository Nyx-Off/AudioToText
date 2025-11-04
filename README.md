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

## Corrections

Cette version corrige :
- ✅ Case à cocher "Détecter les interlocuteurs" bien affichée
- ✅ Boutons Copier, Télécharger, Nouvelle transcription fonctionnels
- ✅ Format de sortie (JSON/TXT/SRT) correctement appliqué
- ✅ Détection de plusieurs interlocuteurs améliorée

## Formats supportés

MP3, WAV, M4A, FLAC, OGG, WebM
