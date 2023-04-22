from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os, time

class Downloader:

    def __init__(self, main_path, logger) -> None:
        self.main_path = main_path
        self.logger    = logger
    

    def initialize_parser(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option('detach', True) # 控制瀏覽器自動關閉
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        options.add_experimental_option('prefs', {
            "download.default_directory": self.main_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        })

        chrome_browser = webdriver.Chrome('./chromedriver', options=options)
        chrome_browser.maximize_window()
        chrome_browser.get('https://www.cir-safety.org/ingredients') # CIR - INGREDIENTS 網頁
        return chrome_browser



    def open_alphabet_tabs(self, chrome_browser, alphabets):
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


    def fetch_target_table(self, chrome_browser, try_times = 3, fail_times = 0):
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
                self.logger.error(str(e))
        return target_table

    

    def downloader(self, alphabet, target, index):

        file_name = target.get_attribute('href').split('.pdf')[0].split('/')[-1]
        print(f'\nfilename =>   [ {file_name}.pdf ]')

        default_file_path     = f'{self.main_path}\\{file_name}.pdf'
        destination_directory = f'{self.main_path}\\pdf\\{alphabet}'
        file_path             = f'{destination_directory}\\{file_name}.pdf'

        if not os.path.isdir(destination_directory):
            os.makedirs(destination_directory)

        if not os.path.isfile(file_path):
            print("\nIt's a new file. Start to Download it.")
            target.click()
            finish = False
            t = 0
            timeout = 15
            while finish is not True and t < timeout:
                finish = False
                t += 1
                print('not yet..')
                time.sleep(1)
                if os.path.isfile(default_file_path):
                    finish = True
            try:
                os.replace(default_file_path, file_path)
                print('Download is finished')
            except Exception as e:
                print(e)
                self.logger.error(f'alphabet => {alphabet}, ingredient => {index},  Replace failed.')
            print('\nFile added !')
        else:
            print("\nExists already")



    


    