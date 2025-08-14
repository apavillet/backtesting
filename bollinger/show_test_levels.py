#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'aide pour afficher les niveaux de test disponibles.
Usage: python show_test_levels.py
"""

TEST_LEVELS = {
    'COARSE': {
        'ATR_MULTIPLIERS': [1.0, 1.5, 2.0, 2.5, 3.0],  # 5 valeurs
        'RR_VALUES': [2.0, 2.5, 3.0, 3.5, 4.0],        # 5 valeurs  
        'VOL_MULTIPLIERS': [0.8, 1.0, 1.2],            # 3 valeurs
        'description': 'Test rapide avec 75 combinaisons par symbole'
    },
    'FINE': {
        'ATR_MULTIPLIERS': [round(i * 0.2, 1) for i in range(5, 16)],  # 1.0 à 3.0 par 0.2 = 11 valeurs
        'RR_VALUES': [round(i * 0.2, 1) for i in range(10, 21)],       # 2.0 à 4.0 par 0.2 = 11 valeurs
        'VOL_MULTIPLIERS': [round(i * 0.1, 1) for i in range(8, 14)],  # 0.8 à 1.3 par 0.1 = 6 valeurs
        'description': 'Test intermédiaire avec 726 combinaisons par symbole'
    },
    'FULL': {
        'ATR_MULTIPLIERS': [round(i * 0.1, 1) for i in range(10, 31)],  # 1.0 à 3.0 par 0.1 = 21 valeurs
        'RR_VALUES': [round(i * 0.1, 1) for i in range(20, 51)],        # 2.0 à 5.0 par 0.1 = 31 valeurs
        'VOL_MULTIPLIERS': [round(i * 0.1, 1) for i in range(8, 14)],   # 0.8 à 1.3 par 0.1 = 6 valeurs
        'description': 'Test complet avec 3906 combinaisons par symbole'
    }
}

SYMBOL_LIST = ['EURUSD', 'EURAUD', 'USDCAD', 'NZDJPY', 'GBPUSD', 'USDJPY', 'EURJPY', 'GBPJPY', 'AUDUSD', 'AUDJPY', 'AUDCAD', 'USDCHF', 'EURNZD', 'EURGBP', 'NZDUSD', 'EURCAD', 'EURCHF', 'GBPCAD', 'AUDNZD', 'CADCHF', 'GBPCHF', 'CADJPY', 'GBPAUD', 'GBPNZD', 'NZDCAD']

def main():
    print("🚀 NIVEAUX DE TEST DISPONIBLES")
    print("=" * 60)
    
    for level_name, config in TEST_LEVELS.items():
        total_combos = len(config['ATR_MULTIPLIERS']) * len(config['RR_VALUES']) * len(config['VOL_MULTIPLIERS'])
        total_tests = total_combos * len(SYMBOL_LIST)
        
        print(f"\n📊 {level_name}")
        print("-" * 40)
        print(f"📝 {config['description']}")
        print(f"🔢 ATR: {len(config['ATR_MULTIPLIERS'])} valeurs ({min(config['ATR_MULTIPLIERS']):.1f} → {max(config['ATR_MULTIPLIERS']):.1f})")
        print(f"🔢 RR:  {len(config['RR_VALUES'])} valeurs ({min(config['RR_VALUES']):.1f} → {max(config['RR_VALUES']):.1f})")
        print(f"🔢 Vol: {len(config['VOL_MULTIPLIERS'])} valeurs ({min(config['VOL_MULTIPLIERS']):.1f} → {max(config['VOL_MULTIPLIERS']):.1f})")
        print(f"⚡ Combinaisons par symbole: {total_combos:,}")
        print(f"🌍 Tests totaux ({len(SYMBOL_LIST)} symboles): {total_tests:,}")
        
        # Estimation du temps
        avg_time_per_test = 4.0
        estimated_seconds = total_tests * avg_time_per_test
        estimated_hours = estimated_seconds / 3600
        estimated_days = estimated_hours / 24
        
        if estimated_hours < 1:
            print(f"⏱️ Temps estimé: ~{estimated_seconds/60:.0f} minutes")
        elif estimated_hours < 24:
            print(f"⏱️ Temps estimé: ~{estimated_hours:.1f}h")
        else:
            print(f"⏱️ Temps estimé: ~{estimated_days:.1f} jours")
        
        # Détail des valeurs pour COARSE
        if level_name == 'COARSE':
            print(f"   ATR: {config['ATR_MULTIPLIERS']}")
            print(f"   RR:  {config['RR_VALUES']}")
            print(f"   Vol: {config['VOL_MULTIPLIERS']}")
    
    print("\n" + "=" * 60)
    print("💡 UTILISATION:")
    print("   python3 test-selenium-single-thread.py --level COARSE")
    print("   python3 test-selenium-single-thread.py --level FINE")
    print("   python3 test-selenium-single-thread.py --level FULL")
    print("\n🔧 Options supplémentaires:")
    print("   --skip-complete  : Ignorer les symboles déjà testés complètement")
    print("\n📈 RECOMMANDATIONS:")
    print("   🟢 COARSE : Pour tester rapidement de nouveaux paramètres")
    print("   🟡 FINE   : Bon compromis vitesse/précision (recommandé)")
    print("   🔴 FULL   : Analyse exhaustive pour les résultats finaux")

if __name__ == "__main__":
    main()
