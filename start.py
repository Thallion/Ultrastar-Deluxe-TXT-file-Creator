#!/usr/bin/env python3
"""
UltraStar Generator - Launcher Script
Überprüft Dependencies und startet die Anwendung
"""

import sys
import subprocess
import importlib.util
from pathlib import Path

def check_dependency(package_name, import_name=None):
    """Überprüft ob ein Package installiert ist"""
    if import_name is None:
        import_name = package_name
    
    spec = importlib.util.find_spec(import_name)
    return spec is not None

def install_requirements():
    """Installiert Requirements automatisch"""
    print("📦 Installiere fehlende Dependencies...")
    
    # Prüfe auf externally-managed-environment (Ubuntu 24.04+)
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", "--dry-run", "numpy"], 
                              capture_output=True, text=True)
        if "externally-managed-environment" in result.stderr:
            print("\n⚠️  Externally-managed-environment erkannt (Ubuntu/Debian)")
            print("💡 Verwende das Linux-Setup-Script:")
            print("   bash linux_setup.sh")
            print("\n   Oder erstelle manuell eine Virtual Environment:")
            print("   python3 -m venv ultrastar_env")
            print("   source ultrastar_env/bin/activate")
            print("   pip install librosa numpy kivymd kivy")
            return False
    except:
        pass
    
    requirements = [
        "librosa",
        "numpy", 
        "kivymd",
        "kivy"
    ]
    
    try:
        for req in requirements:
            if not check_dependency(req):
                print(f"   Installiere {req}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", req])
        
        print("✅ Alle Dependencies installiert!")
        return True
        
    except subprocess.CalledProcessError as e:
        if "externally-managed-environment" in str(e):
            print("\n⚠️  Installation blockiert - Externally-managed-environment")
            print("💡 Lösung für Ubuntu/Debian:")
            print("   1. Verwende: bash linux_setup.sh")
            print("   2. Oder: python3 -m venv ultrastar_env && source ultrastar_env/bin/activate")
        else:
            print(f"❌ Installation fehlgeschlagen: {e}")
        return False

def check_files():
    """Überprüft ob alle notwendigen Dateien vorhanden sind"""
    required_files = [
        "ultrastar_generator.py",
        "ultrastar_gui.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Fehlende Dateien: {', '.join(missing_files)}")
        return False
    
    return True

def main():
    """Hauptfunktion"""
    print("🎵 UltraStar Deluxe Karaoke Generator")
    print("=" * 40)
    
    # 1. Dateien überprüfen
    if not check_files():
        print("\n💡 Stelle sicher, dass alle Python-Dateien im gleichen Verzeichnis sind!")
        input("Drücke Enter zum Beenden...")
        return
    
    # 2. Dependencies überprüfen
    missing_deps = []
    deps_to_check = [
        ("librosa", "librosa"),
        ("numpy", "numpy"),
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
                print("\n💡 Alternative Installationsmethoden:")
                print("   1. Linux-Setup verwenden: bash linux_setup.sh")
                print("   2. Virtual Environment: python3 -m venv venv && source venv/bin/activate")
                print("   3. pipx verwenden: pipx install <package>")
                input("Drücke Enter zum Beenden...")
                return
        else:
            print("\n💡 Installiere Dependencies manuell:")
            print("   Ubuntu/Debian: bash linux_setup.sh")
            print("   Andere: pip install librosa numpy kivymd kivy")
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
                import ultrastar_gui
                ultrastar_gui.UltraStarApp().run()
            except Exception as e:
                print(f"❌ GUI-Fehler: {e}")
                print("\n💡 Versuche CLI-Modus oder prüfe Dependencies")
                input("Drücke Enter zum Beenden...")
            break
        
        elif choice == "2":
            print("\n⌨️  CLI-Modus")
            print("Verwendung: python ultrastar_generator.py <audio_file> [--lyrics lyrics.txt] [--reference original.txt]")
            print("\nBeispiele:")
            print("python ultrastar_generator.py song.mp3 --lyrics lyrics.txt --title 'My Song' --artist 'Artist'")
            print("python ultrastar_generator.py song.mp3 --lyrics lyrics.txt --reference original.txt")
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