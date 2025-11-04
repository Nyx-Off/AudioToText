#!/usr/bin/env python3
"""
AudioToText CLI Interface
Convert audio files to text with speaker detection
"""

import argparse
import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.transcribe import transcriber


def main():
    parser = argparse.ArgumentParser(
        description='Convert audio to text with speaker detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py transcribe audio.mp3
  python cli.py transcribe audio.mp3 --speakers --output result.txt
  python cli.py transcribe audio.mp3 --model small --format json
  python cli.py transcribe audio.mp3 --language fr --speakers
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Transcribe command
    transcribe_parser = subparsers.add_parser('transcribe', help='Transcribe audio file')
    transcribe_parser.add_argument('input_file', help='Input audio file path')
    transcribe_parser.add_argument('--speakers', action='store_true',
                                  help='Enable speaker diarization')
    transcribe_parser.add_argument('--model', choices=['tiny', 'base', 'small', 'medium'],
                                  default='base', help='Whisper model size (default: base)')
    transcribe_parser.add_argument('--language', help='Language code (e.g., fr, en, es)')
    transcribe_parser.add_argument('--output', '-o', help='Output file path')
    transcribe_parser.add_argument('--format', choices=['json', 'txt', 'srt'],
                                  default='txt', help='Output format (default: txt)')
    transcribe_parser.add_argument('--verbose', '-v', action='store_true',
                                  help='Show detailed progress')

    # Info command
    info_parser = subparsers.add_parser('info', help='Show system information')
    info_parser.add_argument('--models', action='store_true',
                            help='Show available models')

    # Version command
    version_parser = subparsers.add_parser('version', help='Show version information')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'transcribe':
        transcribe_file(args)
    elif args.command == 'info':
        show_info(args)
    elif args.command == 'version':
        show_version()


def transcribe_file(args):
    """Transcribe audio file"""
    input_file = Path(args.input_file)

    # Validate input file
    if not input_file.exists():
        print(f"❌ Erreur: Le fichier '{input_file}' n'existe pas", file=sys.stderr)
        sys.exit(1)

    if not input_file.is_file():
        print(f"❌ Erreur: '{input_file}' n'est pas un fichier", file=sys.stderr)
        sys.exit(1)

    # Check if file format is supported
    supported_formats = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.webm']
    if input_file.suffix.lower() not in supported_formats:
        print(f"❌ Erreur: Format de fichier non supporté: {input_file.suffix}")
        print(f"Formats supportés: {', '.join(supported_formats)}", file=sys.stderr)
        sys.exit(1)

    # Check file size (warn if very large)
    file_size_mb = input_file.stat().st_size / (1024 * 1024)
    if file_size_mb > 100:
        print(f"⚠️  Attention: Le fichier est très volumineux ({file_size_mb:.1f}MB)")
        print("   La transcription peut prendre du temps et utiliser beaucoup de mémoire.")

    try:
        if args.verbose:
            print(f"🎵 Transcription du fichier: {input_file}")
            print(f"📝 Modèle: {args.model}")
            print(f"👥 Détection d'interlocuteurs: {'Oui' if args.speakers else 'Non'}")
            print(f"🌐 Langue: {args.language if args.language else 'Auto-détection'}")
            print(f"📄 Format de sortie: {args.format}")
            print()

        # Perform transcription
        print("⏳ Début de la transcription...")
        result = transcriber.transcribe_audio(
            file_path=str(input_file),
            detect_speakers=args.speakers,
            model_size=args.model,
            language=args.language
        )

        # Format output
        formatted_output = transcriber.format_output(result, args.format)

        # Save to file or print to stdout
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_output)
            print(f"✅ Transcription terminée!")
            print(f"📁 Résultat sauvegardé dans: {output_path}")
        else:
            print("✅ Transcription terminée!")
            print("-" * 50)
            print(formatted_output)

        # Show statistics if verbose
        if args.verbose:
            print()
            print("📊 Statistiques:")
            print(f"   Durée: {format_duration(result.duration)}")
            print(f"   Interlocuteurs: {result.num_speakers}")
            print(f"   Langue détectée: {result.language or 'Non détectée'}")
            print(f"   Segments: {len(result.segments)}")

    except KeyboardInterrupt:
        print("\n❌ Transcription interrompue par l'utilisateur", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur lors de la transcription: {str(e)}", file=sys.stderr)
        sys.exit(1)


def show_info(args):
    """Show system information"""
    print("🎙️  AudioToText - Information Système")
    print("=" * 40)

    if args.models:
        print("📋 Modèles disponibles:")
        models = [
            ("tiny", "Très rapide, moins précis"),
            ("base", "Équilibré (recommandé)"),
            ("small", "Précis, plus lent"),
            ("medium", "Très précis, lent")
        ]
        for model, description in models:
            print(f"   {model:<8} - {description}")

    # Check system capabilities
    print("\n🔧 Capacités système:")

    # Check GPU availability
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
            print(f"   GPU: ✅ {gpu_count} détecté(s) ({gpu_name})")
        else:
            print("   GPU: ❌ Non disponible (utilisation du CPU)")
    except ImportError:
        print("   GPU: ⚠️  PyTorch non installé")

    # Check speaker diarization
    try:
        import pyannote.audio
        print("   Diarisation: ✅ Disponible")
    except ImportError:
        print("   Diarisation: ❌ pyannote.audio non installé")

    # Check disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        free_gb = free // (1024**3)
        print(f"   Espace disque: {free_gb}GB disponible")
    except:
        print("   Espace disque: ⚠️  Impossible de vérifier")

    # Show supported formats
    print("\n📄 Formats supportés:")
    formats = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.webm']
    print(f"   {', '.join(formats)}")


def show_version():
    """Show version information"""
    print("🎙️  AudioToText v1.0.0")
    print("Convertisseur audio vers texte avec détection d'interlocuteurs")
    print("Basé sur OpenAI Whisper et pyannote.audio")


def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"


if __name__ == '__main__':
    main()
