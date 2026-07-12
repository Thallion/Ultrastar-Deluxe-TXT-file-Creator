# tests/conftest.py
"""
Pytest-Konfiguration: Projekt-Root in sys.path aufnehmen,
damit die Layer-Pakete (domain, application, ...) importierbar sind
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
