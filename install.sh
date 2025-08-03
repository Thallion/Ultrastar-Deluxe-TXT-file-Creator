#!/bin/bash
# UltraStar Generator - Installation Script

echo "🎵 UltraStar Generator Installation"
echo "=================================="

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funktion für Fehlerbehandlung
error_exit() {
    echo -e "${RED}❌ Fehler: $1${NC}" 1>&2
    exit 1
}

# Prüfe Python Version
echo -e "\n${YELLOW}📋 Prüfe Python Installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo "✅ Python $PYTHON_VERSION gefunden"
    
    # Prüfe auf Python 3.12 (Problem mit Spleeter)
    if [[ "$PYTHON_VERSION" == "3.12" ]]; then
        echo -e "${YELLOW}⚠️  Python 3.12 erkannt - Spleeter ist nicht kompatibel${NC}"
        echo "   Wir verwenden stattdessen Demucs (bessere Qualität)"
    fi
else
    error_exit "Python 3 nicht gefunden. Bitte installiere Python 3.8 oder höher."
fi

# Prüfe auf Virtual Environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual Environment aktiv: $VIRTUAL_ENV"
else
    echo -e "${YELLOW}📦 Erstelle Virtual Environment...${NC}"
    python3 -m venv ultrastar_env || error_exit "Konnte Virtual Environment nicht erstellen"
    
    # Aktiviere Virtual Environment
    source ultrastar_env/bin/activate || error_exit "Konnte Virtual Environment nicht aktivieren"
    echo "✅ Virtual Environment erstellt und aktiviert"
fi

# Update pip
echo -e "\n${YELLOW}📦 Update pip...${NC}"
pip install --upgrade pip setuptools wheel

# Installiere Basis-Requirements
echo -e "\n${YELLOW}📦 Installiere Basis-Dependencies...${NC}"
pip install -r requirements.txt || error_exit "Fehler bei der Installation der Basis-Dependencies"

# Prüfe FFmpeg
echo -e "\n${YELLOW}🎬 Prüfe FFmpeg...${NC}"
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg ist installiert"
else
    echo -e "${RED}❌ FFmpeg nicht gefunden${NC}"
    echo "Bitte installiere FFmpeg:"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: Download von https://ffmpeg.org"
fi

# Installiere erweiterte Vocal-Separation
echo -e "\n${YELLOW}🎵 Installiere erweiterte Vocal-Separation...${NC}"

# Versuche Demucs zu installieren (empfohlen)
echo "Installiere Demucs (empfohlen)..."
if pip install demucs; then
    echo -e "${GREEN}✅ Demucs erfolgreich installiert!${NC}"
    DEMUCS_INSTALLED=true
else
    echo -e "${YELLOW}⚠️  Demucs Installation fehlgeschlagen${NC}"
    DEMUCS_INSTALLED=false
fi

# Falls Python < 3.12, versuche auch Spleeter
if [[ "$PYTHON_VERSION" != "3.12" ]] && [[ "$DEMUCS_INSTALLED" == "false" ]]; then
    echo -e "\n${YELLOW}Versuche Spleeter als Alternative...${NC}"
    if pip install spleeter; then
        echo -e "${GREEN}✅ Spleeter erfolgreich installiert!${NC}"
    else
        echo -e "${YELLOW}⚠️  Spleeter Installation fehlgeschlagen${NC}"
    fi
fi

# Optionale Dependencies
echo -e "\n${YELLOW}📦 Optionale Dependencies...${NC}"
echo "Möchtest du optionale Dependencies installieren? (j/n)"
read -r response

if [[ "$response" =~ ^[Jj]$ ]]; then
    # Matplotlib für Visualisierung
    pip install matplotlib
    
    # Silbentrennung
    pip install pyphen syllables
    
    echo -e "${GREEN}✅ Optionale Dependencies installiert${NC}"
fi

# Erstelle Verzeichnisse
echo -e "\n${YELLOW}📁 Erstelle Verzeichnisse...${NC}"
mkdir -p output
mkdir -p logs

# Test-Import
echo -e "\n${YELLOW}🧪 Teste Installation...${NC}"
python3 -c "
import librosa
import numpy
import kivy
import kivymd
print('✅ Alle Basis-Module erfolgreich importiert')

try:
    import demucs
    print('✅ Demucs verfügbar - Erweiterte Vocal-Separation aktiviert')
except:
    try:
        import spleeter
        print('✅ Spleeter verfügbar - Erweiterte Vocal-Separation aktiviert')
    except:
        print('⚠️  Keine erweiterte Vocal-Separation verfügbar')
"

# Fertig
echo -e "\n${GREEN}🎉 Installation abgeschlossen!${NC}"
echo -e "\n📖 Verwendung:"
echo "   GUI starten:  python start.py"
echo "   CLI:         python ultrastar_generator.py <audio.mp3> --lyrics <lyrics.txt>"
echo ""
echo "💡 Tipps:"
echo "   - Aktiviere das Virtual Environment: source ultrastar_env/bin/activate"
echo "   - Für beste Ergebnisse verwende hochwertige Audio-Dateien"
echo "   - Siehe README.md für weitere Informationen"

# Speichere Aktivierungs-Script
cat > activate.sh << 'EOF'
#!/bin/bash
source ultrastar_env/bin/activate
echo "✅ UltraStar Environment aktiviert"
echo "   GUI starten: python start.py"
echo "   Deaktivieren: deactivate"
EOF

chmod +x activate.sh
echo -e "\n${YELLOW}💡 Shortcut erstellt: ./activate.sh${NC}"