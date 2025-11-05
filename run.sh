#!/bin/bash
# AudioToText Installation and Startup Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    print_status "Checking Python..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_success "Python $PYTHON_VERSION found"
            PYTHON_CMD="python3"
        else
            print_error "Python 3.8+ required. Current version: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 is not installed"
        exit 1
    fi
}

# Check if FFmpeg is installed
check_ffmpeg() {
    print_status "Checking FFmpeg..."
    if command -v ffmpeg &> /dev/null; then
        FFMPEG_VERSION=$(ffmpeg -version | head -n1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n1)
        print_success "FFmpeg $FFMPEG_VERSION found"
    else
        print_warning "FFmpeg is not installed. Installing..."
        if command -v apt-get &> /dev/null; then
            print_status "Installing FFmpeg via apt..."
            sudo apt-get update
            sudo apt-get install -y ffmpeg
        else
            print_error "Cannot install FFmpeg automatically. Please install manually."
            print_status "Visit: https://ffmpeg.org/download.html"
            exit 1
        fi
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    print_success "Dependencies installed"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p uploads outputs
    print_success "Directories created"
}

# Start web application
start_web_app() {
    print_status "Starting web application..."
    print_success "Web application started!"
    echo ""
    print_status "🌐 Access the application:"
    echo "   URL: http://localhost:8000"
    echo "   API Documentation: http://localhost:8000/docs"
    echo ""
    print_status "Press Ctrl+C to stop the application"
    echo ""
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Main installation function
install() {
    print_status "🎙️  Installing AudioToText..."
    echo ""
    check_python
    check_ffmpeg
    create_venv
    activate_venv
    install_dependencies
    create_directories
    echo ""
    print_success "✅ Installation completed successfully!"
    echo ""
    print_status "Usage:"
    echo "   Web application: ./run.sh --web"
    echo "   Command line: ./run.sh --cli"
    echo ""
}

# Parse command line arguments
case "${1:-}" in
    --install|install|"")
        install
        ;;
    --web|web)
        if [ ! -d "venv" ]; then
            print_warning "Application not installed. Installing..."
            install
        fi
        source venv/bin/activate
        start_web_app
        ;;
    --cli|cli)
        if [ ! -d "venv" ]; then
            print_warning "Application not installed. Installing..."
            install
        fi
        source venv/bin/activate
        print_status "CLI interface available. Commands:"
        echo "   python cli.py transcribe file.mp3"
        echo "   python cli.py info"
        echo "   python cli.py version"
        exec bash
        ;;
    --help|help|-h)
        echo "AudioToText - Installation and startup script"
        echo ""
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  --install, install  Install the complete application (default)"
        echo "  --web, web          Start the web application"
        echo "  --cli, cli          Start a shell with the environment activated"
        echo "  --help, help, -h    Show this help"
        echo ""
        echo "Examples:"
        echo "  ./run.sh           # Complete installation"
        echo "  ./run.sh --web     # Start web application"
        echo "  ./run.sh --cli     # Command line interface"
        ;;
    *)
        print_error "Unknown option: $1"
        print_status "Use --help to see available options"
        exit 1
        ;;
esac
