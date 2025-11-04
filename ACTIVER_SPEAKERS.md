# 🎯 Activer la détection de plusieurs interlocuteurs

## Le problème

Pyannote nécessite un token HuggingFace car le modèle est "gated" (accès restreint).
Sans token, tous les segments sont assignés à "Speaker 1".

## Solution rapide (5 minutes)

### Étape 1 : Créer un compte HuggingFace
Allez sur : https://huggingface.co/join
- Utilisez votre email
- Confirmez votre compte

### Étape 2 : Accepter les conditions du modèle
Allez sur : https://huggingface.co/pyannote/speaker-diarization-3.1
- Cliquez sur "Agree and access repository"
- Acceptez les conditions d'utilisation

### Étape 3 : Obtenir votre token
Allez sur : https://huggingface.co/settings/tokens
- Cliquez sur "New token"
- Nom : "AudioToText"
- Type : "Read"
- Cliquez sur "Generate"
- **COPIEZ LE TOKEN** (il commence par "hf_...")

### Étape 4 : Configurer le token

#### Option A : Fichier hf_token.txt (RECOMMANDÉ - plus simple)
```bash
cd ~/AudioToText
echo "hf_VOTRE_TOKEN_ICI" > hf_token.txt
```

Remplacez `hf_VOTRE_TOKEN_ICI` par votre vrai token !

#### Option B : Variable d'environnement
```bash
export HF_TOKEN="hf_VOTRE_TOKEN_ICI"
```

Ou ajoutez dans ~/.bashrc pour le rendre permanent :
```bash
echo 'export HF_TOKEN="hf_VOTRE_TOKEN_ICI"' >> ~/.bashrc
source ~/.bashrc
```

#### Option C : Fichier .env
```bash
cd ~/AudioToText
echo "HF_TOKEN=hf_VOTRE_TOKEN_ICI" > .env
```

### Étape 5 : Relancer l'application
```bash
./run.sh --web
```

## Vérification

Quand vous uploadez un fichier audio avec plusieurs voix, vous devriez voir dans les logs :

```
Using HuggingFace token (length: XX)
Speaker diarization pipeline loaded successfully
Detected X speaker(s)
```

Au lieu de :
```
Warning: Could not load speaker diarization pipeline: 401 Client Error
No speaker diarization data, assigning all to Speaker 1
```

## Exemple complet

```bash
# 1. Obtenir le token sur https://huggingface.co/settings/tokens
# 2. Le mettre dans un fichier
cd ~/AudioToText
echo "hf_AbCdEfGhIjKlMnOpQrStUvWxYz1234567890" > hf_token.txt

# 3. Relancer
./run.sh --web

# 4. Tester avec un fichier audio ayant plusieurs voix
```

## Dépannage

**"401 Client Error"** → Token invalide ou non accepté les conditions
- Vérifiez que vous avez accepté : https://huggingface.co/pyannote/speaker-diarization-3.1
- Vérifiez que votre token est correct (copier-coller depuis HuggingFace)

**"No speaker diarization data"** → Le token n'est pas chargé
- Vérifiez que le fichier hf_token.txt existe dans le dossier AudioToText
- Vérifiez qu'il n'y a pas d'espaces ou de sauts de ligne dans le fichier

**Vérifier le token :**
```bash
cat hf_token.txt
# Devrait afficher : hf_xxxxxxxxxxxxx (sans rien d'autre)
```

## Note

⚠️ **GARDEZ VOTRE TOKEN SECRET !**
- Ne le partagez jamais
- Ne le commitez pas dans git (hf_token.txt est dans .gitignore)
- Si compromis, régénérez-en un nouveau sur HuggingFace
