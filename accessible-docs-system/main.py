#!/usr/bin/env python3
"""
Accessible Docs System - Entry Point

Sistema per rendere accessibili documenti scientifici a persone non vedenti.
"""
import sys
from pathlib import Path

# Aggiungi directory root al path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from ui.main_window import main

if __name__ == "__main__":
    print("=" * 60)
    print("Accessible Docs System")
    print("Sistema di accessibilità per documenti scientifici")
    print("=" * 60)
    print()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nUscita...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERRORE FATALE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
