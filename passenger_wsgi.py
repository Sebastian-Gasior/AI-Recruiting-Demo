"""
Phusion Passenger WSGI Entry Point
Für Netcup Webhosting 4000 NUE Deployment

WICHTIG: Pfade müssen an deine Server-Konfiguration angepasst werden!
"""

import sys
import os

# ====================================
# Virtual Environment aktivieren
# ====================================
# ANPASSEN: Pfad zu deinem venv/bin/python3
# Option 1: Standard venv
INTERP = os.path.expanduser("~/www/ai-recruiting-demo/venv/bin/python3")

# Option 2: Mit uv (.venv)
# INTERP = os.path.expanduser("~/www/ai-recruiting-demo/.venv/bin/python3")

# Option 3: Relativer Pfad (falls Passenger im Projekt-Verzeichnis startet)
# INTERP = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'python3')

if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# ====================================
# Projekt-Pfad hinzufügen
# ====================================
sys.path.insert(0, os.path.dirname(__file__))

# ====================================
# Flask App importieren
# ====================================
from app import app as application

# ====================================
# Production-Mode sicherstellen
# ====================================
if __name__ == "__main__":
    application.run()

