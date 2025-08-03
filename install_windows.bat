@echo off
REM UltraStar Generator - Windows Installation Script
chcp 65001 > nul

echo.
echo 🎵 UltraStar Generator Installation (Windows)
echo ==========================================
echo.

REM Prüfe Python
echo 📋 Prüfe Python Installation...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python nicht gefunden!
    echo.
    echo Bitte installiere Python 3.8 oder höher von:
    echo https://www.python.org/downloads/
    echo.
    echo WICHTIG: Aktiviere "Add Python to PATH" während der Installation!
    pause
    exit /b 1
)

python --version
echo ✅ Python gefunden
echo.

REM Erstelle Virtual Environment
echo 📦 Erstelle Virtual Environment...
if not exist "ultrastar_env" (
    python -m venv ultrastar_env
    if %errorlevel% neq 0 (
        echo ❌ Fehler beim Erstellen des Virtual Environment
        pause
        exit /b 1
    )
    echo ✅ Virtual Environment erstellt
) else (
    echo ✅ Virtual Environment existiert bereits
)

REM Aktiviere Virtual Environment
echo.
echo 📦 Aktiviere Virtual Environment...
call ultrastar_env\Scripts\activate.bat

REM Update pip
echo.
echo 📦 Update pip...
python -m pip install --upgrade pip setuptools wheel

REM Installiere Requirements
echo.
echo 📦 Installiere Basis-Dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Fehler bei der Installation der Dependencies
    pause
    exit /b 1
)

REM Prüfe FFmpeg
echo.
echo 🎬 Prüfe FFmpeg...
ffmpeg -version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ FFmpeg nicht gefunden!
    echo.
    echo Bitte lade FFmpeg herunter:
    echo 1. Gehe zu: https://www.gyan.dev/ffmpeg/builds/
    echo 2. Lade "release essentials" herunter
    echo 3. Entpacke und füge den 'bin' Ordner zu PATH hinzu
    echo.
    echo Oder verwende den Chocolatey Package Manager:
    echo choco install ffmpeg
) else (
    echo ✅ FFmpeg ist installiert
)

REM Installiere erweiterte Vocal-Separation
echo.
echo 🎵 Installiere erweiterte Vocal-Separation...
echo Installiere Demucs (empfohlen)...
pip install demucs
if %errorlevel% equ 0 (
    echo ✅ Demucs erfolgreich installiert!
    set DEMUCS_INSTALLED=true
) else (
    echo ⚠️  Demucs Installation fehlgeschlagen
    set DEMUCS_INSTALLED=false
)

REM Teste Installation
echo.
echo 🧪 Teste Installation...
python -c "import librosa, numpy, kivy, kivymd; print('✅ Alle Basis-Module erfolgreich importiert')"
python -c "try: import demucs; print('✅ Demucs verfügbar - Erweiterte Vocal-Separation aktiviert')" 2>nul || echo ⚠️  Keine erweiterte Vocal-Separation verfügbar

REM Erstelle Verzeichnisse
echo.
echo 📁 Erstelle Verzeichnisse...
if not exist "output" mkdir output
if not exist "logs" mkdir logs

REM Erstelle Start-Scripts
echo.
echo 📝 Erstelle Start-Scripts...

REM GUI Start Script
echo @echo off > start_gui.bat
echo call ultrastar_env\Scripts\activate.bat >> start_gui.bat
echo python start.py >> start_gui.bat
echo pause >> start_gui.bat

REM CLI Start Script
echo @echo off > start_cli.bat
echo call ultrastar_env\Scripts\activate.bat >> start_cli.bat
echo echo. >> start_cli.bat
echo echo UltraStar Generator - CLI Modus >> start_cli.bat
echo echo ================================ >> start_cli.bat
echo echo. >> start_cli.bat
echo echo Verwendung: python ultrastar_generator.py audio.mp3 --lyrics lyrics.txt >> start_cli.bat
echo echo. >> start_cli.bat
echo cmd /k >> start_cli.bat

echo ✅ Start-Scripts erstellt

REM Fertig
echo.
echo ============================================
echo 🎉 Installation abgeschlossen!
echo ============================================
echo.
echo 📖 Verwendung:
echo    GUI starten:  start_gui.bat
echo    CLI öffnen:   start_cli.bat
echo.
echo 💡 Tipps:
echo    - Für beste Ergebnisse verwende hochwertige Audio-Dateien
echo    - Installiere FFmpeg falls noch nicht geschehen
echo    - Siehe README.md für weitere Informationen
echo.
pause