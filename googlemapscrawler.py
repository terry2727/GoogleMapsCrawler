from selenium.webdriver.chrome.options import Options
from selenium import webdriver

import logging
import traceback

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
        
        