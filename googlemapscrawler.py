from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


import logging
import traceback
import time
import re

MAX_WAIT = 5
MAX_RETRY = 5
SCROLL_PAUSE_TIME = 1


class GoogleMapsCrawler:

    def __init__(self):
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
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(lineno)d - %(message)s')

        # add formatter to ch
        fh.setFormatter(formatter)

        # add ch to logger
        logger.addHandler(fh)

        return logger

    # init driver
    def __get_driver(self):

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--window-size=1366,768")
        options.add_argument("--disable-notifications")
        options.add_argument('--disable_infobars')
        options.add_experimental_option(
            'prefs', {'intl.accept_languages': 'en_EB'})
        input_driver = webdriver.Chrome(chrome_options=options)

        return input_driver

    # get into rating page and sort reviews by most recent order
    def sort_by_date(self, url):
        self.driver.get(url)
        wait = WebDriverWait(self.driver, MAX_WAIT)

        # get into rating page
        try:
            time.sleep(3)
            review_page_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//button[@class=\'widget-pane-link\']')))
            review_page_btn.click()
        except Exception as e:
            self.logger.error(e)

        # open dropdown menu
        clicked = False
        tries = 0
        while not clicked and tries < MAX_RETRY:
            try:
                # if not self.debug:
                #     menu_bt = wait.until(EC.element_to_be_clickable(
                #         (By.CSS_SELECTOR, 'div.cYrDcjyGO77__container')))
                # else:
                menu_bt = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//button[@data-value=\'Sort\']')))
                menu_bt.click()

                clicked = True
                time.sleep(3)
            except Exception as e:
                tries += 1
                self.logger.warn(e)

            # failed to open the dropdown
            if tries == MAX_RETRY:
                return -1

        # click the second element of the list: Most Recent (Moi Nhat)
        try:
            recent_rating_bt = self.driver.find_elements_by_xpath(
                '//li[@role=\'menuitemradio\']')[1]
            recent_rating_bt.click()
        except Exception as e:
            self.logger.debug(e)

        # wait to load review (ajax call)
        time.sleep(3)

        return 0

    # get all reviews of a location
    def get_all_reviews(self):
        # scroll to the end of page
        self.__fast_scroll()

        # expand review content
        self.__expand_reviews()

        # parse reviews
        response = BeautifulSoup(self.driver.page_source, 'html.parser')
        rblock = response.find_all('div', class_='section-review-content')

        # get data in each review and add it to a list
        parsed_reviews = []
        for review in rblock:
            parsed_reviews.append(self.__parse(review))

        return parsed_reviews

    # get updated reviews
    def get_recent_updated_reviews(self, latest_review_id):
        # scroll and then check whether there is a reviews that has been crawled
        # if found -> get all new reviews and return as a list
        # if not -> continue scrolling and checking
        offset = 0
        while True:
            # scroll to load reviews
            self.__slow_scroll()

            # wait for loading
            time.sleep(2)

            response = BeautifulSoup(self.driver.page_source, 'html.parser')
            rblock = response.find_all('div', class_='section-review-content')

            for index, review in enumerate(rblock):
                if index >= offset:
                    if review.find(
                            'button', class_='section-review-action-menu')['data-review-id'] == latest_review_id:
                        # expand reviews
                        self.__expand_reviews()
                        return list(map(self.__parse, rblock[:rblock.index(review)]))
            offset += len(rblock)

    # scroll a part each time
    def __slow_scroll(self):
        scrollable_div = self.driver.find_element_by_css_selector(
            'div.section-layout.section-scrollbox.scrollable-y.scrollable-show')
        self.driver.execute_script(
            'arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)

    # scroll to the end of page
    def __fast_scroll(self):

        # Get the reviews div
        scrollable_div = self.driver.find_element_by_css_selector(
            'div.section-layout.section-scrollbox.scrollable-y.scrollable-show')

        # Get current height of reviews div
        last_height = self.driver.execute_script(
            "return arguments[0].scrollHeight", scrollable_div)
        self.logger.info(last_height)

        while True:
            # Scroll down
            self.driver.execute_script(
                'arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Compare new scroll height and last scroll height
            new_height = self.driver.execute_script(
                "return arguments[0].scrollHeight", scrollable_div)
            if new_height == last_height:
                # time.sleep(2)
                break
            last_height = new_height

    # expand review description
    def __expand_reviews(self):
        # use XPath to load complete reviews
        links = self.driver.find_elements_by_xpath(
            '//button[@class=\'section-expand-review blue-link\']')
        for l in links:
            l.click()
        time.sleep(2)

    # retrieve review's datas
    def __parse(self, review):

        item = {}

        # ID
        review_id = review.find(
            'button', class_='section-review-action-menu')['data-review-id']
        # Username
        username = review.find(
            'div', class_='section-review-title').find('span').text.encode('utf-8')

        # Avatar 
        avatar = review.find('img', class_='section-review-link')['src']    

        # review text could be blank
        try:
            review_text = self.__filter_string(review.find(
                'span', class_='section-review-text').text)
        except:
            review_text = None

        # Rating
        review_rating = float(review.find(
            'span', class_='section-review-stars')['aria-label'].split(' ')[1])
        # Review Date
        review_date = self.__convert_time(review.find(
            'span', class_='section-review-publish-date').text)

        # review may have image or not
        try:
            review_image_url = []
            review_image_btns = review.find(
                'div', class_='section-review-photos').find_all('button')
            for btn in review_image_btns:
                style = btn['style']
                image_url = re.search(r'\((.+?)\)', style).group(1)
                review_image_url.append(image_url)
        except:
            review_image_url = []

        item['review_id'] = review_id
        item['caption'] = review_text
        item['review_date'] = review_date
        item['rating'] = review_rating
        item['username'] = username
        item['review_image_url'] = review_image_url
        item['avatar'] = avatar

        return item

    # util function to clean special characters
    def __filter_string(self, str):
        strOut = str.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        return strOut

    def get_total_reviews(self):

        # ajax call
        time.sleep(2)

        resp = BeautifulSoup(self.driver.page_source, 'html.parser')

        return int(resp.find('div', class_='gm2-caption').text.split(' ')[0])

    def get_average_rating(self):

        # ajax call
        time.sleep(2)
        resp = BeautifulSoup(self.driver.page_source, 'html.parser')

        return float(resp.find('div', class_='gm2-display-2').text.replace('\'', ''))

    def __convert_time(self, time_str):
        lst = time_str.split(' ')

        try:
            if lst[1] == 'minute':
                review_date = datetime.now() - timedelta(minutes=1)
            elif lst[1] == 'minutes':
                review_date = datetime.now() - timedelta(minutes=int(lst[0]))
            elif lst[1] == 'hour':
                review_date = datetime.now() - timedelta(hours=1)
            elif lst[1] == 'hours':
                review_date = datetime.now() - timedelta(hours=int(lst[0]))
            elif lst[1] == 'day':
                review_date = datetime.now() - timedelta(days=1)
            elif lst[1] == 'days':
                review_date = datetime.now() - timedelta(days=int(lst[0]))
            elif lst[1] == 'week':
                review_date = datetime.now() - timedelta(weeks=1)
            elif lst[1] == 'weeks':
                review_date = datetime.now() - timedelta(weeks=int(lst[0]))
            elif lst[1] == 'month':
                review_date = datetime.now() + relativedelta(months=-1)
            elif lst[1] == 'months':
                review_date = datetime.now() + \
                    relativedelta(months=-int(lst[0]))
            elif lst[1] == 'year':
                review_date = datetime.now() + relativedelta(years=- 1)
            elif lst[1] == 'years':
                review_date = datetime.now() + \
                    relativedelta(years=- int(lst[0]))
        except Exception as e:
            self.logger.error(e)

        return review_date.strftime("%d-%m-%Y")
