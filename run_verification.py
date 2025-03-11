import json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import subprocess

from pprint import pprint

# Simply add the network name and the URL to the transaction queue of the Safe to verify all of it's transactions
safe_urls = {
    "ethereum": "",
    "arbitrum": "",
}

def scrape_gnosis_safe_transactions():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment for headless mode
    driver = webdriver.Chrome(options=chrome_options)

    transaction_verification_items = []
    
    try:
        for network, url in safe_urls.items():
            driver.get(url)
            address = url[-42:] # last 42 characters of the URL

            time.sleep(1)

            security_notice_xpath = "/html/body/div[2]/div[3]/div/div[2]/div/button"

            WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.XPATH, security_notice_xpath))
            )

            security_notice_button = driver.find_element(By.XPATH, security_notice_xpath)

            if security_notice_button:
                security_notice_button.click()

            i = 0

            while True:
                time.sleep(0.25)

                ui_index = i+3 if i > 0 else 2
                i += 1

                pending_tx_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > h3 > button"

                try: 
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, pending_tx_selector))
                    )
                except:
                    break

                time.sleep(0.25)

                # click on pending tx
                first_pending_tx = driver.find_element(By.CSS_SELECTOR, pending_tx_selector)
                
                first_pending_tx.click()

                advanced_details_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > button"


                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, advanced_details_selector))
                )

                time.sleep(0.25)

                # click advanced details
                advanced_details_button = driver.find_element(By.CSS_SELECTOR, advanced_details_selector)
                advanced_details_button.click()


                # get data
                data_show_more_selector_first = "#__next > div.styles_main__ml_aX > div > main > div > div > div > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiAccordion-root.MuiAccordion-rounded.Mui-expanded.styles_listItem__Y1EBh.mui-style-1qrr0iz > div > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > div > div:nth-child(4) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div > button"
                data_show_more_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > div > div:nth-child(4) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div > button"

                data_text_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > div > div:nth-child(4) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div"

                if i == 0:
                    data_show_more_selector = data_show_more_selector_first

                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, data_show_more_selector))
                )

                time.sleep(0.25)

                data_show_more_button = driver.find_element(By.CSS_SELECTOR, data_show_more_selector)
                data_show_more_button.click()

                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, data_text_selector))
                )

                time.sleep(0.25)

                data_text = driver.find_element(By.CSS_SELECTOR, data_text_selector).text.replace(" Show less", "")
                print(data_text)

                expected_safe_transaction_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > div > div.MuiStack-root.mui-style-1821gv5 > div:nth-child(1) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div"
                expected_domain_hash_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > div > div.MuiStack-root.mui-style-1821gv5 > div:nth-child(2) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div"
                expected_message_hash_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > div > div.MuiStack-root.mui-style-1821gv5 > div:nth-child(3) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div"
                nonce_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > div > div:nth-child(11) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz"

                expected_safe_transaction_text = driver.find_element(By.CSS_SELECTOR, expected_safe_transaction_selector).text
                expected_domain_hash_text = driver.find_element(By.CSS_SELECTOR, expected_domain_hash_selector).text
                expected_message_hash_text = driver.find_element(By.CSS_SELECTOR, expected_message_hash_selector).text
                nonce = driver.find_element(By.CSS_SELECTOR, nonce_selector).text

                transaction_verification_items.append({
                    "network": network,
                    "address": address,
                    "nonce": nonce,
                    "expected_data": data_text,
                    "expected_safe_transaction_hash": expected_safe_transaction_text,
                    "expected_domain_hash": expected_domain_hash_text,
                    "expected_message_hash": expected_message_hash_text
                })

                pprint(transaction_verification_items)

                time.sleep(0.25)

        # Write the collected data to data.json
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(transaction_verification_items, f, indent=4)

        print(f"Successfully wrote {len(transaction_verification_items)} transactions to data.json")

    finally:
        driver.quit()

def run_verification():
    subprocess.run(["bash", "./safe_hashes.sh", "--bulk-file", "data.json"], check=True)

if __name__ == "__main__":
    scrape_gnosis_safe_transactions()
    run_verification()