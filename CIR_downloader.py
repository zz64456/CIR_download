from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
import logging
import time, os, sys, math
import tkinter as tk
from download import Downloader
from loggy import setup_logging
from thread import MyThread



first = 'Null'
last  = 'Null'



def check_main_path():
    try:
        if not os.path.isdir(main_path):
            os.makedirs(main_path)
    except FileNotFoundError:
        print("\n請輸入目標資料夾。")
        return False
    return True


def download(*args):

    global main_path
    main_path = args[0]
    logger = args[1]
    target_alphabet = args[2]
    start = args[3].strip()
    if check_main_path() is False:
        download_label['text'] = '所需資訊不足，請輸入目標資料夾路徑。'
        print("\n所需資訊不足，請輸入目標資料夾路徑。")
        return

    download_label['text'] = f'[{target_alphabet}] 下載中...'

    D = Downloader(main_path, logger)

    # web driver init
    chrome_browser = D.initialize_parser()

    # Ctrl+C 終止程序
    # signal.signal(signal.SIGINT, signal_handler)

    alphabets_div = chrome_browser.find_element(By.CLASS_NAME, 'glossary ')
    alphabets = alphabets_div.find_elements(By.CLASS_NAME, 'glossary-letter')

    # 選取提示
    alphabet_label['text'] = target_alphabet
    # 打開字母分頁
    childs_window = D.open_alphabet_tabs(chrome_browser, alphabets, target_alphabet)

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

        offset = 1
        if len(start) > 0:
            print(f'\n Searching for [ {start} ] ...')
            offset = get_index_from_ingredient(buttons, start)
        
        if not offset:
            download_label['text'] = '找不到資料，請重新輸入。'

        choose_file_to_download(chrome_browser, D, alphabet, buttons, childs_window, offset)

        print(f'\n\n...................................')
        print(f'\n................................... [{alphabet}] 下載完成。')
        brief_download_list()
        print('\n\n------------- 請選擇下一個字母 -------------')
        download_label['text'] = f'現在可以選擇下一個字母'

    chrome_browser.quit()
        
        

def choose_file_to_download(chrome_browser, D, alphabet, buttons, childs_window, offset):
    # list
    through = list()
    index = 0

    offset = int(offset) - 1
    result_path = f'{D.main_path}\\{alphabet}-result.txt'
    if int(offset) == 0:
        reset_result_file(alphabet)
    else:
        result_path = f'{D.main_path}\\{alphabet}-result-{offset+1}.txt'

    buttons = buttons[offset:]

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
            D.logger.error(f' [ fetch_target_table ]')
            D.logger.critical(f'  [ Ingredient ]  =>  {button.text}')
            D.logger.critical(f'  [    Index   ]  =>  {index}')
            D.logger.critical(f'  [    Fail    ]') # 沒下載
            fail_txt(f'{D.main_path}\\fail.txt', ingredient.text)
            continue
            
        target_trs   = target_table.find_elements(By.XPATH, './tr')
        del(target_trs[0])
        
        latest_year = 1500
        tr_index = 1
        escape_status_string = ['Insufficient', 'not opened', 'Re-evaluation', 'No Reported Uses', 'Use Not Supported',
                                'Report Terminated', 'Re-evaluation - Report not opened', 'Use Not Supported - Conditional',
                                'Re-evaluation - Re-opened']
        accept_status_string = ['Published Report', 'Final Report', 'Scientific Literature Review', 'Published Re-review Not Opened',
                                'Tentative Report']
        ingredient_name = ''
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
                D.logger.warning(f'  [ Ingredient ]  =>  {ingredient.text}  |   [    Index   ]  =>  {index}')
                if status.text not in escape_status_string:
                    D.logger.warning(f'  [ New Status ]  =>  {status.text}')
                    # TODO 
                    # Turn escape_status_string list into txt file to load
                    # And add new status into escape_status_string
                D.logger.critical(f' [ Skip ]') # 有可能沒下載
                fail_txt(f'{D.main_path}\\skip.txt', ingredient.text)
                continue

            if len(date.text) > 0:
                print(f'Date {tr_index}  => ', date.text)
                
                # for data like 'IJT 35(Suppl. 3):16-33, 2016'
                if ', ' in date.text:
                    year = date.text.split(', ')
                elif ',)' in date.text: # IJT 23 (Suppl.2:49-54,)2004
                   year = date.text.split(',)') 
                elif ',' in date.text:
                    year = date.text.split(',') 
                
                # for data like '03/08/2022'
                if len(year) > 1:
                    year = year[1]
                else:
                    year = date.text.split('/')[2]

                if not year.isdigit():
                    D.logger.warning(f'  [ Ingredient ]  =>  {ingredient.text}')
                    D.logger.warning(f'  [ New Date ]  =>  {date.text}')
                    D.logger.critical(f'  [   Skip   ]') # 有可能沒下載
                    fail_txt(f'{D.main_path}\\skip.txt', ingredient.text)
                    continue

                if int(year) >= int(latest_year):
                    latest_year = year
                    target = status
                    ingredient_name = ingredient.text
            tr_index += 1


            
        print('Latest Year: ', latest_year)
        print('\nnums: ', len(through))


        if latest_year != 1500:
            time.sleep(1)
            file_name = D.downloader(alphabet, target, ingredient_name)
            time.sleep(1)
            
            with open(result_path, 'a') as f:
                f.write(ingredient_name + ',' + file_name + '\n')
        else:
            D.logger.warning('  [ No PDF ]  =>  ------------------')
            fail_txt(f'{D.main_path}\\skip.txt', ingredient.text)


        index += 1

        chrome_browser.close()

        chrome_browser.switch_to.window(childs_window[alphabet])

    return through


