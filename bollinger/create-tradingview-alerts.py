# -*- coding: utf-8 -*-

import time
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import argparse, traceback

# === CONFIG ===
TRADINGVIEW_BASE_URL = "https://www.tradingview.com/chart/0RKjg68o/"
EXCEL_FILE = "tradingview_backtest_results.xlsx"
BEST_SHEET = "Best_Per_Symbol"

# Paramètres par défaut si pas trouvés dans l'Excel
DEFAULT_ATR = 1.2
DEFAULT_RR = 2.7
DEFAULT_VOL = 0.8

def load_best_parameters():
    """Charge les meilleurs paramètres depuis l'Excel d'analyse."""
    if not os.path.exists(EXCEL_FILE):
        print(f"❌ Fichier {EXCEL_FILE} non trouvé. Utilisation des paramètres par défaut.")
        return {}
    
    try:
        df_best = pd.read_excel(EXCEL_FILE, sheet_name=BEST_SHEET, engine='openpyxl')
        
        if df_best.empty:
            print(f"❌ Feuille {BEST_SHEET} vide. Utilisation des paramètres par défaut.")
            return {}
        
        # Convertir en dictionnaire {Symbol: {ATR, RR, Vol}}
        best_params = {}
        for _, row in df_best.iterrows():
            symbol = row.get('Symbol')
            if symbol:
                best_params[symbol] = {
                    'ATR': row.get('Best ATR Multiplier', DEFAULT_ATR),
                    'RR': row.get('Best RR', DEFAULT_RR), 
                    'Vol': row.get('Best Vol Multiplier', DEFAULT_VOL)
                }
        
        print(f"✅ Chargé {len(best_params)} symboles avec paramètres optimaux:")
        for symbol, params in best_params.items():
            print(f"  {symbol}: ATR={params['ATR']}, RR={params['RR']}, Vol={params['Vol']}")
        
        return best_params
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement de {EXCEL_FILE}: {e}")
        return {}

def setup_driver():
    """Configure et initialise le driver Chrome avec remote debugging."""
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.debugger_address = "127.0.0.1:9222"
    
    try:
        driver = webdriver.Chrome(options=options)
        print("✅ Driver Chrome connecté avec succès")
        return driver
    except Exception as e:
        print(f"❌ Impossible de connecter le driver Chrome: {e}")
        print("💡 Assurez-vous que Chrome est lancé avec --remote-debugging-port=9222")
        return None

def set_strategy_parameters(driver, atr, rr, vol_mult):
    """Configure les paramètres de la stratégie."""
    print(f"🔧 Configuration ATR={atr}, RR={rr}, Vol={vol_mult}")
    
    try:
        # Ouvrir les paramètres avec Cmd+P
        actions = ActionChains(driver)
        actions.key_down(Keys.COMMAND).send_keys('p').key_up(Keys.COMMAND).perform()
        time.sleep(2)
        
        # ATR Multiplier
        atr_input = driver.find_element(
            By.XPATH,
            "//div[contains(text(),'ATR Stop Multiplier') or contains(text(),'Multiplicateur ATR')]/parent::div/following-sibling::div//input"
        )
        atr_input.click()
        actions.key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND).perform()
        atr_input.send_keys(str(atr))
        
        # Risk/Reward Ratio
        rr_input = driver.find_element(
            By.XPATH,
            "//div[contains(text(),'Base Risk/Reward Ratio') or contains(text(),'Ratio Risque/Rendement de base')]/parent::div/following-sibling::div//input"
        )
        rr_input.click()
        actions.key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND).perform()
        rr_input.send_keys(str(rr))
        
        # Volatility Multiplier
        vol_input = driver.find_element(
            By.XPATH,
            "//div[contains(text(),'Dynamic: Min Volatility Multiplier') or contains(text(),'Multiplicateur minimal de volatilité dynamique')]/parent::div/following-sibling::div//input"
        )
        vol_input.click()
        actions.key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND).perform()
        vol_input.send_keys(str(vol_mult))
        
        # Appliquer les changements
        actions.send_keys(Keys.TAB).perform()
        time.sleep(1)
        
        # Attendre que la snackbar disparaisse
        try:
            WebDriverWait(driver, 3).until_not(
                EC.presence_of_element_located((By.CLASS_NAME, "snackbarLayer-_MKqWk5g"))
            )
        except:
            pass
        
        print("✅ Paramètres configurés avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la configuration des paramètres: {e}")
        return False

