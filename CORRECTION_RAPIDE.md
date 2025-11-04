# 🚀 Correction Rapide - AudioToText

Si vous avez déjà le projet installé et qu'il ne fonctionne pas, suivez ce guide pour corriger rapidement les problèmes.

## Option 1 : Correction manuelle (RAPIDE - 2 minutes)

### Étape 1 : Corriger app/main.py

Ouvrez `app/main.py` et trouvez la ligne 248 (environ) qui contient :
```python
return JSONResponse(task.result.model_dump())
```

Remplacez-la par :
```python
return JSONResponse(task.result.model_dump(mode='json'))
```

### Étape 2 : Corriger app/transcribe.py

Ouvrez `app/transcribe.py` et trouvez la fonction `load_pyannote_pipeline` (ligne 40 environ).

Remplacez :
```python
self.pyannote_pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=False  # Using the public model
)
```

Par :
```python
self.pyannote_pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1"
)
```

### Étape 3 : Redémarrer l'application

```bash
# Dans votre terminal, arrêtez l'application (Ctrl+C)
# Puis relancez :
./run.sh --web
```

**C'EST TOUT ! L'application devrait maintenant fonctionner.** 🎉

---

## Option 2 : Réinstallation complète (RECOMMANDÉ)

Si la correction manuelle ne fonctionne pas :

```bash
# 1. Sauvegarder vos fichiers audio si besoin
cd ~/AudioToText

# 2. Télécharger le nouveau ZIP corrigé depuis Claude

# 3. Extraire le nouveau projet
cd ~
unzip AudioToText_COMPLETE_FIXED.zip
cd AudioToText

# 4. Réinstaller
./run.sh --install

# 5. Lancer
./run.sh --web
```

---

## 🧪 Test rapide

Une fois l'application lancée :

1. Ouvrez http://localhost:8000 dans votre navigateur
2. Glissez-déposez un fichier audio court (< 1 minute recommandé pour le test)
3. Cliquez sur "Commencer la transcription"
4. Attendez que la transcription se termine
5. Vous devriez voir le résultat s'afficher !

---

## 📊 Vérification des logs

Si l'application démarre, vous devriez voir dans le terminal :

```
✅ BON SIGNE :
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.

⚠️ WARNING ACCEPTABLE (optionnel) :
Warning: Could not load speaker diarization pipeline: ...
→ Normal si vous n'avez pas de token HuggingFace
→ L'app fonctionne quand même sans diarisation

✅ TRANSCRIPTION EN COURS :
Loading Whisper model: base
100%|██████████| XXXXX/XXXXX [XX:XX<00:00, XXXframes/s]

❌ ERREUR À ÉVITER :
TypeError: Object of type datetime is not JSON serializable
→ Si vous voyez ça, refaites la correction de l'étape 1
```

---

## 💡 Astuces

**Pour transcription plus rapide :**
- Utilisez le modèle "tiny" ou "base" au lieu de "medium"
- Les modèles plus gros sont plus précis mais beaucoup plus lents

**Pour économiser la mémoire :**
- Fermez les autres applications
- Utilisez des fichiers audio courts (< 10 minutes)

**Si ça plante pendant la transcription :**
- Vérifiez que vous avez assez de RAM (4GB minimum recommandé)
- Essayez un fichier plus court
- Utilisez le modèle "tiny"

---

## 🆘 Besoin d'aide ?

Si rien ne fonctionne :

1. Copiez le message d'erreur complet du terminal
2. Vérifiez votre version Python : `python3 --version` (doit être 3.8+)
3. Vérifiez FFmpeg : `ffmpeg -version`
4. Essayez de réinstaller complètement (Option 2)

---

**Bon courage ! L'application en vaut la peine une fois qu'elle fonctionne ! 🎙️**
