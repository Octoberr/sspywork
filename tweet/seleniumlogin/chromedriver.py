"""
使用selenium模拟浏览器登陆tweet
调试的时候使用有界面的浏览器，
运行时可以使用无界面的浏览器
create by swm 20180919
now modify by swm 20181108
"""
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from functools import wraps
import time
import re
from bs4 import BeautifulSoup


class TweetLogin(object):

    def __init__(self, account, pwd):
        self.account = account
        self.pwd = pwd
        self.chrome = "D:\\gitcode\\idown_new\\resource\\webdriver\\chromedriver.exe"

    def doit(self):
        chrome_options = ChromeOptions()
        # 无头
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('lang=zh_CN.UTF-8')
        # chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36")
        # 禁用js
        # chrome_options.add_experimental_option("prefs", {'profile.managed_default_content_settings.javascript': 2})
        chrome_driver = self.chrome
        # driver = webdriver.Chrome(executable_path=chrome_driver)
        driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        # 1、打开登陆界面
        # driver.get("https://accounts.google.com/AccountChooser?service=mail&continue=https://mail.google.com/mail/")
        # no js
        driver.get("https://www.baidu.com")
        # driver.maximize_window()
        # 输入账号密码然后下一步
        # accountnumber = driver.find_element_by_css_selector("#identifierId")
        # nojs
        input = driver.find_element_by_id('kw')
        input.send_keys('anthem site:17173.com')
        baiduyixia = driver.find_element_by_id('su')
        baiduyixia.click()

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "nums_text")))



        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')

        s_l = soup.find_all('div', {"class": "result"})
        for single_result in s_l:
            h3_tag = single_result.find('h3')
            link_tag = single_result.find('a')

            # Get the text and link
            # title = h3_tag.text
            link = link_tag.get('href')
            # desc = single_result.find('div', class_='c-abstract').text
            print(link)

        # 下一页
        nextpage = driver.find_element_by_class_name('n')
        nextpage.click()
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')

        s_l = soup.find_all('div', {"class": "result"})
        for single_result in s_l:
            h3_tag = single_result.find('h3')
            link_tag = single_result.find('a')

            # Get the text and link
            # title = h3_tag.text
            link = link_tag.get('href')
            # desc = single_result.find('div', class_='c-abstract').text
            print(link)

        time.sleep(5)
        driver.quit()


if __name__ == '__main__':
    account = "sepjudy@gmail.com"
    pwd = "ADSZadsz123"
    gg = TweetLogin(account, pwd)
    gg.doit()

