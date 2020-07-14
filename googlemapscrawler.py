from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


import logging
import traceback
import time

MAX_WAIT = 20
MAX_RETRY = 10

class GoogleMapsCrawler:

    def __init__(self, debug = False):
        self.debug = debug
        self.driver = self.__get_driver()
        self.logger = self.__get_logger()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
        
        self.driver.close()
        self.driver.quit()

        return True

    def __get_logger(self):
        # create logger
        logger = logging.getLogger('ggmaps-crawler')
        logger.setLevel(logging.DEBUG)

        # create console handler and set level to debug
        fh = logging.FileHandler('ggmaps-crawler.log')
        fh.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # add formatter to ch
        fh.setFormatter(formatter)

        # add ch to logger
        logger.addHandler(fh)

        return logger

    def __get_driver(self, debug=False):

        options = Options()
        # if not self.debug:
        #     options.add_argument("--headless")
        options.add_argument("--window-size=1366,768")
        options.add_argument("--disable-notifications")
        options.add_experimental_option('prefs',{'intl.accept_languages' : 'en_EB'})
        input_driver = webdriver.Chrome(chrome_options=options)

        return input_driver
        
    def sort_by_date(self, url):
        self.driver.get(url)
        wait = WebDriverWait(self.driver, MAX_WAIT)

        # get into rating page
        try:
            time.sleep(5)
            review_page_btn = self.driver.find_element_by_xpath('//button[@class=\'widget-pane-link\']')
            review_page_btn.click()
        except Exception as e:
            self.logger.error(e)
            self.logger.debug('Failed to click review page button!')

        # open dropdown menu
        clicked = False
        tries = 0
        while not clicked and tries < MAX_RETRY:
            try:
                if not self.debug:
                    menu_bt = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.cYrDcjyGO77__container')))
                else:
                    menu_bt = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@data-value=\'Sort\']')))
                menu_bt.click()

                clicked = True
                time.sleep(5)
            except Exception as e:
                tries += 1
                self.logger.debug(e)
                self.logger.warn('Failed to click recent button')

            # failed to open the dropdown
            if tries == MAX_RETRY:
                return -1
        
        # click the second element of the list: Most Recent (Moi Nhat)
        recent_rating_bt = self.driver.find_elements_by_xpath('//li[@role=\'menuitemradio\']')[1] 
        recent_rating_bt.click()

        # wait to load review (ajax call)
        time.sleep(5)

        return 0
    