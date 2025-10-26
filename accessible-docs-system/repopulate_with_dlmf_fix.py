#!/usr/bin/env python3
"""
Script per testare FIX DLMF e ripopolare database
Usa importer DLMF fixato per aggiungere formule al database esistente
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("TEST E RIPOPOLAMENTO DATABASE CON DLMF FIXATO")
print("=" * 70)

# Step 1: Test importer fixato
print("\n[STEP 1/3] Test importer DLMF fixato...")
print("-" * 70)

from core.archive_importers.dlmf_importer import DLMFImporter

importer = DLMFImporter(cache_dir="dlmf_cache")

# Test su capitolo 5 (Gamma - di solito ha tante formule)
print("\nTest capitolo 5 (Gamma Function)...")
test_formulas = importer.import_chapter('5')

if len(test_formulas) == 0:
    print("❌ FALLITO: Nessuna formula estratta")
    print("\n⚠️ DLMF potrebbe aver cambiato struttura HTML recentemente.")
    print("⚠️ Il tuo database ha già 657 formule da Wikipedia - è sufficiente!")
    print("\nOpzioni:")
    print("  1. Usa le 657 formule Wikipedia (già funzionanti)")
    print("  2. Aspetta che DLMF ripristini l'accesso")
    print("  3. Importa da altre fonti (arXiv)")
    sys.exit(1)
else:
    print(f"✅ SUCCESSO: Estratte {len(test_formulas)} formule!")
    print("\nPrime 3 formule:")
    for i, f in enumerate(test_formulas[:3], 1):
        print(f"  {i}. {f['latex'][:70]}...")

# Step 2: Chiedi conferma per ripopolare
print("\n[STEP 2/3] Ripopolamento database")
print("-" * 70)

from core.formula_database import FormulaDatabase

db = FormulaDatabase("formulas.db")
stats = db.get_statistics()

print(f"\nDatabase attuale:")
print(f"  Totale formule: {stats['total_formulas']}")
print(f"  Da Wikipedia: {stats['total_formulas']} (circa)")

print(f"\nAggiungendo formule DLMF:")
print(f"  Capitoli da importare: 5, 6, 7, 10, 15, 25")
print(f"  Formule attese: ~200-400 addizionali")

risposta = input("\nVuoi procedere? (si/no): ")

if risposta.lower() not in ['si', 'sì', 's', 'yes', 'y']:
    print("\nOperazione annullata.")
    db.close()
    sys.exit(0)

# Step 3: Importa formule
print("\n[STEP 3/3] Importazione formule DLMF...")
print("-" * 70)

chapters = ['5', '6', '7', '10', '15', '25']
total_imported = 0

for chapter in chapters:
    print(f"\nImportando capitolo {chapter}...", end=' ')
    try:
        formulas = importer.import_chapter(chapter)
        count = importer.import_to_database(formulas, db)
        total_imported += count
        print(f"✅ {count} nuove formule")
    except Exception as e:
        print(f"⚠️ Errore: {e}")

# Statistiche finali
print("\n" + "=" * 70)
print("COMPLETATO")
print("=" * 70)

stats = db.get_statistics()
print(f"\nDatabase aggiornato:")
print(f"  Totale formule: {stats['total_formulas']}")
print(f"  Nuove formule DLMF: {total_imported}")
print(f"  Formule verificate: {stats['verified_formulas']}")

print("\n📊 Distribuzione per categoria:")
for cat, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")

db.close()

print("\n✅ Database pronto!")
print("\nProssimi passi:")
print("  1. Testa integrazione: python3 test_integration.py")
print("  2. Usa nel Jump Manager")
print()
