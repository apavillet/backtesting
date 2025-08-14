# -*- coding: utf-8 -*-

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
import random
from multiprocessing import set_start_method

# === CONFIG ===
TRADINGVIEW_URL = "https://www.tradingview.com/chart/0RKjg68o/"
# Arrays from 1.0 to 5.0 with 0.1 increments
ATR_MULTIPLIERS = [round(i * 0.1, 1) for i in range(10, 51)]  # 1.0 to 5.0
RR_VALUES = [round(i * 0.1, 1) for i in range(20, 51)]  # 2.0 to 5.0
SYMBOL_LIST = ['EURUSD', 'EURAUD', 'USDCAD', 'NZDJPY', 'GBPUSD', 'USDJPY', 'EURJPY', 'GBPJPY', 'AUDUSD', 'AUDJPY', 'AUDCAD', 'USDCHF', 'EURNZD', 'EURGBP', 'NZDUSD', 'EURCAD', 'EURCHF', 'GBPCAD', 'AUDNZD', 'CADCHF', 'GBPCHF', 'CADJPY', 'GBPAUD', 'GBPNZD', 'NZDCAD']

# Each profile gets a unique known port from 9221 to 9228
DEBUG_PORTS = [9221 + i for i in range(8)]

# Save full HTML for inspection
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_backtest_for_symbol(currency, user_data_dir, port):
    print(f"Running backtest for {currency} with user data dir: {user_data_dir}")
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"--remote-debugging-port={port}")
    options.add_argument(f'--user-data-dir={user_data_dir}')
    driver = webdriver.Chrome(options=options)

    results = []

    # Navigate to the correct chart
    driver.get(f"https://www.tradingview.com/chart/0RKjg68o/?symbol=PEPPERSTONE:{currency}")
    time.sleep(5)  # Wait for the chart to load
    symbol_name = currency
    print(f"Testing symbol: {symbol_name}")
    # Open settings using Command+P (Mac)
    actions = ActionChains(driver)
    actions.key_down(Keys.COMMAND).send_keys('p').key_up(Keys.COMMAND).perform()
    time.sleep(2)
    for atr in ATR_MULTIPLIERS:
        for rr in RR_VALUES:
            success = False
            for attempt in range(3):
                print(f"Testing ATR={atr}, RR={rr}, Attempt={attempt+1}")
                # ATR input
                atr_input = driver.find_element(
                    By.XPATH,
                    "//div[contains(text(),'ATR Stop Multiplier') or contains(text(),'Multiplicateur ATR')]/parent::div/following-sibling::div//input"
                )
                atr_input.send_keys(Keys.COMMAND + "a")
                actions.key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND).perform()
                time.sleep(1)  # Ensure input is cleared
                atr_input.send_keys(Keys.BACKSPACE)

                atr_input.send_keys(str(atr))

                # RR input
                rr_input = driver.find_element(
                    By.XPATH,
                    "//div[contains(text(),'Base Risk/Reward Ratio') or contains(text(),'Ratio Risque/Rendement de base')]/parent::div/following-sibling::div//input"
                )
                rr_input.send_keys(Keys.COMMAND + "a")
                actions.key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND).perform()
                rr_input.send_keys(Keys.BACKSPACE)

                rr_input.send_keys(str(rr))

                time.sleep(1)  # Ensure input is cleared
                actions.send_keys(Keys.TAB).perform()  # Move focus to the next element
                # Wait until snackbar disappears if present
                try:
                    WebDriverWait(driver, 3).until_not(
                        EC.presence_of_element_located((By.CLASS_NAME, "snackbarLayer-_MKqWk5g"))
                    )
                except:
                    pass  # Ignore if not found or timeout

                # Get Net Profit
                net_profit_elem = driver.find_element(By.XPATH, "//div[contains(text(),'Profit net') or contains(text(),'Total P&L')]/parent::div/following-sibling::div/div[1]")
                net_profit = net_profit_elem.text
                # Remove everything except numbers and decimal point and + or - sign
                net_profit = net_profit.replace('$', '').replace('€', '').replace('£', '').replace(',', '')
                net_profit = net_profit.strip()

                # Get % Win Rate
                win_rate_elem = driver.find_element(By.XPATH, "//div[contains(text(),'Pourcentage de trades gagnants') or contains(text(),'Profitable trades')]/parent::div/following-sibling::div/div[1]")
                win_rate = win_rate_elem.text

                # Get drawdown
                drawdown_elem = driver.find_element(By.XPATH, "//div[contains(text(),'Drawdown') or contains(text(),'drawdown')]/parent::div/following-sibling::div/div[1]")
                drawdown = drawdown_elem.text
                # Remove everything except numbers and decimal point
                drawdown = drawdown.replace('%', '').replace('€', '').replace('£', '').replace(',', '')
                drawdown = drawdown.strip()

                # Total trades
                total_trades_elem = driver.find_element(By.XPATH, "//div[contains(text(),'Total des trades') or contains(text(),'Total trades')]/parent::div/following-sibling::div")
                total_trades = total_trades_elem.text

                # Profit factor
                profit_factor_elem = driver.find_element(By.XPATH, "//div[contains(text(),'Profit factor') or contains(text(),'Profit factor')]/parent::div/following-sibling::div")
                profit_factor = profit_factor_elem.text
                # Remove everything except numbers and decimal point
                profit_factor = profit_factor.replace('x', '').replace(',', '.').strip()

                print(f"Net Profit: {net_profit}, Win Rate: {win_rate}, Drawdown: {drawdown}, Total Trades: {total_trades}, Profit Factor: {profit_factor}")

                results.append({
                    "ATR Multiplier": atr,
                    "RR": rr,
                    "Net Profit": net_profit,
                    "Win Rate": win_rate,
                    "drawdown": drawdown,
                    "Total Trades": total_trades,
                    "Profit Factor": profit_factor,
                    "Symbol": symbol_name
                })
                success = True
                break
            if not success:
                results.append({
                    "ATR Multiplier": atr,
                    "RR": rr,
                    "Net Profit": "Error",
                    "Win Rate": "Error",
                    "drawdown": "Error",
                    "Total Trades": "Error",
                    "Profit Factor": "Error",
                    "Symbol": symbol_name
                })
            time.sleep(1)

    # Reset to base parameters
    BASE_ATR = 1.2
    BASE_RR = 2.7
    actions = ActionChains(driver)
    actions.key_down(Keys.COMMAND).send_keys('p').key_up(Keys.COMMAND).perform()
    time.sleep(2)

    # ATR input
    atr_input = driver.find_element(
        By.XPATH,
        "//div[contains(text(),'ATR Stop Multiplier') or contains(text(),'Multiplicateur ATR')]/parent::div/following-sibling::div//input"
    )
    atr_input.send_keys(Keys.COMMAND + "a")
    actions.key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND).perform()
    time.sleep(1)  # Ensure input is cleared
    atr_input.send_keys(Keys.BACKSPACE)

    atr_input.send_keys(str(BASE_ATR))

    # RR input
    rr_input = driver.find_element(
        By.XPATH,
        "//div[contains(text(),'Base Risk/Reward Ratio') or contains(text(),'Ratio Risque/Rendement de base')]/parent::div/following-sibling::div//input"
    )
    rr_input.send_keys(Keys.COMMAND + "a")
    actions.key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND).perform()
    time.sleep(1)  # Ensure input is cleared
    rr_input.send_keys(Keys.BACKSPACE)

    rr_input.send_keys(str(BASE_RR))

    # Wait until snackbar disappears if present
    try:
        WebDriverWait(driver, 5).until_not(
            EC.presence_of_element_located((By.CLASS_NAME, "snackbarLayer-_MKqWk5g"))
        )
    except:
        pass  # Ignore if not found or timeout
    close_button = driver.find_element(By.XPATH, "//button[@data-name='submit-button']")
    close_button.click()
    time.sleep(2)
    print("Strategy parameters reset to default values.")

    driver.quit()
    return results