def delete_existing_alerts(driver):
    """Supprime toutes les alertes existantes créées par ce script."""
    try:
        print("🧹 Suppression des alertes existantes...")
        
        # Aller à la page des alertes
        driver.get("https://www.tradingview.com/u/alerts/")
        time.sleep(3)
        
        # Attendre que la page se charge
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'alerts')]"))
        )
        
        deleted_count = 0
        max_attempts = 50  # Limite pour éviter les boucles infinies
        
        for attempt in range(max_attempts):
            try:
                # Chercher les alertes créées par notre script (contenant "Optimal Strategy Alert")
                alert_rows = driver.find_elements(
                    By.XPATH, 
                    "//tr[.//td[contains(text(), 'Optimal Strategy Alert')]]"
                )
                
                if not alert_rows:
                    # Essayer un autre sélecteur si le premier ne fonctionne pas
                    alert_rows = driver.find_elements(
                        By.XPATH, 
                        "//div[contains(text(), 'Optimal Strategy Alert')]/ancestor::tr"
                    )
                
                if not alert_rows:
                    # Sélecteur alternatif pour les alertes en général
                    alert_rows = driver.find_elements(
                        By.XPATH, 
                        "//div[contains(@data-name, 'alert-item') and .//text()[contains(., 'Optimal Strategy Alert')]]"
                    )
                
                if not alert_rows:
                    print(f"✅ Aucune alerte de script trouvée (tentative {attempt + 1})")
                    break
                
                # Supprimer la première alerte trouvée
                alert_row = alert_rows[0]
                
                # Chercher le bouton de suppression (icône poubelle ou menu)
                delete_selectors = [
                    ".//div[@data-name='alert-delete-button']",
                ]
                
                delete_button = None
                for selector in delete_selectors:
                    try:
                        delete_button = alert_row.find_element(By.XPATH, '..').find_element(By.XPATH, selector)
                        break
                    except:
                        continue
                
                if delete_button:
                    # Faire défiler vers l'élément si nécessaire
                    driver.execute_script("arguments[0].scrollIntoView(true);", delete_button)
                    time.sleep(0.5)
                    
                    # Cliquer sur le bouton de suppression
                    driver.execute_script("arguments[0].click();", delete_button)
                    time.sleep(1)
                    
                    # Confirmer la suppression si une boîte de dialogue apparaît
                    try:
                        confirm_selectors = [
                            "//button[contains(text(), 'Delete') or contains(text(), 'Supprimer')]",
                            "//button[contains(text(), 'Confirm') or contains(text(), 'Confirmer')]",
                            "//button[contains(text(), 'Yes') or contains(text(), 'Oui')]",
                            "//button[@name='yes']",
                            "//button[@data-name='confirm']"
                        ]
                        
                        for confirm_selector in confirm_selectors:
                            try:
                                confirm_button = WebDriverWait(driver, 2).until(
                                    EC.element_to_be_clickable((By.XPATH, confirm_selector))
                                )
                                confirm_button.click()
                                break
                            except:
                                continue
                    except:
                        pass  # Pas de confirmation nécessaire
                    
                    deleted_count += 1
                    print(f"🗑️ Alerte {deleted_count} supprimée")
                    time.sleep(1)  # Attendre que la suppression soit effective
                    
                else:
                    print("⚠️ Bouton de suppression non trouvé pour cette alerte")
                    # Essayer de cliquer droit pour ouvrir le menu contextuel
                    try:
                        actions = ActionChains(driver)
                        actions.context_click(alert_row).perform()
                        time.sleep(1)
                        
                        # Chercher l'option "Delete" dans le menu contextuel
                        context_delete = driver.find_element(
                            By.XPATH, 
                            "//div[contains(@class, 'context-menu')]//div[contains(text(), 'Delete') or contains(text(), 'Supprimer')]"
                        )
                        context_delete.click()
                        
                        deleted_count += 1
                        print(f"🗑️ Alerte {deleted_count} supprimée (menu contextuel)")
                        time.sleep(1)
                        
                    except:
                        print("⚠️ Impossible de supprimer cette alerte, passage à la suivante")
                        break
                        
            except Exception as e:
                print(f"⚠️ Erreur lors de la suppression d'alerte: {e}")
                print(traceback.print_exc())
                break
        
        print(f"✅ Suppression terminée: {deleted_count} alertes supprimées")
        return deleted_count
        
    except Exception as e:
        print(f"❌ Erreur lors de la suppression des alertes: {e}")
        return 0

