"""
Application Interfaces - Ports für externe Abhängigkeiten
"""
from application.interfaces.audio_processor_interface import AudioProcessorInterface
from application.interfaces.vocal_separator_interface import VocalSeparatorInterface
from application.interfaces.file_repository_interface import FileRepositoryInterface

__all__ = ['AudioProcessorInterface', 'VocalSeparatorInterface', 'FileRepositoryInterface']
