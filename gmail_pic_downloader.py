from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import requests
import os
from time import sleep
import random
import re

LINK_REGEX = '(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])?'
SO_LOGIN = 'https://stackoverflow.com/users/login'
USED_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0'
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:79.0) Gecko/20100101 Firefox/79.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 7.1.2; AFTMM Build/NS6265; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/70.0.3538.110 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/601.7.7 (KHTML, like Gecko) Version/9.1.2 Safari/601.7.7',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/601.5.17 (KHTML, like Gecko) Version/9.1 Safari/601.5.17',
]

COOKIES = {
    'NID': '',
    'CONSENT': '',
    '1P_JAR': '',
    'SID': '',
    '__Secure-3PSID': '',
    'HSID': '',
    'SSID': '',
    'APISID': '',
    'SAPISID': '',
    '__Secure-3PAPISID': '',
    'SIDCC': '',
    '__Secure-3PSIDCC': '',
}

HEADERS = {
    'User-Agent': '',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://contacts.google.com/',
    'X-Same-Domain': '1',
    'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
    'Origin': 'https://contacts.google.com',
    'DNT': '1',
    'Connection': 'keep-alive',
    'TE': 'Trailers',
}


class GmailPicDownloader:
    """
    Download profile picture of a Gmail account. If a webdriver already exists pass it as an argument. Firefox is preferred
    as it was used for developing this script. If webdriver doesn't exists or you want to create a new one, you must pass the 
    address of geckodriver for Firefox as key argument.
    username and password arguments are for logging in to gmail.
    target_email is the profile which its picture will be downloaded.
    This script logs in to gmail through stackoverflow then uses the cookies to mimic a HTTPS request for photo URL.

    """
    def __init__(self, username, password, target_email='', firefox_executable_path='./geckodriver', driver=None):
        self.username = username
        self.password = password
        self.target_email = target_email
        self.user_agent = random.choice(USER_AGENTS)
        if driver:
            self.driver = driver
        else:
            profile = webdriver.FirefoxProfile()
            profile.set_preference('general.useragent.override', USED_AGENT)
            self.driver = webdriver.Firefox(executable_path=firefox_executable_path, firefox_profile=profile)
        self.wait = WebDriverWait(self.driver, 20)
    
    def __exit__(self):
        self.driver.close()


    def set_target_email(self, email):
        """
        Set the target email address.
        """
        self.target_email = email

    def login_gmail(self):
        """
        Login to gmail using Stackoverflow website then going to mail.google.com. The reason for this
        is google doesn't allow direct login to gmail using Selenium.
        """
        self.driver.get(SO_LOGIN)
        google_login = self.driver.find_element_by_css_selector('button.s-btn__icon:nth-child(1)')
        google_login.click()
        self.wait.until(expected_conditions.element_to_be_clickable((By.XPATH, '//*[@id="identifierNext"]')))
        login_field = self.driver.find_element_by_xpath('//*[@id="identifierId"]')
        login_field.send_keys(self.username)
        next_button = self.driver.find_element_by_xpath('//*[@id="identifierNext"]')
        next_button.click()
        self.wait.until(expected_conditions.element_to_be_clickable((By.XPATH, '//*[@type="password"]')))
        password_field = self.driver.find_element_by_xpath('//*[@type="password"]')
        password_field.send_keys(self.password)
        next_button = self.driver.find_element_by_xpath('//*[@id="passwordNext"]')
        next_button.click()
        sleep(1)
        self.driver.get('https://mail.google.com/#inbox')
        sleep(1)


    def get_new_cookies(self, cookies):
        """
        Extracts required cookies from webdriver cookies.
        """
        new_cookies = {}
        for k, v in COOKIES.items():
            new_cookies[k] = cookies[k]
        return new_cookies

    def get_img_url_using_request(self):
        """
        This method uses cookies from webdriver to mimic a real HTTPS request for getting profile picture URL
        """
        cookies = { c["name"]: c["value"] for c in self.driver.get_cookies() }
        req_cookies = self.get_new_cookies(cookies)
        HEADERS['User-Agent'] = self.user_agent
        data = {
            'f.req': f'[[["WWoa8","[null,\\"{self.target_email}\\",13,[1,4,2]]",null,"generic"]]]',
        }
        response = requests.post('https://contacts.google.com/_/SocialPeopleHovercardUi/data/batchexecute', headers=HEADERS, cookies=req_cookies, data=data)
        m = re.search('\S{28}:\d{13}', response.text) # finding a required string used in POST data
        data['at'] = m.group(0)
        response = requests.post('https://contacts.google.com/_/SocialPeopleHovercardUi/data/batchexecute', headers=HEADERS, cookies=req_cookies, data=data)
        m = re.search(LINK_REGEX, response.text) # finding url of photo
        print('URL: ', m.group(0))
        return m.group(0)


    def profile_has_pic(self, url):
        """
        If a google user doesn't have a photo, a default picture is used. This method
        checks if the image url is not the default picture url.
        """
        if 'default-user' in url or 'AAAAAAAAAAA' in url:
            return False
        return True
        
    def download_profile_pic(self):
        """
        Gets image url and if the target user had profile picture, downloads the full size image.
        """
        url = self.get_img_url_using_request()
        if self.profile_has_pic(url):
            img = requests.get(url)
            with open(os.path.dirname(os.path.abspath(__file__)) +  '/' + self.target_email + '.png', 'wb') as fp:
                fp.write(img.content)
                print('Image Downloaded!')
        else:
            print('User doesn\'t a profile picture!')




    
    def close(self):
        """
        Close the browser.
        """
        self.driver.close()



def main():
    target_email = input('Enter Mail: ') # eg. test@gmail.com
    downloader = GmailPicDownloader(username='username', password='password', target_email=target_email)
    downloader.login_gmail()
    downloader.download_profile_pic()
    downloader.close()

if __name__ == '__main__':
    main()