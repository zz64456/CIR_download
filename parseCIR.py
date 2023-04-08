from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time

def initialize_parser():
    options = webdriver.ChromeOptions()
    options.add_experimental_option('detach', True) # 控制瀏覽器自動關閉
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_browser = webdriver.Chrome('./chromedriver', options=options)
    chrome_browser.maximize_window()
    chrome_browser.get('https://www.cir-safety.org/ingredients') # CIR - INGREDIENTS 網頁
    return chrome_browser
    
    # chrome_browser.get('http://127.0.0.1:5000/') # 點擊單一Report

# assert 'On-Line INFOBASE - ingredients' in chrome_browser.title


def open_alphabet_tabs(alphabets):
    count = 0
    for alpha in alphabets:
        if count > 3:
            break
        print(alpha.text)
        button = alpha.find_element(By.TAG_NAME, 'a')
        time.sleep(3)
        button.click()
        count += 1
        print(f'Finish opening tabs[{count}]')


def main():
    chrome_browser = initialize_parser()

    #get current window handle
    p = chrome_browser.current_window_handle

    alphabets_div = chrome_browser.find_element(By.CLASS_NAME, 'glossary ')
    alphabets = alphabets_div.find_elements(By.CLASS_NAME, 'glossary-letter')


    
    open_alphabet_tabs(alphabets)

    chrome_browser.switch_to.window(chrome_browser.window_handles[1])

    



    # time.sleep(10)




    # plaint_text = chrome_browser.find_element(By.TAG_NAME, "body").text

    # print(plaint_text)



if __name__ == '__main__':
    main()