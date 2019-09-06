"""
使用selenium模拟浏览器登陆tweet
调试的时候使用有界面的浏览器，
运行时可以使用无界面的浏览器
create by swm 20180919
now modify by swm 20181108
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from functools import wraps
import time
import re


class TweetLogin(object):

    def __init__(self, account, pwd):
        self.account = account
        self.pwd = pwd
        self.chrome = "D:\swmdata\idwon_test_data_bak\idownresourceslib\lib\chrome\chromedriver.exe"

    def doit(self):
        chrome_options = Options()
        # 无头
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument('lang=zh_CN.UTF-8')
        # chrome_options.add_argument("--window-size=1920x1080")
        # chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36")
        # 禁用js
        chrome_options.add_experimental_option("prefs", {'profile.managed_default_content_settings.javascript': 2})
        chrome_driver = self.chrome
        # driver = webdriver.Chrome(executable_path=chrome_driver)
        driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        # 1、打开登陆界面
        # driver.get("https://accounts.google.com/AccountChooser?service=mail&continue=https://mail.google.com/mail/")
        # no js
        driver.get("https://twitter.com/login")
        driver.maximize_window()
        # 输入账号密码然后下一步
        # accountnumber = driver.find_element_by_css_selector("#identifierId")
        # nojs
        accountnumber = driver.find_element_by_name('session[username_or_email]')
        accountnumber.send_keys(self.account)
        # accountnumber.send_keys(Keys.ENTER)
        try:
            # passwd = WebDriverWait(driver, 10).until(
            #     EC.text_to_be_present_in_element((By.XPATH, '//*[contains(concat( " ", @class, " " ), concat( " ", "daaWTb", " " ))]'), "忘记了密码？")
            # )
            # passwd = driver.find_element_by_css_selector(".zHQkBf")
            # nojs
            passwd = driver.find_element_by_name('session[password]')
            passwd.send_keys(self.pwd)
            passwd.send_keys(Keys.ENTER)
        except Exception as err:
            print("Error:{}\n跳转密码界面失败".format(err))
        # 跳转gmail登陆后的界面
        # 后面要增加手机验证码的情况,现在

        time.sleep(5)
        driver.quit()


if __name__ == '__main__':
    account = "sepjudy@gmail.com"
    pwd = "ADSZadsz123"
    gg = TweetLogin(account, pwd)
    gg.doit()