def create_alert(driver, symbol, condition="Signal"):
    """Crée une alerte pour le symbole en utilisant la page d'alertes directe."""
    try:
        print(f"🚨 Création d'alerte pour {symbol}...")
        
        
        # Chercher le bouton "Create Alert" ou équivalent
        create_alert_selectors = [
            "//button[contains(text(), 'Create Alert') or contains(text(), 'Create alert') or contains(text(), 'New Alert')]",
            "//div[contains(text(), 'Create Alert') or contains(text(), 'Create alert') or contains(text(), 'New Alert')]",
            "//a[contains(text(), 'Create Alert') or contains(text(), 'Create alert') or contains(text(), 'New Alert')]",
            "//button[contains(@class, 'create') and contains(@class, 'alert')]",
            "//*[contains(@aria-label, 'Create alert') or contains(@aria-label, 'create alert')]",
            "//button[@aria-label='Create Alert']"
        ]
        
        create_button = None
        for selector in create_alert_selectors:
            buttons = driver.find_elements(By.XPATH, selector)
            print(f"   🔍 Sélecteur '{selector[:50]}...': {len(buttons)} boutons trouvés")
            if buttons:
                for i, button in enumerate(buttons):
                    try:
                        if button.is_displayed() and button.is_enabled():
                            create_button = button
                            button_text = button.text or button.get_attribute('aria-label') or f"Button {i}"
                            print(f"   ✅ Bouton de création trouvé: {button_text}")
                            break
                    except:
                        continue
                if create_button:
                    break
        
        if not create_button:
            print(f"   ❌ Aucun bouton de création d'alerte trouvé")
            # Essayer un raccourci clavier Alt+A comme alternative
            print("   � Tentative avec raccourci Alt+A...")
            actions = ActionChains(driver)
            actions.key_down(Keys.ALT).send_keys('a').key_up(Keys.ALT).perform()
            time.sleep(3)
        else:
            # Cliquer sur le bouton de création
            print(f"   🖱️ Clic sur le bouton de création...")
            driver.execute_script("arguments[0].scrollIntoView(true);", create_button)
            time.sleep(1)
            create_button.click()
            time.sleep(3)
        
         
        # ÉTAPE 1: Sélectionner la stratégie dans la condition
        print("🔧 Configuration de la condition - Sélection de la stratégie...")
        try:
            # Chercher le dropdown "Condition" qui contient "Price" par défaut
            condition_selectors = [
                "//span[contains(text(), 'Price')]/parent::div/parent::div",  # 
            ]
            
            condition_dropdown = None
            for selector in condition_selectors:
                try:
                    condition_dropdown = driver.find_element(By.XPATH, selector)
                    print(f"✅ Dropdown condition trouvé avec: {selector}")
                    break
                except:
                    continue
            
            if condition_dropdown:
                # Cliquer sur le dropdown pour l'ouvrir
                driver.execute_script("arguments[0].scrollIntoView(true);", condition_dropdown)
                time.sleep(0.5)
                condition_dropdown.click()
                time.sleep(2)
                
                # Chercher notre stratégie dans la liste
                strategy_selectors = [
                    "//span[contains(text(), 'Swing Bollinger Mean Reversion') and contains(@class, 'apply-overflow-tooltip')]",
                ]
                
                strategy_option = None
                for selector in strategy_selectors:
                    try:
                        strategy_option = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        print(f"✅ Stratégie trouvée avec: {selector}")
                        break
                    except:
                        continue
                
                if strategy_option:
                    strategy_option.click()
                    time.sleep(1)
                    print("✅ Stratégie 'Swing Bollinger Mean Reversion' sélectionnée")
                else:
                    print("⚠️ Stratégie 'Swing Bollinger Mean Reversion' non trouvée dans la liste")
                    # Lister les options disponibles pour debug
                    available_options = driver.find_elements(By.XPATH, "//div[contains(@class, 'option')] | //option | //li[contains(@class, 'item')]")
                    print(f"   Options disponibles ({len(available_options)}):")
                    for i, option in enumerate(available_options[:10]):
                        try:
                            option_text = option.text.strip()
                            if option_text:
                                print(f"     {i}: {option_text}")
                        except:
                            pass
            else:
                print("⚠️ Dropdown condition non trouvé")
                
        except Exception as condition_e:
            print(f"⚠️ Erreur lors de la sélection de la stratégie: {condition_e}")
        
        # ÉTAPE 2: Cliquer sur l'onglet Message
        print("🔍 Clic sur l'onglet Message...")
        try:
            message_tab = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "alert-dialog-tabs__message"))
            )
            message_tab.click()
            time.sleep(2)  # Attendre plus longtemps que l'onglet se charge
            print("✅ Onglet Message activé")
        except Exception as tab_e:
            print(f"⚠️ Erreur lors du clic sur l'onglet Message: {tab_e}")
            # Essayer un sélecteur alternatif
            try:
                message_tab = driver.find_element(By.XPATH, "//div[contains(text(), 'Message') and contains(@class, 'tab')]")
                message_tab.click()
                time.sleep(2)
                print("✅ Onglet Message activé (sélecteur alternatif)")
            except:
                print("⚠️ Impossible de trouver l'onglet Message")
        
        # Configuration du nom de l'alerte
        alert_name = f"{symbol} - Optimal Strategy Alert"
        
        # Chercher le champ nom de l'alerte avec plusieurs sélecteurs
        print("🔍 Recherche du champ nom d'alerte...")
        name_selectors = [
            "//input[@placeholder='Alert name']",
            "//input[@placeholder='Nom de l'alerte']",
            "//input[contains(@class, 'name')]",
            "//div[contains(@class, 'dialog')]//input[1]"
        ]
        
        name_input = None
        for selector in name_selectors:
            try:
                name_input = driver.find_element(By.XPATH, selector)
                print(f"✅ Champ nom trouvé avec: {selector}")
                break
            except:
                continue
        
        if name_input:
            try:
                # Faire défiler vers l'élément et le rendre visible
                driver.execute_script("arguments[0].scrollIntoView(true);", name_input)
                time.sleep(0.5)
                
                name_input.clear()
                name_input.send_keys(alert_name)
                print(f"✅ Nom configuré: {alert_name}")
            except Exception as name_e:
                print(f"⚠️ Erreur configuration nom: {name_e}")
        else:
            print("⚠️ Champ nom d'alerte non trouvé, utilisation du nom par défaut")
        
        # Configuration du message d'alerte (format JSON pour webhooks)
        alert_message = f"""{{
  "strategy": "Swing Bollinger Mean Reversion",
  "ticker": "{{{{ticker}}}}",
  "interval": "{{{{interval}}}}",
  "side": "{{{{strategy.order.action}}}}",
  "order_id": "{{{{strategy.order.id}}}}",
  "position_size": "{{{{strategy.position_size}}}}",
  "market_position_size": "{{{{strategy.market_position_size}}}}",
  "entry_price": "{{{{strategy.order.price}}}}",
  "date": "{{{{time}}}}",
  "comment": "{{{{strategy.order.comment}}}}",
  "optimized_params": {{
    "atr_multiplier": {getattr(driver, 'current_atr', 1.2)},
    "risk_reward": {getattr(driver, 'current_rr', 2.7)},
    "vol_multiplier": {getattr(driver, 'current_vol', 0.8)}
  }}
}}"""
        
        # Chercher le champ message avec plusieurs sélecteurs
        print("🔍 Recherche du champ message...")
        message_selectors = [
            "//textarea[@id='alert-message']",  # ID spécifique
            "//textarea[@placeholder='Message']",
            "//textarea[@placeholder='Message (Optional)']",
            "//textarea[contains(@class, 'message')]",
            "//div[contains(@class, 'message')]//textarea",
            "//textarea[contains(@data-name, 'message')]",
            "//div[contains(@class, 'dialog')]//textarea"
        ]
        
        message_input = None
        # Essayer d'abord avec l'ID spécifique
        try:
            message_input = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "alert-message"))
            )
            print("✅ Champ message trouvé avec ID: alert-message")
        except:
            # Si l'ID ne fonctionne pas, essayer les autres sélecteurs
            for selector in message_selectors:
                try:
                    message_input = WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    print(f"✅ Champ message trouvé avec: {selector}")
                    break
                except:
                    continue
        
        if message_input:
            try:
                # Faire défiler vers l'élément et le rendre visible
                driver.execute_script("arguments[0].scrollIntoView(true);", message_input)
                time.sleep(0.5)
                
                # Cliquer d'abord pour s'assurer que le champ est actif
                message_input.click()
                time.sleep(0.2)
                
                # Effacer complètement le contenu existant
                print("🧹 Effacement du contenu existant du champ message...")
                actions = ActionChains(driver)
                actions.key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND).perform()
                time.sleep(0.1)
                actions.send_keys(Keys.DELETE).perform()
                time.sleep(0.2)
                
                # Double vérification avec clear()
                message_input.clear()
                time.sleep(0.2)
                
                # Insérer notre message
                message_input.send_keys(alert_message)
                print("✅ Message configuré avec succès")
                
            except Exception as msg_e:
                print(f"⚠️ Erreur configuration message: {msg_e}")
                # Essayer une approche alternative avec ActionChains
                try:
                    print("🔄 Tentative alternative avec ActionChains...")
                    actions = ActionChains(driver)
                    actions.move_to_element(message_input).click().perform()
                    time.sleep(0.2)
                    
                    # Effacement complet avec sélection totale + suppression
                    actions.key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND).perform()
                    time.sleep(0.1)
                    actions.send_keys(Keys.DELETE).perform()
                    time.sleep(0.2)
                    
                    # Insérer le message
                    actions.send_keys(alert_message).perform()
                    print("✅ Message configuré avec ActionChains")
                except Exception as alt_e:
                    print(f"⚠️ Erreur alternative message: {alt_e}")
        else:
            print("⚠️ Champ message non trouvé")
        
        # Créer l'alerte - Essayer plusieurs sélecteurs pour le bouton
        print("🔍 Recherche du bouton de création...")
        create_selectors = [
            "//button[contains(text(), 'Create')]",
            "//button[contains(text(), 'Créer')]", 
            "//button[contains(text(), 'CREATE')]",
            "//button[@data-name='submit']",
            "//button[@data-name='create']",
            "//button[contains(@class, 'create')]",
            "//button[contains(@class, 'submit')]",
            "//div[contains(@class, 'dialog')]//button[last()]",
            "//button[contains(@class, 'primary')]"
        ]
        
        create_button = None
        for selector in create_selectors:
            try:
                create_button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                print(f"✅ Bouton de création trouvé avec: {selector}")
                break
            except:
                continue
        
        if create_button:
            try:
                # Faire défiler vers le bouton
                driver.execute_script("arguments[0].scrollIntoView(true);", create_button)
                time.sleep(0.5)
                
                # Essayer de cliquer
                create_button.click()
                print("✅ Bouton de création cliqué")
                
                # Attendre que l'alerte soit créée
                time.sleep(3)
                
                # Vérifier si l'alerte a été créée (la boîte de dialogue se ferme)
                try:
                    WebDriverWait(driver, 5).until_not(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'dialog')]"))
                    )
                    print(f"✅ Alerte créée avec succès pour {symbol}")
                    return True
                except:
                    print("⚠️ La boîte de dialogue est encore ouverte, possible erreur")
                    return False
                    
            except Exception as click_e:
                print(f"❌ Erreur lors du clic sur le bouton: {click_e}")
                return False
        else:
            print("❌ Bouton de création non trouvé")
            
            # Essayer d'utiliser la touche Entrée comme alternative
            try:
                print("🔄 Tentative avec la touche Entrée...")
                actions = ActionChains(driver)
                actions.send_keys(Keys.ENTER).perform()
                time.sleep(2)
                return True
            except:
                return False
            
    except Exception as e:
        print(f"❌ Erreur générale lors de la création d'alerte: {e}")
        return False

