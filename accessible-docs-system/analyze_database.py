#!/usr/bin/env python3
"""
Analisi dettagliata del database formule
"""

from core.formula_database import FormulaDatabase


def main():
    db = FormulaDatabase('formulas.db')
    
    print("=" * 80)
    print("ANALISI COMPLETA DATABASE FORMULE")
    print("=" * 80)
    
    # Statistiche generali
    stats = db.get_statistics()
    print(f"\n{'📊 STATISTICHE GENERALI':^80}")
    print("-" * 80)
    print(f"  Totale formule:      {stats['total_formulas']:4d}")
    print(f"  Formule verificate:  {stats['verified']:4d}")
    
    # Per categoria
    print(f"\n{'📚 DISTRIBUZIONE PER CATEGORIA':^80}")
    print("-" * 80)
    for cat, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
        bar = '█' * (count * 3)
        print(f"  {cat:20s} [{count:3d}] {bar}")
    
    # Per difficoltà
    print(f"\n{'🎯 DISTRIBUZIONE PER DIFFICOLTÀ':^80}")
    print("-" * 80)
    for diff, count in sorted(stats['by_difficulty'].items()):
        stars = '⭐' * diff
        bar = '█' * (count * 2)
        print(f"  Livello {diff} {stars:15s} [{count:3d}] {bar}")
    
    # Tutti i tag
    all_tags = db.get_all_tags()
    print(f"\n{'🏷️  TUTTI I TAG ({len(all_tags)} totali)':^80}")
    print("-" * 80)
    # Raggruppa in colonne
    tags_per_row = 5
    for i in range(0, len(all_tags), tags_per_row):
        row_tags = all_tags[i:i+tags_per_row]
        print("  " + " | ".join(f"{tag:15s}" for tag in row_tags))
    
    # Formule per sottocategoria
    print(f"\n{'📑 FORMULE PER CATEGORIA E SOTTOCATEGORIA':^80}")
    print("=" * 80)
    
    for category in sorted(stats['by_category'].keys()):
        formulas = db.search_formulas(category=category, limit=1000)
        
        # Raggruppa per sottocategoria
        subcats = {}
        for f in formulas:
            subcat = f['subcategory'] or 'misc'
            if subcat not in subcats:
                subcats[subcat] = []
            subcats[subcat].append(f)
        
        print(f"\n🔹 {category.upper()} ({len(formulas)} formule)")
        print("-" * 80)
        
        for subcat, subcat_formulas in sorted(subcats.items()):
            print(f"\n  └─ {subcat} ({len(subcat_formulas)} formule):")
            
            for f in subcat_formulas[:5]:  # Primi 5
                stars = '⭐' * f['difficulty']
                print(f"     • {f['name']:35s} {stars:10s}")
                print(f"       {f['latex']}")
            
            if len(subcat_formulas) > 5:
                print(f"     ... e altre {len(subcat_formulas) - 5} formule")
    
    # Esempi di ricerche
    print(f"\n{'🔍 ESEMPI DI RICERCHE':^80}")
    print("=" * 80)
    
    searches = [
        ("Formule con 'frazione'", {"query": "frazione"}),
        ("Formule di calcolo", {"category": "calculus"}),
        ("Formule basilari (diff=1)", {"difficulty": 1, "limit": 5}),
        ("Formule con tag 'integrale'", {"tags": ["integrale"]}),
        ("Formule greche", {"query": "greco"}),
    ]
    
    for title, params in searches:
        results = db.search_formulas(**params)
        print(f"\n🔎 {title}: {len(results)} risultati")
        for f in results[:3]:
            print(f"   • {f['name']:40s} [{f['category']}]")
            print(f"     {f['latex']}")
        if len(results) > 3:
            print(f"   ... e altre {len(results) - 3} formule")
    
    db.close()
    
    print("\n" + "=" * 80)
    print("✅ Analisi completata")
    print("=" * 80)


if __name__ == "__main__":
    main()
