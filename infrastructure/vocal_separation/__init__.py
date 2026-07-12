"""
Vocal Separation Implementierungen
"""
from infrastructure.vocal_separation.vocal_separator_factory import VocalSeparatorFactory
from infrastructure.vocal_separation.demucs_separator import DemucsSeparator
from infrastructure.vocal_separation.spleeter_separator import SpleeterSeparator
from infrastructure.vocal_separation.basic_separator import BasicHarmonicSeparator

__all__ = ['VocalSeparatorFactory', 'DemucsSeparator', 'SpleeterSeparator', 'BasicHarmonicSeparator']
