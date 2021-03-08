"""
百度搜索非常怪，明明昨天有效今天又失效了
fuck，直接使用webdriver吧
create bu judy 2019/12/11
"""
import time
import traceback
from sys import platform

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from idownclient.config_spiders import (webdriver_path_debian,
                                        webdriver_path_win)
from ...scoutplugbase import ScoutPlugBase


class BaiDu(ScoutPlugBase):

    def __init__(self):
        ScoutPlugBase.__init__(self)

    def _start_driver(self):
        try:
            if platform == 'linux' or platform == 'linux2':
                driver_path = webdriver_path_debian
            elif platform == 'win32':
                driver_path = webdriver_path_win
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('lang=zh_CN.UTF-8')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-dev-shm-usage')
            # chrome_options.add_argument('log-level=3')
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36")
            driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=driver_path)
            driver.set_page_load_timeout(30)
            driver.set_script_timeout(30)
            driver.implicitly_wait(30)
            return driver
        except Exception:
            self._logger.error(traceback.format_exc())

    def get_reslinks(self, query, page=1):
        """
        获取搜索结果
        """
        driver = None
        links = []
        try:
            driver: webdriver = self._start_driver()
            driver.get("https://www.baidu.com")
            driver.maximize_window()

            kw_input = driver.find_element_by_id('kw')
            kw_input.send_keys(query)

            baiduyixia = driver.find_element_by_id('su')
            baiduyixia.click()

            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "nums_text")))

            html = driver.page_source
            soup = BeautifulSoup(html, 'lxml')

            s_l = soup.find_all('div', {"class": "c-container"})
            for single_result in s_l:
                # h3_tag = single_result.find('h3')
                link_tag = single_result.find('a')
                if link_tag is None:
                    continue
                # Get the text and link
                # title = h3_tag.text
                link = link_tag.get('href')
                # desc = single_result.find('div', class_='c-abstract').text
                if not link.__contains__('http'):
                    link = 'https://www.baidu.com' + link
                links.append(link)
            return links
        except:
            self._logger.error(f"Baidu search {query} error, err:{traceback.format_exc()}")
            return None
        finally:
            if driver is not None:
                driver.close()
