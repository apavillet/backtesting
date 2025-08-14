#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de démarrage interactif pour choisir le niveau de test optimal.
Usage: python quick_start.py
"""

import os
import sys

TEST_LEVELS = {
    'COARSE': {
        'combos': 75,
        'time_min': 5,
        'description': 'Test rapide pour exploration'
    },
    'FINE': {
        'combos': 726, 
        'time_min': 45,
        'description': 'Test recommandé (compromis vitesse/précision)'
    },
    'FULL': {
        'combos': 3906,
        'time_min': 240,
        'description': 'Test exhaustif pour analyse finale'
    }
}

SYMBOL_GROUPS = {
    'majors': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF'],
    'minors': ['EURJPY', 'GBPJPY', 'EURGBP', 'AUDCAD', 'EURCAD', 'EURCHF'],
    'exotics': ['NZDJPY', 'CADCHF', 'GBPNZD', 'AUDNZD', 'GBPCAD', 'NZDUSD']
}

def print_banner():
    print("🚀 BACKTESTING OPTIMIZER - DÉMARRAGE RAPIDE")
    print("=" * 60)
    print("Ce script vous aide à choisir les paramètres optimaux.")
    print("")

def choose_level():
    print("📊 CHOISISSEZ VOTRE NIVEAU DE TEST:")
    print("")
    
    for i, (level, info) in enumerate(TEST_LEVELS.items(), 1):
        time_str = f"{info['time_min']}min" if info['time_min'] < 60 else f"{info['time_min']//60}h"
        print(f"{i}. {level:>6} - {info['combos']:>4} combos (~{time_str:>4}) - {info['description']}")
    
    print("")
    while True:
        try:
            choice = input("Votre choix (1-3) : ").strip()
            if choice in ['1', '2', '3']:
                levels = list(TEST_LEVELS.keys())
                return levels[int(choice) - 1]
            print("❌ Choix invalide. Entrez 1, 2 ou 3.")
        except KeyboardInterrupt:
            print("\n❌ Arrêt demandé.")
            sys.exit(0)

def choose_symbols():
    print("\n🎯 CHOISISSEZ VOS SYMBOLES:")
    print("")
    print("1. TOUS LES SYMBOLES (25 paires) - Test complet")
    print("2. MAJEURS SEULEMENT (6 paires) - Plus rapide")  
    print("3. SÉLECTION PERSONNALISÉE - Choisir manuellement")
    print("")
    
    while True:
        try:
            choice = input("Votre choix (1-3) : ").strip()
            
            if choice == '1':
                return None  # Tous les symboles
            elif choice == '2':
                return SYMBOL_GROUPS['majors']
            elif choice == '3':
                return choose_custom_symbols()
            else:
                print("❌ Choix invalide. Entrez 1, 2 ou 3.")
        except KeyboardInterrupt:
            print("\n❌ Arrêt demandé.")
            sys.exit(0)

def choose_custom_symbols():
    print("\n📋 SYMBOLES DISPONIBLES:")
    all_symbols = SYMBOL_GROUPS['majors'] + SYMBOL_GROUPS['minors'] + SYMBOL_GROUPS['exotics']
    
    for i, symbol in enumerate(all_symbols, 1):
        group = 'majors' if symbol in SYMBOL_GROUPS['majors'] else 'minors' if symbol in SYMBOL_GROUPS['minors'] else 'exotics'
        print(f"{i:2d}. {symbol} ({group})")
    
    print(f"\n💡 Entrez les numéros séparés par des espaces (ex: 1 2 5)")
    print(f"💡 Ou tapez 'majors', 'minors', 'exotics' pour un groupe")
    print("")
    
    while True:
        try:
            selection = input("Votre sélection : ").strip()
            
            if selection.lower() in SYMBOL_GROUPS:
                return SYMBOL_GROUPS[selection.lower()]
            
            # Parse numbers
            try:
                numbers = [int(x) for x in selection.split()]
                if all(1 <= n <= len(all_symbols) for n in numbers):
                    return [all_symbols[n-1] for n in numbers]
                else:
                    print(f"❌ Numéros invalides. Utilisez 1-{len(all_symbols)}")
            except ValueError:
                print("❌ Format invalide. Utilisez des numéros ou 'majors/minors/exotics'")
                
        except KeyboardInterrupt:
            print("\n❌ Arrêt demandé.")
            sys.exit(0)

def calculate_time(level, symbols):
    """Calcule le temps estimé."""
    combos = TEST_LEVELS[level]['combos']
    symbol_count = len(symbols) if symbols else 25
    total_tests = combos * symbol_count
    minutes = total_tests * 4 / 60  # 4 sec par test
    return minutes, total_tests

def generate_command(level, symbols, skip_complete):
    """Génère la commande à exécuter."""
    cmd = f"python3 test-selenium-single-thread.py --level {level}"
    
    if symbols:
        cmd += f" --symbols {' '.join(symbols)}"
    
    if skip_complete:
        cmd += " --skip-complete"
    
    return cmd

def main():
    print_banner()
    
    # Choisir le niveau
    level = choose_level()
    
    # Choisir les symboles
    symbols = choose_symbols()
    
    # Option de reprendre un test
    if os.path.exists("tradingview_backtest_results.xlsx"):
        print(f"\n🔄 Un fichier de résultats existe déjà.")
        print(f"💡 Voulez-vous ignorer les combinaisons déjà testées?")
        skip_choice = input("Reprendre où vous vous êtes arrêté? (o/N) : ").strip().lower()
        skip_complete = skip_choice in ['o', 'oui', 'y', 'yes']
    else:
        skip_complete = False
    
    # Calcul des estimations
    minutes, total_tests = calculate_time(level, symbols)
    symbol_count = len(symbols) if symbols else 25
    
    # Résumé
    print(f"\n📊 RÉSUMÉ DE VOTRE CONFIGURATION:")
    print(f"📈 Niveau: {level} ({TEST_LEVELS[level]['combos']} combos/symbole)")
    print(f"🎯 Symboles: {symbol_count} paire(s)")
    if symbols and len(symbols) <= 6:
        print(f"   {', '.join(symbols)}")
    print(f"🔢 Tests totaux: {total_tests:,}")
    
    if minutes < 60:
        print(f"⏱️ Temps estimé: ~{minutes:.0f} minutes")
    else:
        print(f"⏱️ Temps estimé: ~{minutes/60:.1f} heures")
    
    if skip_complete:
        print(f"🔄 Reprise activée (ignore les tests déjà faits)")
    
    # Génération de la commande
    command = generate_command(level, symbols, skip_complete)
    
    print(f"\n🚀 COMMANDE À EXÉCUTER:")
    print(f"   {command}")
    print("")
    
    # Confirmation et lancement
    print(f"✅ Configuration confirmée?")
    confirm = input("Lancer le test maintenant? (O/n) : ").strip().lower()
    
    if confirm in ['', 'o', 'oui', 'y', 'yes']:
        print(f"\n🎯 Lancement du test...")
        print(f"💡 Assurez-vous que Chrome est ouvert avec --remote-debugging-port=9222")
        print(f"💡 Et que vous êtes connecté à TradingView")
        print("")
        
        # Exécuter la commande
        os.system(command)
    else:
        print(f"\n📋 Commande prête à copier:")
        print(f"   {command}")
        print(f"\n💡 Exécutez cette commande quand vous serez prêt!")

if __name__ == "__main__":
    main()
