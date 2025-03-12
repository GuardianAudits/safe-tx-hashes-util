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
    "flare": "",
    "berachain": "",
    "ink": "",
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

            time.sleep(3)

            security_notice_xpath = "/html/body/div[2]/div[3]/div/div[2]/div/button"

            try:
                WebDriverWait(driver, 6).until(
                    EC.presence_of_all_elements_located((By.XPATH, security_notice_xpath))
                )

                security_notice_button = driver.find_element(By.XPATH, security_notice_xpath)

                if security_notice_button:
                    security_notice_button.click()
            except:
                pass

            i = 0
            isAlternate = False
            isAlternate2 = False

            while True:

                ui_index = i+3 if i > 0 else 2
                i += 1

                pending_tx_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > h3 > button"
                pending_tx_selector_alternate = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div.MuiButtonBase-root.MuiAccordionSummary-root.mui-style-1duugzx"

                if not isAlternate:
                    try: 
                        WebDriverWait(driver, 3).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, pending_tx_selector))
                        )
                    except:
                        pending_tx_selector = pending_tx_selector_alternate
                        isAlternate = True
                else:
                    pending_tx_selector = pending_tx_selector_alternate


                time.sleep(0.25)

                # click on pending tx
                try: 
                    first_pending_tx = driver.find_element(By.CSS_SELECTOR, pending_tx_selector)
                    
                    first_pending_tx.click()
                except:
                    break # no more transactions

                advanced_details_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > button"
                if ui_index == 2:
                    advanced_details_selector_alternate = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiAccordion-root.MuiAccordion-rounded.Mui-expanded.styles_listItem__Y1EBh.mui-style-1tktuix > div.MuiCollapse-root.MuiCollapse-vertical.MuiCollapse-entered.mui-style-c4sutr > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > button"
                else: 
                    advanced_details_selector_alternate = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div.MuiCollapse-root.MuiCollapse-vertical.MuiCollapse-entered.mui-style-c4sutr > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > button"

                if isAlternate:
                    advanced_details_selector = advanced_details_selector_alternate

                print(advanced_details_selector)
                print(isAlternate)
                
                try: 
                    WebDriverWait(driver, 3).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, advanced_details_selector))
                    )
                except:
                    # Some UIs have a slightly different structure
                    advanced_details_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiAccordion-root.MuiAccordion-rounded.Mui-expanded.styles_listItem__Y1EBh.mui-style-1kyu3wg > div.MuiCollapse-root.MuiCollapse-vertical.MuiCollapse-entered.mui-style-c4sutr > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > button"
                    isAlternate2 = True

                time.sleep(0.25)

                # click advanced details
                advanced_details_button = driver.find_element(By.CSS_SELECTOR, advanced_details_selector)
                advanced_details_button.click()


                # get data
                if isAlternate2:
                    data_show_more_selector_first = "#__next > div.styles_main__ml_aX > div > main > div > div > div > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiAccordion-root.MuiAccordion-rounded.Mui-expanded.styles_listItem__Y1EBh.mui-style-1kyu3wg > div.MuiCollapse-root.MuiCollapse-vertical.MuiCollapse-entered.mui-style-c4sutr > div > div > div > div > div > div.styles_details___YvqT > div.styles_txData__V4oPh > div > div:nth-child(2) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div > button"
                else: 
                    data_show_more_selector_first = "#__next > div.styles_main__ml_aX > div > main > div > div > div > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiAccordion-root.MuiAccordion-rounded.Mui-expanded.styles_listItem__Y1EBh.mui-style-1qrr0iz > div > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > div > div:nth-child(4) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div > button"
                data_show_more_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > div > div:nth-child(4) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div > button"

                data_show_more_selector_alternate = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div.MuiCollapse-root.MuiCollapse-vertical.MuiCollapse-entered.mui-style-c4sutr > div > div > div > div > div > div.styles_details___YvqT > div.styles_txData__V4oPh > div > div:nth-child(2) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div > button"

                data_text_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > div > div:nth-child(4) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div"

                data_text_selector_alternate = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div.MuiCollapse-root.MuiCollapse-vertical.MuiCollapse-entered.mui-style-c4sutr > div > div > div > div > div > div.styles_details___YvqT > div.styles_txData__V4oPh > div > div:nth-child(2) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div"

                if isAlternate:
                    data_show_more_selector = data_show_more_selector_alternate
                    data_text_selector = data_text_selector_alternate

                if ui_index == 2 and isAlternate2:
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


                nonce_selector_alternate = f"#multisig_0x6ae078461f35c3cC216A71029F71ee7Bc4d9a10b_0x084f1dc9eaa5c1854126c61c4213a00d8557c76ccc5087135b163e048e5f91f7 > div.styles_nonce__DhqL3.MuiBox-root.mui-style-33ykiv"
                nonce_selector_alternate = f"#multisig_0x6ae078461f35c3cC216A71029F71ee7Bc4d9a10b_0x2f56f9d320240c80ac287b80a9ae04998e634efe8bd0f4abbf0527c0bc645a40 > div.styles_nonce__DhqL3.MuiBox-root.mui-style-33ykiv"

                nonce_xpath_alternate = f'//*[@id="multisig_0x6ae078461f35c3cC216A71029F71ee7Bc4d9a10b_0x2f56f9d320240c80ac287b80a9ae04998e634efe8bd0f4abbf0527c0bc645a40"]/div[1]'
                nonce_xpath_alternate = f'//*[@id="multisig_0x6ae078461f35c3cC216A71029F71ee7Bc4d9a10b_0x084f1dc9eaa5c1854126c61c4213a00d8557c76ccc5087135b163e048e5f91f7"]/div[1]'
                

                if isAlternate:

                    if ui_index == 2:
                        if isAlternate2:
                            expected_safe_transaction_copy_selector = "#__next > div.styles_main__ml_aX > div > main > div > div > div > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiAccordion-root.MuiAccordion-rounded.Mui-expanded.styles_listItem__Y1EBh.mui-style-1kyu3wg > div.MuiCollapse-root.MuiCollapse-vertical.MuiCollapse-entered.mui-style-c4sutr > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > div:nth-child(1) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div > div > div > span > button"
                        else:
                            expected_safe_transaction_copy_selector = "#__next > div > div > main > div > div > div > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiAccordion-root.MuiAccordion-rounded.Mui-expanded.styles_listItem__Y1EBh.mui-style-1tktuix > div.MuiCollapse-root.MuiCollapse-vertical.MuiCollapse-entered.mui-style-c4sutr > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > div:nth-child(1) > div.styles_container__Y8ngK > div > div > span > button"
                    else:
                        if isAlternate2:
                            expected_safe_transaction_copy_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div.MuiCollapse-root.MuiCollapse-vertical.MuiCollapse-entered.mui-style-c4sutr > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > div:nth-child(1) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div > div > div > span > button"
                        else:
                            expected_safe_transaction_copy_selector = f"#__next > div > div > main > div > div > div > div:nth-child({ui_index}) > div.MuiCollapse-root.MuiCollapse-vertical.MuiCollapse-entered.mui-style-c4sutr > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > div:nth-child(1) > div.styles_container__Y8ngK > div > div > span > button"

                    expected_safe_transaction_copy_button = driver.find_element(By.CSS_SELECTOR, expected_safe_transaction_copy_selector)
                    expected_safe_transaction_copy_button.click()

                    expected_domain_hash_text = ""
                    expected_message_hash_text = ""

                    expected_safe_transaction_text = driver.execute_script("return navigator.clipboard.readText()")

                    print(expected_safe_transaction_text)

                    nonce_selector = f"#multisig_{address}_{expected_safe_transaction_text} > div.styles_nonce__DhqL3.MuiBox-root.mui-style-33ykiv"

                    nonce = driver.find_element(By.CSS_SELECTOR, nonce_selector).text

                else: 
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