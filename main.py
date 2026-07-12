# main.py
"""
Haupteinstiegspunkt für die UltraStar Generator Anwendung
"""
import sys
import logging

# Setup Logging
from config.settings import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.app.log_directory / 'ultrastar.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def setup_dependencies():
    """Erstellt und konfiguriert alle Dependencies"""
    # Domain Services
    from domain.services.pitch_detection_service import PitchDetectionService
    from domain.services.beat_detection_service import BeatDetectionService

    pitch_service = PitchDetectionService()
    beat_service = BeatDetectionService()

    # Infrastructure
    from infrastructure.audio.librosa_audio_processor import LibrosaAudioProcessor
    from infrastructure.vocal_separation.vocal_separator_factory import VocalSeparatorFactory
    from infrastructure.persistence.ultrastar_file_repository import UltraStarFileRepository

    audio_processor = LibrosaAudioProcessor(
        sample_rate=config.audio.sample_rate,
        hop_length=config.audio.hop_length
    )

    vocal_separator = VocalSeparatorFactory.create(
        preferred=config.vocal_separation.preferred_model
    )

    file_repository = UltraStarFileRepository()

    # Application Services
    from application.services.ultrastar_generator_service import UltraStarGeneratorService

    generator_service = UltraStarGeneratorService(
        audio_processor=audio_processor,
        vocal_separator=vocal_separator,
        file_repository=file_repository,
        pitch_detection_service=pitch_service,
        beat_detection_service=beat_service
    )

    return generator_service


def run_gui():
    """Startet die GUI-Anwendung"""
    logger.info("Starte GUI...")

    # Setup Dependencies
    generator_service = setup_dependencies()

    # Setup MVC
    from presentation.models.ultrastar_model import UltraStarModel
    from presentation.controllers.ultrastar_controller import UltraStarController
    from presentation.views.ultrastar_view import UltraStarView

    # Model
    model = UltraStarModel()

    # Controller
    controller = UltraStarController(model, generator_service)

    # Kivy App
    from kivymd.app import MDApp

    class UltraStarApp(MDApp):
        def build(self):
            self.theme_cls.theme_style = config.app.theme_style
            self.theme_cls.primary_palette = config.app.primary_palette
            self.title = "UltraStar Generator"

            # View
            view = UltraStarView()
            view.controller = controller

            # Observer Pattern
            model.add_observer(view)

            return view

    # Run
    app = UltraStarApp()
    app.run()


def run_cli():
    """Startet die CLI-Anwendung"""
    import argparse

    parser = argparse.ArgumentParser(
        description='UltraStar Deluxe Karaoke Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('audio', help='Audio-Datei (MP3, WAV, etc.)')
    parser.add_argument('--lyrics', '-l', help='Lyrics-Datei (TXT, LRC)')
    parser.add_argument('--title', '-t', help='Song-Titel')
    parser.add_argument('--artist', '-a', help='Künstler')
    parser.add_argument('--output', '-o', help='Output-Pfad')

    args = parser.parse_args()

    # Setup Dependencies
    generator_service = setup_dependencies()

    # Process
    logger.info(f"Verarbeite: {args.audio}")

    # Parse Lyrics wenn vorhanden
    lyrics = None
    if args.lyrics:
        from presentation.controllers.ultrastar_controller import UltraStarController
        from presentation.models.ultrastar_model import UltraStarModel
        controller = UltraStarController(UltraStarModel(), generator_service)
        lyrics = controller._load_lyrics(args.lyrics)

    result = generator_service.generate_from_audio(
        audio_path=args.audio,
        title=args.title,
        artist=args.artist,
        lyrics=lyrics,
        output_path=args.output
    )

    if result.success:
        logger.info(f"✅ Erfolgreich: {result.output_path}")
    else:
        logger.error(f"❌ Fehler: {', '.join(result.errors)}")
        sys.exit(1)


def main():
    """Haupteinstiegspunkt"""
    if len(sys.argv) > 1 and sys.argv[1] != '--gui':
        # CLI-Modus
        run_cli()
    else:
        # GUI-Modus
        run_gui()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Programm beendet")
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}", exc_info=True)
        sys.exit(1)
