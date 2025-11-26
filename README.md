# 🤖 AI Recruiting Demo

**Automatische CV-Analyse mit KI** – Flask-basierte Web-App für strukturiertes Job Matching und Persönlichkeitsbewertung mit OpenAI GPT-4o-mini.

## 📋 Projekt-Übersicht

Dieses Projekt ist eine **Machbarkeitsstudie** und demonstriert:
- PDF-Upload und Textextraktion
- KI-gestützte CV-Analyse mit GPT-4o-mini
- Job Requirements Matching (40 Skills, gewichtet)
- Big Five Persönlichkeitstest (IPIP-30) mit job-spezifischem Profil
- Strukturierte Bewertung und Empfehlungen
- Browser-basierte Ergebnis-Anzeige mit 4 Tabs

## Warniung!!!
Das ist eine Machbarkeitstudie und NICHT für den aktiven Gebrauch gedacht.
Alle Daten werden von OpenAI analysiert und somit an das Unternehmen übergeben.
Es sollte unbedingt mit den Demo-Lebensläufen gearbeitet werden!

## 🚀 Quick Start

### 1. Environment Setup (mit uv)

```bash
# Python Virtual Environment erstellen
uv venv

# Aktivieren
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Dependencies installieren
uv pip install -r requirements.txt
```

### 2. Konfiguration

```bash
# .env Datei erstellen
cp .env.example .env

# OpenAI API Key eintragen
# Editiere .env und füge deinen API Key ein
```

### 3. Anwendung starten

```bash
python app.py
```

Die Anwendung läuft auf: `http://localhost:5000`

## 📁 Projekt-Struktur

```
AI-Recruiting-Demo/
├── app.py                  # Flask Application
├── requirements.txt        # Python Dependencies
├── .env.example           # Config Template
├── .gitignore            # Git Ignore Rules
├── README.md             # Diese Datei
├── templates/            # HTML Templates
│   └── index.html
├── static/              # CSS, JS
│   ├── css/
│   │   └── style.css
│   └── js/
├── uploads/             # Temporäre PDF-Uploads (auto-delete)
├── config/             # Konfigurationsdateien
│   ├── job_requirements.yaml    # Job-Anforderungen + Persönlichkeitsprofile
│   └── big_five_questions.yaml  # IPIP-30 Fragen (60 Fragen Pool)
├── utils/              # Utility-Module
│   ├── big_five_scoring.py      # Big Five Scoring Algorithmus
│   └── job_requirements.py      # Job Requirements Loader
└── docs/              # Projekt-Dokumentation
```

## Projekt Bilder

![AI-Recruting-DEMO](Bilder/00-AI-Recruting.jpg)

**Upload & Auswertung**
- Job Matching Score 
- Gesamtbewertung (CV + Persönlichkeit) falls Persönlichkeits-Test absolviert
- Anforderungen-Abgleich
    - MUST-HAVE (60% Gewichtung)
    - SHOULD-HAVE (30% Gewichtung)
    - NICE-TO-HAVE (10% Gewichtung)
- Gap Analysis
- Persönliche Informationen
- Berufserfahrung
- Ausbildung
- Fähigkeiten
- INFO - Analyse-Details

![Analyse-Ergebnisse](Bilder/01-Auswertung.jpg)

**Stellenausschreibung**
- MUST-HAVE ANFORDERUNGEN
- SHOULD-HAVE ANFORDERUNGEN
- NICE-TO-HAVE ANFORDERUNGEN

![Stellenausschreibung](Bilder/02-Stellenausschreibung.jpg)

**Persönlichkeitstest**
- 30 Fragen
- Optional

![Big Five Persönlichkeitstest](Bilder/03-Big-Five-Profil.jpg)

## 🛠️ Tech Stack

- **Backend**: Flask 3.0
- **PDF Processing**: pdfplumber 0.11
- **AI/LLM**: OpenAI API (GPT-4o-mini)
- **Environment**: Python 3.11+, uv


## 🚀 Deployment

Das Projekt kann auf **Netcup Webhosting 4000 NUE** deployt werden:
- ✅ Python 3.11+ Support
- ✅ Flask WSGI via Phusion Passenger
- ✅ SSH-Zugriff für Setup
- ✅ 512 MB Memory Limit pro Prozess


**Schnellstart**:
1. `passenger_wsgi.py` und `.htaccess.example` anpassen
2. Projekt auf Server hochladen
3. Virtual Environment erstellen
4. Dependencies installieren
5. `.env` auf Server erstellen

## 🔒 Sicherheit

- API Keys werden via `.env` verwaltet (nicht im Git!)
- PDFs werden nach Analyse automatisch gelöscht
- Keine persistente Speicherung von Bewerberdaten
- Production-ready mit Security Headers

## 📝 License

Demo-Projekt - Alle Rechte vorbehalten.

## 👤 Autor

Sebastian Gasior
AI Recruiting Demo Feasibility Study

---