def run_with_profile(args):
    symbol, profile_path, port = args
    return run_backtest_for_symbol(symbol, profile_path, port)

def main():
    import multiprocessing as mp

    print("Log into TradingView manually if needed. Starting tests...")

    chrome_profiles = [
        (symbol, f"/tmp/selenium_profile_{i%8+1}", DEBUG_PORTS[i % 8])
        for i, symbol in enumerate(SYMBOL_LIST)
    ]
    print(f"Using {len(chrome_profiles)} profiles for {len(SYMBOL_LIST)} symbols.")
    print("Profiles:", chrome_profiles)

    with mp.Pool(processes=mp.cpu_count() // 2) as pool:
        all_results_nested = pool.map(run_with_profile, chrome_profiles)

    # Flatten results
    all_results = [item for sublist in all_results_nested for item in sublist]

    all_df = pd.DataFrame(all_results)
    output_file = "tradingview_backtest_results.xlsx"
    all_df.to_excel(output_file, sheet_name="All_Results", index=False, engine='openpyxl')

    # Best per symbol
    all_df["Net Profit Clean"] = pd.to_numeric(all_df["Net Profit"].replace('[\$,]', '', regex=True), errors='coerce')
    best_per_symbol = all_df.loc[all_df.groupby("Symbol")["Net Profit Clean"].idxmax()].reset_index(drop=True)
    with pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        best_per_symbol.to_excel(writer, index=False, sheet_name="Best_Per_Symbol")

    # Average metrics by parameter combination (ATR Multiplier, RR) across all symbols
    avg_per_params = all_df.groupby(["ATR Multiplier", "RR"]).agg({
        "Net Profit Clean": "mean",
        "Win Rate": "mean",
        "drawdown": "mean",
        "Profit Factor": "mean",
        "Total Trades": "mean"
    }).reset_index()

    # Write average parameter performance to a new sheet
    with pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        avg_per_params.to_excel(writer, index=False, sheet_name="Average_Per_Parameters")

    print(f"Backtesting complete. Results saved to {output_file}")

if __name__ == "__main__":
    set_start_method("spawn")
    main()