from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
import logging
import time, os, sys, signal, threading
import tkinter as tk
from download import Downloader
from loggy import setup_logging
from thread import MyThread



first = 'Null'
last  = 'Null'



def check_main_path():
    if not os.path.isdir(main_path):
        os.makedirs(main_path)



def download(path, logger):

    global main_path
    main_path = path
    check_main_path()

    D = Downloader(main_path, logger)

    # web driver init
    chrome_browser = D.initialize_parser()

    # Ctrl+C 終止程序
    # signal.signal(signal.SIGINT, signal_handler)

    alphabets_div = chrome_browser.find_element(By.CLASS_NAME, 'glossary ')
    alphabets = alphabets_div.find_elements(By.CLASS_NAME, 'glossary-letter')

    # 打開字母分頁
    childs_window = D.open_alphabet_tabs(chrome_browser, alphabets)

    # TODO args[2] - alphabet

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

        # TODO args[3] - button

        reset_result_file(alphabet)

        download_list = choose_file_to_download(chrome_browser, D, alphabet, buttons, childs_window)

    chrome_browser.quit()
        
        

def choose_file_to_download(chrome_browser, D, alphabet, buttons, childs_window):
    # list
    through = list()
    index = 0

    buttons = buttons[36:]        # 測試用

    actions = ActionChains(chrome_browser)

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

        target_table = D.fetch_target_table(chrome_browser)
        if target_table is False:
            print('\nPDF表格獲取失敗')
            print('結束爬蟲')
            D.logger.error(f'alphabet => {alphabet}, index => {index},  [ fetch_target_table ] failed.')
            return
            
        target_trs   = target_table.find_elements(By.XPATH, './tr')
        del(target_trs[0])
        
        latest_year = 1500
        tr_index = 1
        escape_status_string = ['Insufficient', 'not opened', 'Re-evaluation', 'No Reported Uses', 'Use Not Supported']
        accept_status_string = ['Published Report', 'Final Report', 'Scientific Literature Review']
        new_status_string = []
        for tr in target_trs:
            time.sleep(1)
            
            year = []

            tds = tr.find_elements(By.XPATH, './td')

            ingredient = tds[0].find_element(By.XPATH, './font[@class="regtext"]')
            status     = tds[1].find_element(By.XPATH, './table/tbody/tr/td/table/tbody/tr/td/font/a')
            date       = tds[2].find_element(By.XPATH, './font')

            if ingredient.text not in through:
                if len(through) == 0:
                    global first
                    first = ingredient.text
                through.append(ingredient.text)
                global last
                last = ingredient.text

            # Skip unknown status
            if status.text not in accept_status_string:
                if status.text not in escape_status_string:
                    new_status_string.append(status.text)
                continue

            if len(date.text) > 0:
                print(f'date_{tr_index}  => ', date.text)
                
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

        # New Status Found
        if len(new_status_string) > 0:
            for status in new_status_string:
                D.logger.warning(f'  Ingredient  =>  {ingredient.text} , tr_index => {tr_index}')
                D.logger.warning(f'  [ New Status ]  =>  {status}')

            
        print('latest_year: ',latest_year)
            
        time.sleep(1)

        D.downloader(alphabet, target, index)

        time.sleep(1)


        print('\nnums: ',len(through))
        # print(through)

        index += 1

        result_path = f'{D.main_path}\\{alphabet}-result.txt'
        with open(result_path, 'a') as f:
            f.write(ingredient.text+'\n')


        chrome_browser.close()

        chrome_browser.switch_to.window(childs_window[alphabet])

    return through




def signal_handler(signal='', frame=''):
    print('\n\n------------- 您終止了爬蟲程序 -------------')
    print('\n此次爬蟲...\n')
    print('　第一筆資料為：　　',first)
    print('最後一筆資料為：　　',last)
    sys.exit(0)


def reset_result_file(alphabet):
    result_path = f'{main_path}\\{alphabet}-result.txt'
    if os.path.isfile(result_path):
        os.remove(result_path)




def main():
    # logging
    logDir = 'crawler'
    loggerName = logDir+'allLogger'
    setup_logging(logDir)
    logger = logging.getLogger(loggerName)


    window = tk.Tk()
    window.title('CIR parser')
    window.geometry("500x100")
    # 標示文字
    label = tk.Label(window, text = 'Download path:')
    label.pack()

    # 輸入欄位
    entry = tk.Entry(window, # 輸入欄位所在視窗
        width = 50) # 輸入欄位的寬度
    entry.pack(pady = 10)

    # 建立按鈕
    entry_btn = tk.Button(window, # 按鈕所在視窗
        text = 'Start',  # 顯示文字
        command=lambda: MyThread(download, entry.get(), logger)) # 按下按鈕所執行的函數
    # 以預設方式排版按鈕
    entry_btn.pack(side='top', pady=10)

    window.protocol("WM_DELETE_WINDOW", signal_handler)

    window.mainloop()



if __name__ == '__main__':
    main()