# AudioToText 🎙️

Convertir des voix, des paroles en Texte, même s'il y a plusieurs interlocuteurs.

Une application gratuite et open-source qui fonctionne entièrement hors ligne sur Linux, utilisant les technologies les plus avancées de reconnaissance vocale.

## ✨ Fonctionnalités

- 🎯 **Reconnaissance vocale précise** avec OpenAI Whisper
- 👥 **Détection d'interlocuteurs multiples** avec pyannote.audio
- 🌐 **Interface web intuitive** pour un usage simple
- 💻 **Interface ligne de commande** pour l'automatisation
- 🔒 **100% privé et local** - aucun envoi de données externes
- 🆓 **Entièrement gratuit** - que des technologies open-source
- 📁 **Formats supportés** : MP3, WAV, M4A, FLAC, OGG, WebM
- 📄 **Export multiple** : Texte, JSON, SRT (sous-titres)

## 🚀 Installation Rapide

### Prérequis

- Python 3.8 ou supérieur
- FFmpeg (installé automatiquement par le script)
- Linux (Ubuntu, Debian, Fedora, CentOS, Arch...)

### Installation automatique

```bash
# Clonez le projet
git clone <repository-url>
cd AudioToText

# Lancez l'installation complète
./run.sh --install
```

Le script d'installation va automatiquement :
- ✅ Vérifier Python 3.8+
- ✅ Installer FFmpeg si nécessaire
- ✅ Créer un environnement virtuel
- ✅ Installer toutes les dépendances
- ✅ Configurer les permissions

## 📖 Utilisation

### Interface Web (Recommandé)

```bash
# Démarrez l'application web
./run.sh --web
```

Ouvrez votre navigateur et accédez à **http://localhost:8000**

1. Glissez-déposez votre fichier audio ou cliquez pour parcourir
2. Choisissez les options (détection d'interlocuteurs, modèle, langue)
3. Cliquez sur "Commencer la transcription"
4. Téléchargez le résultat dans le format de votre choix

### Ligne de Commande

```bash
# Activez l'environnement
source venv/bin/activate

# Transcription simple
python cli.py transcribe mon_fichier_audio.mp3

# Avec détection d'interlocuteurs
python cli.py transcribe meeting.mp3 --speakers

# Choix du modèle (plus précis mais plus lent)
python cli.py transcribe interview.wav --model small --speakers

# Export en JSON avec langue spécifiée
python cli.py transcribe podcast.m4a --language fr --format json

# Voir toutes les options
python cli.py --help
```

## 🎛️ Options et Configuration

### Modèles Whisper disponibles

| Modèle | Taille | Vitesse | Précision | Usage |
|--------|-------|---------|-----------|-------|
| tiny | ~39MB | ⚡ Très rapide | 📉 Moyenne | Brouillons rapides |
| base | ~74MB | 🚀 Rapide | 📈 Bonne | **Recommandé** |
| small | ~244MB | 🐢 Modéré | 📊 Très bonne | Usage quotidien |
| medium | ~769MB | 🐌 Lent | 🎯 Excellente | Haute précision |

### Formats de sortie

- **Texte simple** : `[00:00:00] Speaker 1: Bonjour comment allez-vous?`
- **JSON** : Structure complet avec métadonnées
- **SRT** : Sous-titres pour vidéos

### Langues supportées

Français, English, Español, Deutsch, Italiano, Português, Nederlands, Русский, 中文, 日本語, et bien d'autres!

## 🏗️ Architecture Technique

```
AudioToText/
├── app/
│   ├── main.py              # FastAPI web server
│   ├── transcribe.py        # Core transcription engine
│   ├── models.py            # Data structures
│   ├── exceptions.py        # Error handling
│   └── static/              # Web assets
├── templates/
│   └── index.html           # Web interface
├── cli.py                   # Command-line interface
├── requirements.txt         # Python dependencies
└── run.sh                   # Installation script
```

## 🔧 Dépannage

### Problèmes courants

**"FFmpeg non trouvé"**
```bash
# Installation manuelle
sudo apt-get install ffmpeg          # Ubuntu/Debian
sudo yum install ffmpeg              # CentOS/RHEL
sudo dnf install ffmpeg              # Fedora
sudo pacman -S ffmpeg                # Arch Linux
```

**"Mémoire insuffisante"**
- Utilisez le modèle `tiny` ou `base`
- Réduisez la taille des fichiers audio
- Fermez d'autres applications

**"GPU non détecté"**
- L'application fonctionne parfaitement sur CPU
- Pour GPU : installez les pilotes CUDA/ROCm
- PyTorch utilisera automatiquement le GPU si disponible

### Logs et erreurs

Les logs sont affichés dans la console lors de l'exécution. Pour des logs détaillés :

```bash
# Mode verbose pour la CLI
python cli.py transcribe fichier.mp3 --verbose

# Logs de l'application web
./run.sh --web 2>&1 | tee web.log
```

## 🤝 Contribuer

Contributions sont les bienvenues! Voici comment commencer :

1. Fork le projet
2. Créez une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commitez vos changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- **OpenAI** pour le modèle Whisper [github.com/openai/whisper](https://github.com/openai/whisper)
- **pyannote.audio** pour la diarisation [github.com/pyannote/pyannote-audio](https://github.com/pyannote/pyannote-audio)
- **FastAPI** pour le framework web [fastapi.tiangolo.com](https://fastapi.tiangolo.com)

## 📞 Support

- 📖 Documentation complète dans ce README
- 🐛 Reportez les issues sur GitHub
- 💬 Discussions et suggestions bienvenues

---

**AudioToText** - Créé avec ❤️ pour rendre la transcription accessible à tous.