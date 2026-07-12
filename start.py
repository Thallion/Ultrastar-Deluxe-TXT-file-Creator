# start.py
#!/usr/bin/env python3
"""
UltraStar Generator - Launcher Script
Überprüft Dependencies und startet die Anwendung mit DDD/MVC Architektur
"""

import sys
import subprocess
import importlib.util
from pathlib import Path


def check_dependency(package_name: str, import_name: str = None) -> bool:
    """Überprüft ob ein Package installiert ist"""
    if import_name is None:
        import_name = package_name
    
    spec = importlib.util.find_spec(import_name)
    return spec is not None


def check_project_structure() -> bool:
    """Überprüft ob die neue Projektstruktur vorhanden ist"""
    required_dirs = [
        'domain',
        'application', 
        'infrastructure',
        'presentation',
        'config'
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"❌ Fehlende Verzeichnisse: {', '.join(missing_dirs)}")
        print("\n💡 Die Projektstruktur wurde nach DDD/MVC refactored.")
        print("   Bitte stelle sicher, dass alle Verzeichnisse vorhanden sind.")
        return False
    
    return True


def install_requirements() -> bool:
    """Installiert Requirements automatisch"""
    print("📦 Installiere fehlende Dependencies...")
    
    requirements = [
        "librosa>=0.10.0",
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "soundfile>=0.12.0",
        "kivymd>=1.1.1",
        "kivy>=2.1.0"
    ]
    
    try:
        for req in requirements:
            package_name = req.split('>=')[0]
            if not check_dependency(package_name):
                print(f"   Installiere {package_name}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", req])
        
        print("✅ Alle Dependencies installiert!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation fehlgeschlagen: {e}")
        return False


def main():
    """Hauptfunktion"""
    print("🎵 UltraStar Deluxe Karaoke Generator - Clean Architecture Edition")
    print("=" * 60)
    
    # 1. Projektstruktur überprüfen
    if not check_project_structure():
        print("\n💡 Migrationshinweis:")
        print("   Die alte Struktur (ultrastar_generator.py, ultrastar_gui.py)")
        print("   wurde durch eine saubere DDD/MVC Architektur ersetzt.")
        print("\n   Verwende stattdessen: python main.py")
        input("\nDrücke Enter zum Beenden...")
        return
    
    # 2. Dependencies überprüfen
    missing_deps = []
    deps_to_check = [
        ("librosa", "librosa"),
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("soundfile", "soundfile"),
        ("kivymd", "kivymd"),
        ("kivy", "kivy")
    ]
    
    for package, import_name in deps_to_check:
        if not check_dependency(package, import_name):
            missing_deps.append(package)
    
    if missing_deps:
        print(f"\n📋 Fehlende Dependencies: {', '.join(missing_deps)}")
        response = input("\nAutomatisch installieren? (j/n): ").lower().strip()
        
        if response in ['j', 'ja', 'y', 'yes']:
            success = install_requirements()
            if not success:
                print("\n💡 Alternative:")
                print("   pip install -r requirements.txt")
                input("Drücke Enter zum Beenden...")
                return
        else:
            print("\n💡 Installiere Dependencies manuell:")
            print("   pip install -r requirements.txt")
            input("Drücke Enter zum Beenden...")
            return
    
    # 3. Modus auswählen
    print("\n🚀 Wie möchtest du das Tool starten?")
    print("1. GUI - Grafische Benutzeroberfläche (empfohlen)")
    print("2. CLI - Kommandozeile")
    print("3. Beenden")
    
    while True:
        choice = input("\nWähle (1/2/3): ").strip()
        
        if choice == "1":
            print("\n🖥️  Starte GUI...")
            try:
                from main import run_gui
                run_gui()
            except Exception as e:
                print(f"❌ GUI-Fehler: {e}")
                print("\n💡 Versuche CLI-Modus oder prüfe Dependencies")
                input("Drücke Enter zum Beenden...")
            break
        
        elif choice == "2":
            print("\n⌨️  CLI-Modus")
            print("Verwendung: python main.py <audio_file> [options]")
            print("\nBeispiele:")
            print("  python main.py song.mp3 --lyrics lyrics.txt --title 'My Song' --artist 'Artist'")
            print("  python main.py song.mp3 -l lyrics.txt -t 'My Song' -a 'Artist'")
            print("\nOptionen:")
            print("  --lyrics, -l   : Lyrics-Datei (optional)")
            print("  --title, -t    : Song-Titel (optional)")
            print("  --artist, -a   : Künstler (optional)")
            print("  --output, -o   : Output-Pfad (optional)")
            input("\nDrücke Enter zum Beenden...")
            break
        
        elif choice == "3":
            print("\n👋 Auf Wiedersehen!")
            break
        
        else:
            print("❌ Ungültige Auswahl. Bitte 1, 2 oder 3 eingeben.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Programm beendet.")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        input("Drücke Enter zum Beenden...")