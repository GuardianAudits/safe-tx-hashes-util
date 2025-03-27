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

network_to_rpc = {
    "ethereum": "https://rpc.ankr.com/eth",
    "arbitrum": "https://arb1.arbitrum.io/rpc",
    "flare": "https://rpc.ankr.com/flare",
    "berachain": "https://cdn.routescan.io/api/evm/80094/rpc",
    "ink": "https://rpc-qnd.inkonchain.com",
}

network_to_safe_address = {
    "ethereum": "0x4DFF9b5b0143E642a3F63a5bcf2d1C328e600bf8",
    "arbitrum": "0x4DFF9b5b0143E642a3F63a5bcf2d1C328e600bf8",
    "flare": "0x6ae078461f35c3cC216A71029F71ee7Bc4d9a10b",
    "berachain": "0x425d1D17C33bdc0615eA18D1b18CCA7e14bEeb58",
    "ink": "0xc95de55ce5e93f788A1Faab2A9c9503F51a5dAE2",
}

# Notice that Bera is Alternate2

def scrape_gnosis_safe_transactions():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment for headless mode
    driver = webdriver.Chrome(options=chrome_options)

    transaction_verification_items = []

    isSigned = False
    
    try:
        for network, url in safe_urls.items():
            driver.get(url)
            address = url[-42:] # last 42 characters of the URL

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

            try:
                time.sleep(0.5)

                accept_all_button_selector = f"#__next > div.styles_popup__tYrT2 > div > form > div > div > div.MuiGrid-root.MuiGrid-container.mui-style-roudc1 > div:nth-child(2) > button"

                driver.find_element(By.CSS_SELECTOR, accept_all_button_selector).click()
            except:
                pass


            try: 
                accept_all_button_selector_2 = f"#__next > div.styles_popup__tYrT2 > div > form > div > div > div.MuiGrid-root.MuiGrid-container.mui-style-roudc1"

                driver.find_element(By.CSS_SELECTOR, accept_all_button_selector_2).click()
            except:
                pass


            i = 0
            isAlternate = False
            isAlternate2 = False

            while True:

                ui_index = i+3 if i > 0 else 2
                i += 1

                
                if isSigned:
                    pending_tx_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > h3 > button"
                    pending_tx_selector_alternate = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div.MuiButtonBase-root.MuiAccordionSummary-root.mui-style-1duugzx"

                else:
                    pending_tx_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > h3 > div"
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

                driver.execute_script("window.scrollBy(0, 100);")
                
                try: 
                    WebDriverWait(driver, 5).until(
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
                                        
                data_to_address_text_selector = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div > div > div > div > div > div > div.styles_details___YvqT.undefined > div.styles_txSummary__CFbSQ > div > div:nth-child(2) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div > div > div > div.MuiBox-root.mui-style-b5p5gz > span > span"
                data_to_address_text_selector_first = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiAccordion-root.MuiAccordion-rounded.Mui-expanded.styles_listItem__Y1EBh.mui-style-1qrr0iz > div > div > div > div > div > div > div.styles_details___YvqT.undefined > div.styles_txSummary__CFbSQ > div > div:nth-child(2) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div > div > div > div.MuiBox-root.mui-style-b5p5gz > span > span"                         

                if not isAlternate2:
                    data_to_address_copy_selector_first_alternate = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiAccordion-root.MuiAccordion-rounded.Mui-expanded.styles_listItem__Y1EBh.mui-style-1tktuix > div.MuiCollapse-root.MuiCollapse-vertical.MuiCollapse-entered.mui-style-c4sutr > div > div > div > div > div > div.styles_txSigners__Zdzmy > ul > li.MuiListItem-root.MuiListItem-gutters.MuiListItem-padding.mui-style-vtcp25 > div.MuiListItemText-root.mui-style-1tsvksn > span > div > div.MuiBox-root.mui-style-i6bazn > div > span > button"
                    data_to_address_copy_selector_alternate = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div.MuiCollapse-root.MuiCollapse-vertical.MuiCollapse-entered.mui-style-c4sutr > div > div > div > div > div > div.styles_txSigners__Zdzmy > ul > li.MuiListItem-root.MuiListItem-gutters.MuiListItem-padding.mui-style-vtcp25 > div.MuiListItemText-root.mui-style-1tsvksn > span > div > div.MuiBox-root.mui-style-i6bazn > div > span > button"
                else:
                    print("GETTING HERE")
                    data_to_address_copy_selector_first_alternate = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiAccordion-root.MuiAccordion-rounded.Mui-expanded.styles_listItem__Y1EBh.mui-style-1kyu3wg > div.MuiCollapse-root.MuiCollapse-vertical.MuiCollapse-entered.mui-style-c4sutr > div > div > div > div > div > div.styles_txSigners__Zdzmy > ul > li.MuiListItem-root.MuiListItem-gutters.MuiListItem-padding.mui-style-ziyhyr > div.MuiListItemText-root.mui-style-1tsvksn > span > div > div.MuiBox-root.mui-style-1lchl8k > div > span > button"
                    data_to_address_copy_selector_alternate = f"#__next > div.styles_main__ml_aX > div > main > div > div > div > div:nth-child({ui_index}) > div.MuiCollapse-root.MuiCollapse-vertical.MuiCollapse-entered.mui-style-c4sutr > div > div > div > div > div > div.styles_txSigners__Zdzmy > ul > li.MuiListItem-root.MuiListItem-gutters.MuiListItem-padding.mui-style-ziyhyr > div.MuiListItemText-root.mui-style-1tsvksn > span > div > div.MuiBox-root.mui-style-1lchl8k > div > span > button"
                

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

                if isAlternate:

                    if ui_index == 2:
                        data_to_address_copy_selector = data_to_address_copy_selector_first_alternate
                        if isAlternate2:
                            expected_safe_transaction_copy_selector = "#__next > div.styles_main__ml_aX > div > main > div > div > div > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiAccordion-root.MuiAccordion-rounded.Mui-expanded.styles_listItem__Y1EBh.mui-style-1kyu3wg > div.MuiCollapse-root.MuiCollapse-vertical.MuiCollapse-entered.mui-style-c4sutr > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > div:nth-child(1) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-true.mui-style-kxu0dz > div > div > div > span > button"
                        else:
                            expected_safe_transaction_copy_selector = "#__next > div > div > main > div > div > div > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiAccordion-root.MuiAccordion-rounded.Mui-expanded.styles_listItem__Y1EBh.mui-style-1tktuix > div.MuiCollapse-root.MuiCollapse-vertical.MuiCollapse-entered.mui-style-c4sutr > div > div > div > div > div > div.styles_details___YvqT > div.styles_txSummary__CFbSQ > div:nth-child(1) > div.styles_container__Y8ngK > div > div > span > button"
                    else:
                        data_to_address_copy_selector = data_to_address_copy_selector_alternate
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


                    try: 
                        to_address_copy_button = driver.find_element(By.CSS_SELECTOR, data_to_address_copy_selector)
                        to_address_copy_button.click()
                    except:
                        # scroll up a bit and try again
                        driver.execute_script("window.scrollBy(0, -150);")
                        to_address_copy_button = driver.find_element(By.CSS_SELECTOR, data_to_address_copy_selector)
                        to_address_copy_button.click()

                        #scroll back down
                        driver.execute_script("window.scrollBy(0, 150);")

                    to_address = driver.execute_script("return navigator.clipboard.readText()")

                    nonce_selector = f"#multisig_{address}_{expected_safe_transaction_text} > div.styles_nonce__DhqL3.MuiBox-root.mui-style-33ykiv"

                    nonce = driver.find_element(By.CSS_SELECTOR, nonce_selector).text

                else: 
                    expected_safe_transaction_text = driver.find_element(By.CSS_SELECTOR, expected_safe_transaction_selector).text
                    expected_domain_hash_text = driver.find_element(By.CSS_SELECTOR, expected_domain_hash_selector).text
                    expected_message_hash_text = driver.find_element(By.CSS_SELECTOR, expected_message_hash_selector).text
                    nonce = driver.find_element(By.CSS_SELECTOR, nonce_selector).text

                    if ui_index == 2:
                        data_to_address_text_selector = data_to_address_text_selector_first

                    to_address = driver.find_element(By.CSS_SELECTOR, data_to_address_text_selector).text

                transaction_verification_items.append({
                    "network": network,
                    "address": address,
                    "to_address": to_address,
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


def simulate_actions():
    # Read in the data.json file
    with open("data.json", "r", encoding="utf-8") as f:
        transaction_verification_items = json.load(f)

        # simulate each transaction
        for transaction in transaction_verification_items:
            rpc_url = network_to_rpc[transaction.get("network")]
            safe_address = network_to_safe_address[transaction.get("network")]
            result = subprocess.run(
                [
                    "cast",
                    "call",
                    transaction.get("to_address"),
                    "--rpc-url",
                    rpc_url,
                    "--from",
                    safe_address,
                    "--data",
                    transaction.get("expected_data"),
                    "--trace"
                ],
                check=True
            )
            print(result)

if __name__ == "__main__":
    # scrape_gnosis_safe_transactions()
    # run_verification()
    simulate_actions()