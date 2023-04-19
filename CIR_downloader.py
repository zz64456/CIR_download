from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta, timezone
import logging
import time, os



def setup_logging(logDir):
    dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
    now = dt1.astimezone(timezone(timedelta(hours=8))) # 轉換時區 -> 東八區
    date_today = datetime.strftime(now, '%Y-%m-%d')
    
    logName = date_today + '.log'
    # logDir  = 'log'
    logPath = 'log/' + logDir + '/' + logName

    os.makedirs('log/' + logDir,exist_ok=True)

    allLogger = logging.getLogger(logDir+'allLogger')
    allLogger.setLevel(logging.DEBUG)

    fileHandler = logging.FileHandler(logPath, encoding='utf-8',mode='a')
    fileHandler.setLevel(logging.INFO)

    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(logging.WARNING)

    AllFormatter = logging.Formatter("%(asctime)s - [line:%(lineno)d] - %(levelname)s: %(message)s")
    fileHandler.setFormatter(AllFormatter)
    streamHandler.setFormatter(AllFormatter)

    allLogger.addHandler(fileHandler)
    allLogger.addHandler(streamHandler)

    return allLogger




# logging
logDir = 'crawler'
loggerName = logDir+'allLogger'
setup_logging(logDir)
logger = logging.getLogger(loggerName)






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
        if count > 2:
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
    # 設置等待時間
    wait = WebDriverWait(chrome_browser, 10)

    target_table = False
    location = (By.XPATH, '/html/body/form/table/tbody/tr[2]/td/table/tbody')

    while fail_times < try_times and target_table is False:
        try:
            target_table = wait.until(EC.presence_of_element_located(location))
        except Exception as e:
            fail_times += 1
            print('\nFail times:', fail_times)
            print(str(e))
            logger.error(str(e))

        
    return target_table


def downloader(alphabet, target, index):
    
    # print('\ntarget:', target.get_attribute('href'))
    file_name = target.get_attribute('href').split('.pdf')[0].split('/')[-1]
    print(f'\nfilename =>   [ {file_name} ]')

    destination_directory = f'pdf\\{alphabet}'
    if not os.path.isdir(destination_directory):
        os.makedirs(destination_directory)

    path = f'{destination_directory}\\{file_name}.pdf'
    if not os.path.isfile(path):
        print("\nIt's a new file. Start to Download it.")

        target.click()
    
        finish = False
        t = 0
        timeout = 10
        while finish is not True and t < timeout:
            finish = False
            t += 1
            print('not yet..')
            time.sleep(1)
            if os.path.isfile(f'pdf\\{file_name}.pdf'):
                finish = True
                print('Download is finished')
        try:
            os.replace(f'pdf\\{file_name}.pdf', path)
        except Exception as e:
            print(e)
            logger.error(f'alphabet => {alphabet}, ingredient => {index},  Replace failed.')

        print('\nFile added !')

    else:
        print("\nExists already")




# web driver init
chrome_browser = initialize_parser()

# Action chains init
actions = ActionChains(chrome_browser)


def main():
    alphabets_div = chrome_browser.find_element(By.CLASS_NAME, 'glossary ')
    alphabets = alphabets_div.find_elements(By.CLASS_NAME, 'glossary-letter')

    # CIR 主頁面
    parent_window = chrome_browser.current_window_handle


    # 將字母分頁全部開好
    childs_window = open_alphabet_tabs(chrome_browser, alphabets)


    # 照字母順序A-Z
    for alphabet in childs_window.keys():

        chrome_browser.switch_to.window(childs_window[alphabet])
        print(f"\nSwitch to Alphabet [{alphabet}]")

        # [字母]開頭之文章
        # 設置等待時間
        wait = WebDriverWait(chrome_browser, 10)
        location = (By.XPATH, '/html/body/table/tbody/tr/td/table/tbody/tr[5]/td/table/tbody/tr/td[3]/table/tbody/tr/td/table/tbody')
        try:
            tbody = wait.until(EC.presence_of_element_located(location))
            buttons = tbody.find_elements(By.XPATH, './tr/td/a')
        except Exception as e:
            print(str(e))


        time.sleep(2)

        download_list = choose_file_to_download(alphabet, buttons, childs_window)

        result_directory = 'result'
        if not os.path.isdir(result_directory):
            os.makedirs(result_directory)

        path = f'{result_directory}\\{alphabet}-result.txt'
        with open(path, 'w') as f:
            for ingredient in download_list:
                f.write(ingredient+'\n')
        
        
        


def choose_file_to_download(alphabet, buttons, childs_window):
    # list
    through = list()
    index = 0



    # buttons = buttons[:]        # 測試用

    for button in buttons:
        
        

        # 定位項目 item
        print('\n*************  ', button.text, ' *************\n')
        time.sleep(1)

        # 重置滑鼠
        actions.reset_actions()


        # 點擊item(人名)，打開pdf選擇視窗
        actions.move_to_element(button).click()
        actions.perform()


        time.sleep(1)

        # 切換到pdf選擇視窗
        chrome_browser.switch_to.window(chrome_browser.window_handles[-1])
        print("Switch to pdf page: " + str(chrome_browser.current_url) + '\n')

        target_table = fetch_target_table(chrome_browser)
        if target_table is False:
            
            print('\nPDF表格獲取失敗')
            print('結束爬蟲')
            logger.error(f'alphabet => {alphabet}, index => {index},  [ fetch_target_table ] failed.')
            return
            
        target_trs   = target_table.find_elements(By.XPATH, './tr')

        del(target_trs[0])

        
        # download = False
        latest_year = 1500
        tr_index = 1
        escape_status_string = ['Insufficient', 'not opened', 'Re-evaluation', 'No Reported Uses']
        accept_status_string = ['Published Report', 'Final Report']
        for tr in target_trs:
            time.sleep(1)
            
            year = []

            tds = tr.find_elements(By.XPATH, './td')

            ingredient = tds[0].find_element(By.XPATH, './font[@class="regtext"]')
            status     = tds[1].find_element(By.XPATH, './table/tbody/tr/td/table/tbody/tr/td/font/a')
            date       = tds[2].find_element(By.XPATH, './font')

            if ingredient.text not in through:
                through.append(ingredient.text)

            # if status.text not in accept_status_string:
            if status.text in escape_status_string:
                logger.warning(f'alphabet => {alphabet}, index => {index}, tr_index => {tr_index}')
                logger.warning(f'{status.text},  [ accept_status_string ] failed.')
                continue

            if len(date.text) > 0:
                print(f'date_{tr_index} => ', date.text)
                
                # for data like 'IJT 35(Suppl. 3):16-33, 2016'
                if ', ' in date.text:
                    year = date.text.split(', ')
                elif ',' in date.text:
                    year = date.text.split(',') 
                
                # for data like '03/08/2022'
                if len(year) > 1:
                    year = year[1]
                else:
                    year = date.text.split('/')[2]

                if int(year) >= int(latest_year):
                    latest_year = year
                    target = status
            tr_index += 1

            
        print('latest_year: ',latest_year)
            
        time.sleep(1)

        downloader(alphabet, target, index)

        time.sleep(1)


        print('\nnums: ',len(through))
        print(through)

        index += 1



        chrome_browser.close()

        chrome_browser.switch_to.window(childs_window[alphabet])

    return through







if __name__ == '__main__':
    main()