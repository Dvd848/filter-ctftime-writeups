import unittest
import logging
import time
import main
import os

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pathlib import Path
from multiprocessing import Process
from enum import Enum

GECKODRIVER_PATH = Path(__file__).parent / "geckodriver" / "geckodriver"

class PageURIs(Enum):
    LOGIN       = "/login"
    INDEX       = "/"
    FILTER      = "/filter"
    SETTINGS    = "/settings"
    TOS         = "/tos"


class TestBase(unittest.TestCase):
    PORT = 5000
    TIMEOUT = 4

    @classmethod
    def getUrl(cls, page = ''):
        return f"http://localhost:{cls.PORT}{page}"


    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        start = time.time()
        cls.logger = logging.getLogger(cls.__name__)
        cls.logger.setLevel(logging.DEBUG)

        try:
            cls.username = os.environ['WFF_USERNAME']
            cls.password = os.environ['WFF_PASSWORD']
        except KeyError:
            raise RuntimeError("Please set environment variables WFF_USERNAME, WFF_PASSWORD with valid test login credentials")

        cls.app = main.create_app()
        cls.server = Process(target = cls.app.run, kwargs = {'port': cls.PORT})
        cls.server.start()
        end = time.time()
        cls.logger.info(f"Setup f{cls.__name__} in {end - start} seconds")

    @classmethod
    def tearDownClass(cls):
        start = time.time()
        cls.server.terminate()
        cls.server.join()
        end = time.time()
        cls.logger.debug(f"Tore down f{cls.__name__} in {end - start} seconds")

    @classmethod
    def login(cls, browser, username = None, password = None):
        username = username or cls.username
        password = password or cls.password

        browser.get(cls.getUrl(PageURIs.LOGIN.value))

        email_input = WebDriverWait(browser, cls.TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "firebaseui-id-email"))
        )
        email_input.send_keys(username)
        browser.find_element_by_css_selector('button.firebaseui-id-submit').click()

        password_input = WebDriverWait(browser, cls.TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "firebaseui-id-password"))
        )
        password_input.send_keys(password)
        browser.find_element_by_css_selector('button.firebaseui-id-submit').click()

        if username == cls.username and password == cls.password:
            WebDriverWait(browser, cls.TIMEOUT).until(EC.url_to_be(cls.getUrl(PageURIs.FILTER.value)))


    def setupBrowser(self):
        options = Options()
        options.headless = True
        self.browser = webdriver.Firefox(options=options, executable_path = GECKODRIVER_PATH)
        self.addCleanup(self.browser.quit)

    def teardownBrowser(self):
        self.browser.close()


class TestLoggedOut(TestBase):
         
    def setUp(self):
        super().setUp()
        self.setupBrowser()

    def tearDown(self):
        super().tearDown()
        self.teardownBrowser()
    

    def testHomeTitle(self):
        self.browser.get(self.getUrl(PageURIs.INDEX.value))
        self.assertIn('Writeup Feed Filter', self.browser.title)

    def testNavigation(self):
        self.browser.get(self.getUrl(PageURIs.INDEX.value))
        nav_elements = self.browser.find_elements_by_xpath("/html/body//header//nav/a")
        self.assertEqual(len(nav_elements), 2)
        expected_links = [PageURIs.INDEX.value, PageURIs.LOGIN.value]
        for element in nav_elements:
            self.assertIn(element.get_attribute("href").replace(self.getUrl(), ""), expected_links)

    def testRedirectToLogin(self):
        for page in [PageURIs.FILTER.value, PageURIs.SETTINGS.value]:
            self.browser.get(self.getUrl(page))
            try:
                WebDriverWait(self.browser, self.TIMEOUT).until(EC.url_to_be(self.getUrl(PageURIs.LOGIN.value)))
            except Exception:
                self.fail(f"{page} Did not redirect to login page")
    
    def testTermsOfService(self):
        self.browser.get(self.getUrl(PageURIs.TOS.value))
        self.assertIn('Terms & Conditions', self.browser.title)

    def testLogin(self):
        self.login(self.browser)
        self.assertEqual('Filter the Writeups Feed', self.browser.find_element_by_tag_name('h1').get_attribute('textContent'))



    
class TestLoggedIn(TestBase):    
    def setUp(self):
        super().setUp()
        self.setupBrowser()
        self.login(self.browser)

    def testBasicLoggedIn(self):
        self.assertEqual('Filter the Writeups Feed', self.browser.find_element_by_tag_name('h1').get_attribute('textContent'))
        self.assertEqual(main.COOKIE_MENU_TYPE_LOGGED_IN, self.browser.get_cookie(main.COOKIE_MENU_TYPE)["value"])



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main(verbosity=2)