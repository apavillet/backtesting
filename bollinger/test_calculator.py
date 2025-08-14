#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculateur de temps de test et optimiseur de planning.
Usage: python test_calculator.py [--level COARSE|FINE|FULL] [--symbols EURUSD GBPUSD]
"""

import argparse

TEST_LEVELS = {
    'COARSE': {
        'ATR_MULTIPLIERS': [1.0, 1.5, 2.0, 2.5, 3.0],
        'RR_VALUES': [2.0, 2.5, 3.0, 3.5, 4.0],
        'VOL_MULTIPLIERS': [0.8, 1.0, 1.2],
    },
    'FINE': {
        'ATR_MULTIPLIERS': [round(i * 0.2, 1) for i in range(5, 16)],
        'RR_VALUES': [round(i * 0.2, 1) for i in range(10, 21)],
        'VOL_MULTIPLIERS': [round(i * 0.1, 1) for i in range(8, 14)],
    },
    'FULL': {
        'ATR_MULTIPLIERS': [round(i * 0.1, 1) for i in range(10, 31)],
        'RR_VALUES': [round(i * 0.1, 1) for i in range(20, 51)],
        'VOL_MULTIPLIERS': [round(i * 0.1, 1) for i in range(8, 14)],
    }
}

ALL_SYMBOLS = ['EURUSD', 'EURAUD', 'USDCAD', 'NZDJPY', 'GBPUSD', 'USDJPY', 'EURJPY', 'GBPJPY', 'AUDUSD', 'AUDJPY', 'AUDCAD', 'USDCHF', 'EURNZD', 'EURGBP', 'NZDUSD', 'EURCAD', 'EURCHF', 'GBPCAD', 'AUDNZD', 'CADCHF', 'GBPCHF', 'CADJPY', 'GBPAUD', 'GBPNZD', 'NZDCAD']

def format_time(seconds):
    """Formate le temps en format lisible."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.0f}min"
    elif seconds < 86400:
        return f"{seconds/3600:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f} jours"

def calculate_test_time(level, symbols=None, avg_time_per_test=4.0):
    """Calcule le temps de test pour un niveau et des symboles donnés."""
    if symbols is None:
        symbols = ALL_SYMBOLS
    
    config = TEST_LEVELS[level]
    combos_per_symbol = len(config['ATR_MULTIPLIERS']) * len(config['RR_VALUES']) * len(config['VOL_MULTIPLIERS'])
    total_tests = combos_per_symbol * len(symbols)
    total_time = total_tests * avg_time_per_test
    
    return {
        'level': level,
        'symbols': len(symbols),
        'combos_per_symbol': combos_per_symbol,
        'total_tests': total_tests,
        'total_time_seconds': total_time,
        'total_time_formatted': format_time(total_time)
    }

def suggest_optimization(level, symbols):
    """Suggère des optimisations basées sur le niveau et les symboles."""
    suggestions = []
    
    result = calculate_test_time(level, symbols)
    
    if result['total_time_seconds'] > 86400:  # Plus d'un jour
        suggestions.append("⚠️  Test très long (>24h). Considérez:")
        suggestions.append("   • Réduire le niveau (FULL → FINE → COARSE)")
        suggestions.append("   • Tester d'abord quelques symboles majeurs")
        suggestions.append("   • Utiliser --skip-complete pour reprendre")
    
    if level == 'FULL' and len(symbols) > 10:
        suggestions.append("💡 Pour FULL avec beaucoup de symboles:")
        suggestions.append("   • Commencez par FINE pour identifier les meilleurs ranges")
        suggestions.append("   • Puis FULL seulement sur les ranges prometteurs")
    
    if level == 'COARSE':
        suggestions.append("🚀 Mode COARSE actif:")
        suggestions.append("   • Idéal pour explorer rapidement")
        suggestions.append("   • Utilisez FINE sur les symboles prometteurs")
    
    # Suggestions de symboles par priorité
    major_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF']
    minor_pairs = ['EURJPY', 'GBPJPY', 'EURGBP', 'AUDCAD']
    
    if len(symbols) == len(ALL_SYMBOLS):
        suggestions.append("📊 Ordre de test recommandé:")
        suggestions.append(f"   1. Majeurs ({len(major_pairs)}): {', '.join(major_pairs[:3])}...")
        suggestions.append(f"   2. Mineurs ({len(minor_pairs)}): {', '.join(minor_pairs[:3])}...")
        suggestions.append("   3. Exotiques (restants)")
    
    return suggestions

def main():
    parser = argparse.ArgumentParser(description="Calculateur de temps de test")
    parser.add_argument('--level', choices=['COARSE', 'FINE', 'FULL'], default='FINE')
    parser.add_argument('--symbols', nargs='*', help='Symboles spécifiques (ex: EURUSD GBPUSD)')
    parser.add_argument('--all-levels', action='store_true', help='Afficher tous les niveaux')
    args = parser.parse_args()
    
    symbols = args.symbols if args.symbols else ALL_SYMBOLS
    
    print("🧮 CALCULATEUR DE TEMPS DE TEST")
    print("=" * 50)
    
    if args.all_levels:
        print(f"\n📊 Comparaison pour {len(symbols)} symbole(s):")
        if len(symbols) < len(ALL_SYMBOLS):
            print(f"   Symboles: {', '.join(symbols)}")
        
        for level in ['COARSE', 'FINE', 'FULL']:
            result = calculate_test_time(level, symbols)
            print(f"\n{level:>6}: {result['total_tests']:>6,} tests → {result['total_time_formatted']:>8}")
    else:
        result = calculate_test_time(args.level, symbols)
        
        print(f"\n📈 NIVEAU: {result['level']}")
        print(f"🎯 Symboles: {result['symbols']}")
        print(f"⚡ Combinaisons/symbole: {result['combos_per_symbol']:,}")
        print(f"🔢 Tests totaux: {result['total_tests']:,}")
        print(f"⏱️ Temps estimé: {result['total_time_formatted']}")
        
        # Suggestions d'optimisation
        suggestions = suggest_optimization(args.level, symbols)
        if suggestions:
            print(f"\n{suggestions[0]}")
            for suggestion in suggestions[1:]:
                print(suggestion)
    
    print(f"\n💡 COMMANDES RAPIDES:")
    print(f"   Test rapide majeurs: --level COARSE --symbols EURUSD GBPUSD USDJPY")
    print(f"   Test complet: --level FINE")
    print(f"   Analyse exhaustive: --level FULL")

if __name__ == "__main__":
    main()
