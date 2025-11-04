#!/usr/bin/env python3
"""
Test script to validate AudioToText project structure
"""

import os
import sys
from pathlib import Path

def test_project_structure():
    """Test that all required files and directories exist"""

    print("🧪 Test de la structure du projet AudioToText")
    print("=" * 50)

    # Required files
    required_files = [
        "README.md",
        "requirements.txt",
        "cli.py",
        "run.sh",
        "app/__init__.py",
        "app/main.py",
        "app/models.py",
        "app/transcribe.py",
        "app/exceptions.py",
        "templates/index.html",
        "app/static/css/style.css",
        "app/static/js/app.js"
    ]

    # Required directories
    required_dirs = [
        "app",
        "app/static",
        "app/static/css",
        "app/static/js",
        "templates",
        "uploads",
        "outputs"
    ]

    all_good = True

    # Test files
    print("📁 Vérification des fichiers requis:")
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✅ {file_path} ({size} bytes)")
        else:
            print(f"  ❌ {file_path} - MANQUANT")
            all_good = False

    print()

    # Test directories
    print("📂 Vérification des répertoires requis:")
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/ - MANQUANT")
            all_good = False

    print()

    # Test file permissions
    print("🔐 Vérification des permissions:")
    executables = ["cli.py", "run.sh"]
    for exe in executables:
        if os.access(exe, os.X_OK):
            print(f"  ✅ {exe} est exécutable")
        else:
            print(f"  ⚠️  {exe} n'est pas exécutable")

    print()

    # Test Python syntax
    print("🐍 Vérification de la syntaxe Python:")
    python_files = [
        "cli.py",
        "app/__init__.py",
        "app/main.py",
        "app/models.py",
        "app/transcribe.py",
        "app/exceptions.py"
    ]

    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                compile(f.read(), py_file, 'exec')
            print(f"  ✅ {py_file} - syntaxe OK")
        except SyntaxError as e:
            print(f"  ❌ {py_file} - erreur de syntaxe: {e}")
            all_good = False
        except Exception as e:
            print(f"  ⚠️  {py_file} - erreur: {e}")

    print()

    # Test basic imports (without dependencies)
    print("📦 Vérification des imports de base:")
    try:
        sys.path.insert(0, '.')

        # Test models import
        from app.models import TranscriptionRequest, TaskStatus, TranscriptionResult
        print("  ✅ app.models - import OK")

        # Test exceptions import
        from app.exceptions import AudioToTextException
        print("  ✅ app.exceptions - import OK")

    except ImportError as e:
        print(f"  ⚠️  Import error (normal sans dépendances): {e}")
    except Exception as e:
        print(f"  ❌ Erreur d'import: {e}")
        all_good = False

    print()

    # Summary
    if all_good:
        print("🎉 Tous les tests de structure sont passés avec succès!")
        print("✅ Le projet est prêt pour l'installation")
        return True
    else:
        print("❌ Certains tests ont échoué. Veuillez corriger les problèmes ci-dessus.")
        return False

if __name__ == "__main__":
    success = test_project_structure()
    sys.exit(0 if success else 1)