def create_alerts_for_symbols(best_params, symbols_to_process=None, dry_run=False):
    """Crée les alertes pour tous les symboles avec leurs paramètres optimaux."""
    
    if not best_params:
        print("❌ Aucun paramètre optimal chargé. Arrêt du script.")
        return
    
    # Filtrer les symboles si spécifié
    if symbols_to_process:
        filtered_params = {k: v for k, v in best_params.items() if k in symbols_to_process}
        if not filtered_params:
            print(f"❌ Aucun des symboles spécifiés trouvé: {symbols_to_process}")
            return
        best_params = filtered_params
    
    if dry_run:
        print("🧪 MODE DRY-RUN: Simulation sans création d'alertes")
        for symbol, params in best_params.items():
            print(f"🔍 {symbol}: ATR={params['ATR']}, RR={params['RR']}, Vol={params['Vol']}")
        return
    
    driver = setup_driver()
    if not driver:
        return
    
    try:
        # Supprimer toutes les alertes existantes créées par ce script
        deleted_count = delete_existing_alerts(driver)
        if deleted_count > 0:
            print(f"🧹 {deleted_count} alertes existantes supprimées")
            time.sleep(2)  # Pause après suppression
        
        successful_alerts = 0
        failed_alerts = 0
        
        for symbol, params in best_params.items():
            print(f"\n{'='*50}")
            print(f"🎯 Traitement de {symbol}")
            print(f"{'='*50}")
            
            # Aller sur le graphique du symbole
            symbol_url = f"{TRADINGVIEW_BASE_URL}?symbol=PEPPERSTONE:{symbol}"
            driver.get(symbol_url)
            time.sleep(5)  # Attendre le chargement
            
            # Stocker les paramètres actuels dans le driver pour le message d'alerte
            driver.current_atr = params['ATR']
            driver.current_rr = params['RR'] 
            driver.current_vol = params['Vol']
            
            # Configurer les paramètres optimaux
            if set_strategy_parameters(driver, params['ATR'], params['RR'], params['Vol']):
                
                # Attendre que la stratégie se charge avec les nouveaux paramètres
                time.sleep(3)
                
                # Créer l'alerte
                if create_alert(driver, symbol):
                    successful_alerts += 1
                    print(f"✅ {symbol}: Alerte créée avec succès")
                else:
                    failed_alerts += 1
                    print(f"❌ {symbol}: Échec création alerte")
            else:
                failed_alerts += 1
                print(f"❌ {symbol}: Échec configuration paramètres")
            
            # Pause entre les symboles pour éviter la surcharge
            time.sleep(2)
        
        print(f"\n{'='*50}")
        print(f"📊 RÉSUMÉ")
        print(f"{'='*50}")
        print(f"✅ Alertes créées avec succès: {successful_alerts}")
        print(f"❌ Échecs: {failed_alerts}")
        print(f"📈 Total traité: {successful_alerts + failed_alerts}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur générale: {e}")
    finally:
        print("\n🔄 Fermeture du driver...")
        driver.quit()