def get_index_from_ingredient(buttons, ingredient):
    for index, item in enumerate(buttons):
        if item.text == ingredient:
            return index +1 
    return False


def fail_txt(path, ingredient):
    if not os.path.isfile(path):
        open(path, "x")
        
    with open(path, 'a') as f:
        f.write(ingredient + '\n')


def brief_download_list():
    print('\n此次爬蟲...\n')
    print('　第一筆資料為：　　',first)
    print('最後一筆資料為：　　',last)

def signal_handler(signal='', frame=''):
    print('\n\n------------- 您終止了爬蟲程序 -------------')
    brief_download_list()
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
    window.geometry("700x250")
    # 標示文字
    global download_label
    download_label = tk.Label(window, text = 'Download path:')
    download_label.grid(row=0, column=0, columnspan=10, padx=5, pady=2)

    # 輸入欄位
    entry = tk.Entry(window, # 輸入欄位所在視窗
        font=('Arial 10'),
        width = 60)
    entry.grid(row=1, column=0, columnspan=10, padx=5, pady=5)

    # 建立字母按鈕
    alphabets = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
    cnt = 0
    for alphabet in alphabets:
        bg = 'grey'
        if cnt%2 == 1:
            bg = '#c9c7c7'
        entry_btn = tk.Button(window, # 按鈕所在視窗
            text = alphabet,  # 顯示文字
            height= 2,
            width = 5,
            bg=bg,
            command=lambda alphabet=alphabet: MyThread(download, entry.get(), logger, alphabet, start.get())) # 按下按鈕所執行的函數

        r = math.floor(cnt / 7) + 3
        c = cnt % 7
        entry_btn.grid(row=r, column=c, padx=2, pady=3)

        cnt += 1

    # 指定開始位置
    start_label = tk.Label(window, text = 'From', font='Arial 10')
    start_label.grid(row=6, column=4, columnspan=4, padx=5, pady=2)
    default_value = tk.StringVar()
    default_value.set("")
    start = tk.Entry(window, 
        font=('Arial 11'),
        width=40,
        justify='center',
        textvariable=default_value
        )
    start.grid(row=6, column=6, columnspan=5, padx=5, pady=5)

    global alphabet_label
    alphabet_label = tk.Label(window, text = 'A', font='Arial 72', bg='green')
    alphabet_label.grid(row=2, column=10, rowspan=5, ipadx=30, padx=60, pady=20)

    window.protocol("WM_DELETE_WINDOW", signal_handler)

    window.mainloop()



if __name__ == '__main__':
    main()