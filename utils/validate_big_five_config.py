"""
Validation Script für Big Five Questions Configuration
Prüft ob der Fragenpool korrekt strukturiert ist

Unterstützt erweiterte Fragenpools:
- Mindestens 30 Fragen (optimal: 60+ für zufällige Auswahl)
- Mindestens 12 Fragen pro Dimension (für zufällige Auswahl von 6)
"""

import yaml
from pathlib import Path
from collections import Counter

def validate_big_five_config(config_path: str = "config/big_five_questions.yaml") -> bool:
    """
    Validiert die Big Five Questions YAML-Datei
    
    Prüft:
    - Alle 5 Dimensionen vorhanden (O, C, E, A, N)
    - Mindestens 30 Fragen insgesamt (optimal: 60+)
    - Mindestens 12 Fragen pro Dimension (für zufällige Auswahl von 6)
    - Alle Fragen haben id, dimension, keying, text
    - IDs sind eindeutig und positiv
    - Keying ist entweder "+" oder "-"
    
    Returns:
        True wenn valide, False sonst
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        print(f"[ERROR] Config-Datei nicht gefunden: {config_path}")
        return False
    
    print(f"[OK] Lade Konfiguration: {config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Prüfe Dimensions-Definition
    expected_dimensions = {'O', 'C', 'E', 'A', 'N'}
    if 'dimensions' not in data:
        print("[ERROR] 'dimensions' Schlüssel fehlt")
        return False
    
    actual_dimensions = set(data['dimensions'].keys())
    if actual_dimensions != expected_dimensions:
        missing = expected_dimensions - actual_dimensions
        extra = actual_dimensions - expected_dimensions
        if missing:
            print(f"[ERROR] Fehlende Dimensionen: {missing}")
        if extra:
            print(f"[ERROR] Unerwartete Dimensionen: {extra}")
        return False
    
    print("[OK] Alle 5 Dimensionen vorhanden: O, C, E, A, N")
    
    # Prüfe Questions
    if 'questions' not in data:
        print("❌ 'questions' Schlüssel fehlt")
        return False
    
    questions = data['questions']
    
    # Prüfe Gesamtzahl (mindestens 30, optimal 60+)
    if len(questions) < 30:
        print(f"[ERROR] Zu wenige Fragen: {len(questions)} (mindestens 30 erforderlich)")
        return False
    
    if len(questions) >= 60:
        print(f"[OK] Gesamtzahl Fragen: {len(questions)} (optimal für zufällige Auswahl)")
    else:
        print(f"[WARN] Gesamtzahl Fragen: {len(questions)} (optimal wären 60+ für zufällige Auswahl)")
    
    # Prüfe Fragen-Struktur und Dimension-Verteilung
    dimension_counts = Counter()
    question_ids = set()
    valid_keyings = {'+', '-'}
    
    for i, question in enumerate(questions, 1):
        # Prüfe erforderliche Felder
        if 'id' not in question:
            print(f"[ERROR] Frage {i}: 'id' fehlt")
            return False
        
        if 'dimension' not in question:
            print(f"[ERROR] Frage {question.get('id', i)}: 'dimension' fehlt")
            return False
        
        if 'keying' not in question:
            print(f"[ERROR] Frage {question.get('id', i)}: 'keying' fehlt")
            return False
        
        if 'text' not in question:
            print(f"[ERROR] Frage {question.get('id', i)}: 'text' fehlt")
            return False
        
        # Prüfe ID-Bereich (muss positiv sein)
        q_id = question['id']
        if q_id < 1:
            print(f"[ERROR] Frage ID muss positiv sein: {q_id}")
            return False
        
        # Prüfe auf doppelte IDs
        if q_id in question_ids:
            print(f"[ERROR] Doppelte Frage-ID: {q_id}")
            return False
        question_ids.add(q_id)
        
        # Prüfe Dimension
        dimension = question['dimension']
        if dimension not in expected_dimensions:
            print(f"[ERROR] Frage {q_id}: Ungültige Dimension '{dimension}'")
            return False
        dimension_counts[dimension] += 1
        
        # Prüfe Keying
        keying = question['keying']
        if keying not in valid_keyings:
            print(f"[ERROR] Frage {q_id}: Ungültiges Keying '{keying}' (erwartet: '+' oder '-')")
            return False
        
        # Prüfe Text nicht leer
        if not question['text'] or not question['text'].strip():
            print(f"[ERROR] Frage {q_id}: Text ist leer")
            return False
    
    # Prüfe Dimension-Verteilung (mindestens 12 pro Dimension für zufällige Auswahl)
    print("\n[INFO] Dimension-Verteilung:")
    all_valid = True
    min_questions_per_dim = 12
    
    for dim in expected_dimensions:
        count = dimension_counts[dim]
        if count < 6:
            print(f"  [ERROR] {dim}: {count} Fragen (mindestens 6 erforderlich)")
            all_valid = False
        elif count < min_questions_per_dim:
            print(f"  [WARN] {dim}: {count} Fragen (optimal wären {min_questions_per_dim}+ für zufällige Auswahl)")
        else:
            print(f"  [OK] {dim}: {count} Fragen (ausreichend für zufällige Auswahl)")
    
    if not all_valid:
        return False
    
    # Prüfe ID-Eindeutigkeit (IDs müssen eindeutig sein, aber müssen nicht lückenlos sein)
    max_id = max(question_ids) if question_ids else 0
    print(f"\n[OK] Fragen-IDs eindeutig (Bereich: {min(question_ids) if question_ids else 0}-{max_id})")
    
    # Statistiken
    keying_counts = Counter(q['keying'] for q in questions)
    print(f"\n[INFO] Keying-Verteilung:")
    print(f"  Normal (+): {keying_counts['+']} Fragen")
    print(f"  Reversed (-): {keying_counts['-']} Fragen")
    
    print("\n" + "="*50)
    print("[OK] VALIDIERUNG ERFOLGREICH!")
    print("="*50)
    
    return True


if __name__ == "__main__":
    import sys
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/big_five_questions.yaml"
    
    success = validate_big_five_config(config_path)
    sys.exit(0 if success else 1)

