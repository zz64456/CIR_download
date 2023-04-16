from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchAttributeException
from selenium.webdriver.support import event_firing_webdriver
from selenium.webdriver.common.keys import Keys
import time, os



def initialize_parser():
    options = webdriver.ChromeOptions()
    options.add_experimental_option('detach', True) # 控制瀏覽器自動關閉
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    options.add_experimental_option('prefs', {
        "download.default_directory": r"C:\Users\z5202\training\parse-CIR\pdf",
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    })

    chrome_browser = webdriver.Chrome('./chromedriver', options=options)
    chrome_browser.maximize_window()
    chrome_browser.get('https://www.cir-safety.org/ingredients') # CIR - INGREDIENTS 網頁
    return chrome_browser
    


def open_alphabet_tabs(chrome_browser, alphabets):
    childs_window = {}
    count = 0
    for alpha in alphabets:
        if count > 1:
            break

        windows_old = chrome_browser.window_handles

        button = alpha.find_element(By.TAG_NAME, 'a')
        time.sleep(1.5)
        button.click()
        count += 1
        print(f'Finish opening {alpha.text}')

        # matching opened windows
        windows_new = chrome_browser.window_handles
        new = list(set(windows_new) - set(windows_old))
        childs_window[alpha.text] = new[0]
    return childs_window


def fetch_target_table(chrome_browser, try_times = 3, fail_times = 0):
    if fail_times <= try_times:
        try:
            target_table = chrome_browser.find_element(By.XPATH, '/html/body/form/table/tbody/tr[2]/td/table/tbody')
        except:
            print('\nFail times:', fail_times)
            fail_times += 1
            fetch_target_table(chrome_browser, try_times, fail_times)
    return target_table


def downloader(target):
    # print('\ntarget:', target.get_attribute('href'))
    file_name = target.get_attribute('href').split('.pdf')[0].split('/')[-1]
    # print('\nfilename:', file_name)
    path = f'C:\\Users\\z5202\\training\\parse-CIR\\pdf\\{file_name}.pdf'
    # print('\npath:', path, '\n')
    if not os.path.isfile(path):
        target.click()
        time.sleep(1)
        print('\nfilename:', file_name, ' DOWNLOADED!')


def main():
    chrome_browser = initialize_parser()
    actions = ActionChains(chrome_browser)

    alphabets_div = chrome_browser.find_element(By.CLASS_NAME, 'glossary ')
    alphabets = alphabets_div.find_elements(By.CLASS_NAME, 'glossary-letter')

    # CIR 主頁面
    parent_window = chrome_browser.current_window_handle


    # 將字母分頁全部開好
    childs_window = open_alphabet_tabs(chrome_browser, alphabets)


    # 照字母順序A-Z
    for key in childs_window.keys():
        chrome_browser.switch_to.window(childs_window[key])
        print(f"\nSwitch to Alpha: [{key}]")

        # 定位字母清單(list)
        tbody = chrome_browser.find_element(By.XPATH, '/html/body/table/tbody/tr/td/table/tbody/tr[5]/td/table/tbody/tr/td[3]/table/tbody/tr/td/table/tbody')
        buttons = tbody.find_elements(By.XPATH, './tr/td/a')

        
        
        # list
        through = set()



        

        for button in buttons:
            
            if len(through) > 0 and len(through) % 15 == 0: # 每15筆
                print("\n----------- Page Down... -----------\n")
                actions.send_keys(Keys.PAGE_DOWN).perform() # 按下Page Down滑動滾輪
                time.sleep(1)
                


            # 定位項目 item
            print('\n*************  Target =>', button.text, ' *************\n')
            time.sleep(1)


            actions.reset_actions()

            # actions.move_by_offset(button.location['x'], button.location['y'])

            # 點擊item(人名)，打開pdf選擇視窗
            actions.move_to_element(button).click()
            actions.perform()


            time.sleep(4)

            # 切換到pdf選擇視窗
            chrome_browser.switch_to.window(chrome_browser.window_handles[-1])
            print("Switch to pdf page: "+str(chrome_browser.current_url))

            target_table = fetch_target_table(chrome_browser)
                
            target_trs   = target_table.find_elements(By.XPATH, './tr')

            del(target_trs[0])

            latest_year = 1500
            # download = False
            for tr in target_trs:
                time.sleep(1)

                tds = tr.find_elements(By.XPATH, './td')

                ingredient = tds[0].find_element(By.XPATH, './font[@class="regtext"]')
                status     = tds[1].find_element(By.XPATH, './table/tbody/tr/td/table/tbody/tr/td/font/a')
                date       = tds[2].find_element(By.XPATH, './font')

                if ingredient not in through:
                    through.add(ingredient.text)

                if len(date.text) > 0:
                    year = date.text.split(', ')
                    if len(year) > 1:
                        year = year[1]
                    else:
                        year = date.text.split('/')[2]

                    if int(year) >= int(latest_year):
                        latest_year = year
                        target = status

                

                
            time.sleep(1)

            downloader(target)

            time.sleep(1)


            print('\nnums: ',len(through))



            chrome_browser.close()

            chrome_browser.switch_to.window(childs_window[key])







if __name__ == '__main__':
    main()