def main():
    parser = argparse.ArgumentParser(description="Créer des alertes TradingView avec paramètres optimaux")
    parser.add_argument('--symbols', nargs='+', help='Symboles spécifiques à traiter (ex: --symbols EURUSD GBPUSD)')
    parser.add_argument('--dry-run', action='store_true', help='Mode simulation sans création d\'alertes')
    parser.add_argument('--list', action='store_true', help='Lister les symboles disponibles')
    
    args = parser.parse_args()
    
    # Charger les meilleurs paramètres
    best_params = load_best_parameters()
    
    if args.list:
        print("\n📋 Symboles disponibles avec paramètres optimaux:")
        for symbol in sorted(best_params.keys()):
            params = best_params[symbol]
            print(f"  {symbol}: ATR={params['ATR']}, RR={params['RR']}, Vol={params['Vol']}")
        return
    
    if not best_params:
        print("❌ Aucun paramètre optimal disponible. Vérifiez votre fichier Excel.")
        return
    
    print("🚀 Démarrage de la création d'alertes TradingView")
    print("💡 Assurez-vous que:")
    print("   - Chrome est ouvert avec --remote-debugging-port=9222")
    print("   - Vous êtes connecté à TradingView")
    print("   - La stratégie est chargée sur le graphique")
    
    input("\n⏸️ Appuyez sur Entrée pour continuer...")
    
    # Créer les alertes
    create_alerts_for_symbols(
        best_params, 
        symbols_to_process=args.symbols,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main()
