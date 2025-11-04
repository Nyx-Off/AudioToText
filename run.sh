#!/bin/bash

# AudioToText Installation and Startup Script
# This script sets up the environment and starts the application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.8+ is installed
check_python() {
    print_status "Vérification de Python..."

    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_success "Python $PYTHON_VERSION trouvé"
            PYTHON_CMD="python3"
        else
            print_error "Python 3.8 ou supérieur requis. Version actuelle: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 n'est pas installé"
        exit 1
    fi
}

# Check if FFmpeg is installed
check_ffmpeg() {
    print_status "Vérification de FFmpeg..."

    if command -v ffmpeg &> /dev/null; then
        FFMPEG_VERSION=$(ffmpeg -version | head -n1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n1)
        print_success "FFmpeg $FFMPEG_VERSION trouvé"
    else
        print_warning "FFmpeg n'est pas installé. Installation en cours..."

        # Detect distribution and install FFmpeg
        if command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            print_status "Installation de FFmpeg via apt..."
            sudo apt-get update
            sudo apt-get install -y ffmpeg
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL/Fedora
            print_status "Installation de FFmpeg via yum..."
            sudo yum install -y epel-release
            sudo yum install -y ffmpeg
        elif command -v dnf &> /dev/null; then
            # Fedora
            print_status "Installation de FFmpeg via dnf..."
            sudo dnf install -y ffmpeg
        elif command -v pacman &> /dev/null; then
            # Arch Linux
            print_status "Installation de FFmpeg via pacman..."
            sudo pacman -S --noconfirm ffmpeg
        else
            print_error "Impossible d'installer FFmpeg automatiquement. Veuillez l'installer manuellement."
            print_status "Visitez: https://ffmpeg.org/download.html"
            exit 1
        fi

        if command -v ffmpeg &> /dev/null; then
            print_success "FFmpeg installé avec succès"
        else
            print_error "L'installation de FFmpeg a échoué"
            exit 1
        fi
    fi
}

# Create virtual environment
create_venv() {
    print_status "Création de l'environnement virtuel..."

    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        print_success "Environnement virtuel créé"
    else
        print_warning "L'environnement virtuel existe déjà"
    fi
}

# Activate virtual environment
activate_venv() {
    print_status "Activation de l'environnement virtuel..."
    source venv/bin/activate
    print_success "Environnement virtuel activé"
}

# Upgrade pip
upgrade_pip() {
    print_status "Mise à jour de pip..."
    pip install --upgrade pip
    print_success "Pip mis à jour"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installation des dépendances Python..."

    # Install system dependencies for magic library
    if command -v apt-get &> /dev/null; then
        print_status "Installation des dépendances système pour python-magic..."
        sudo apt-get update
        sudo apt-get install -y libmagic1
    elif command -v yum &> /dev/null; then
        print_status "Installation des dépendances système pour python-magic..."
        sudo yum install -y file-devel
    elif command -v dnf &> /dev/null; then
        print_status "Installation des dépendances système pour python-magic..."
        sudo dnf install -y file-devel
    fi

    # Install Python packages
    pip install -r requirements.txt
    print_success "Dépendances Python installées"
}

# Create necessary directories
create_directories() {
    print_status "Création des répertoires nécessaires..."
    mkdir -p uploads outputs
    print_success "Répertoires créés"
}

# Make CLI script executable
make_executable() {
    print_status "Configuration des permissions..."
    chmod +x cli.py
    print_success "Scripts rendus exécutables"
}

# Function to start the web application
start_web_app() {
    print_status "Démarrage de l'application web..."
    print_success "Application web démarrée!"
    echo ""
    print_status "🌐 Accès à l'application:"
    echo "   URL: http://localhost:8000"
    echo "   Documentation API: http://localhost:8000/docs"
    echo ""
    print_status "Pour arrêter l'application, appuyez sur Ctrl+C"
    echo ""

    # Start the FastAPI application
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Function to run CLI
run_cli() {
    print_status "Interface CLI disponible. Commandes:"
    echo "   python cli.py transcribe fichier.mp3"
    echo "   python cli.py info"
    echo "   python cli.py version"
    echo ""
}

# Main installation function
install() {
    print_status "🎙️  Installation de AudioToText..."
    echo ""

    check_python
    check_ffmpeg
    create_venv
    activate_venv
    upgrade_pip
    install_dependencies
    create_directories
    make_executable

    echo ""
    print_success "✅ Installation terminée avec succès!"
    echo ""
    print_status "Utilisation:"
    echo "   Application web: ./run.sh --web"
    echo "   Ligne de commande: ./run.sh --cli"
    echo "   Ou activez l'environnement: source venv/bin/activate"
    echo ""
}

# Parse command line arguments
case "${1:-}" in
    --install|install|"")
        install
        ;;
    --web|web)
        if [ ! -d "venv" ]; then
            print_warning "L'application n'est pas installée. Installation en cours..."
            install
        fi
        source venv/bin/activate
        start_web_app
        ;;
    --cli|cli)
        if [ ! -d "venv" ]; then
            print_warning "L'application n'est pas installée. Installation en cours..."
            install
        fi
        source venv/bin/activate
        run_cli
        exec bash
        ;;
    --help|help|-h)
        echo "AudioToText - Script d'installation et de démarrage"
        echo ""
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  --install, install  (défaut) Installe l'application complète"
        echo "  --web, web          Démarre l'application web"
        echo "  --cli, cli          Démarre un shell avec l'environnement activé"
        echo "  --help, help, -h    Affiche cette aide"
        echo ""
        echo "Exemples:"
        echo "  ./run.sh           # Installation complète"
        echo "  ./run.sh --web     # Démarrer l'application web"
        echo "  ./run.sh --cli     # Interface ligne de commande"
        ;;
    *)
        print_error "Option inconnue: $1"
        print_status "Utilisez --help pour voir les options disponibles"
        exit 1
        ;;
esac