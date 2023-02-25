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
from selenium.common.exceptions import WebDriverException

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
    PORT            = 5000
    TIMEOUT         = 10
    TIMEOUT_LONG    = 15

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
            cls.username = os.environ['WFF_TEST_USERNAME']
            cls.password = os.environ['WFF_TEST_PASSWORD']
        except KeyError:
            msg = "Please set environment variables WFF_TEST_USERNAME, WFF_TEST_PASSWORD with valid test login credentials"
            raise RuntimeError(msg) from None

        cls.setupBrowser()
        cls.app = main.create_app()
        cls.server = Process(target = cls.app.run, kwargs = {'port': cls.PORT})
        cls.server.start()
        end = time.time()
        cls.logger.info(f"Setup f{cls.__name__} in {end - start} seconds")

    @classmethod
    def tearDownClass(cls):
        start = time.time()
        cls.teardownBrowser()
        cls.server.terminate()
        cls.server.join()
        end = time.time()
        cls.logger.debug(f"Tore down f{cls.__name__} in {end - start} seconds")

    @classmethod
    def login(cls, username = None, password = None):
        username = username or cls.username
        password = password or cls.password

        cls.browser.get(cls.getUrl(PageURIs.LOGIN.value))

        email_input = WebDriverWait(cls.browser, cls.TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "firebaseui-id-email"))
        )
        email_input.send_keys(username)
        cls.browser.find_element(By.CSS_SELECTOR, 'button.firebaseui-id-submit').click()

        password_input = WebDriverWait(cls.browser, cls.TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "firebaseui-id-password"))
        )
        password_input.send_keys(password)
        cls.browser.find_element(By.CSS_SELECTOR, 'button.firebaseui-id-submit').click()

        if username == cls.username and password == cls.password:
            WebDriverWait(cls.browser, cls.TIMEOUT).until(EC.url_to_be(cls.getUrl(PageURIs.FILTER.value)))

    @classmethod
    def setupBrowser(cls):
        options = Options()
        options.add_argument("--headless")

        kwargs = {}
        if GECKODRIVER_PATH.exists():
            kwargs["executable_path"] = GECKODRIVER_PATH
        
        try:
            cls.browser = webdriver.Firefox(options=options, **kwargs)
        except WebDriverException as e:
            print(f"ERROR: {str(e)}\n")
            if "geckodriver" in str(e):
                raise FileNotFoundError(
                    f"This script has a dependency on geckodriver, please add it to the PATH or to {GECKODRIVER_PATH.absolute()}") from e
            else:
                raise e

    @classmethod
    def teardownBrowser(cls):
        cls.browser.quit()

    def screenshot(self, name = "screenshot"):
        path = "./tmp/screenshots/"
        Path(path).mkdir(parents = True, exist_ok = True)
        self.browser.save_screenshot(f"{path}{name}.png")



class TestLoggedOut(TestBase):

    def testHomeTitle(self):
        self.browser.get(self.getUrl(PageURIs.INDEX.value))
        self.assertIn('Writeup Feed Filter', self.browser.title)

    def testNavigation(self):
        self.browser.get(self.getUrl(PageURIs.INDEX.value))
        nav_elements = self.browser.find_elements(By.XPATH, "/html/body//header//nav/a")
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

    

class TestLogin(TestBase):
    def testLogin(self):
        self.login()
        self.assertEqual('Filter the Writeups Feed', self.browser.find_element(By.TAG_NAME, 'h1').get_attribute('textContent'))

    @unittest.skip("Avoid lockout due to multiple failed attempts")
    def testBadCredentials(self):
        self.login(self.username, self.password+self.password)
        self.browser.implicitly_wait(3) # seconds
        self.browser.get(self.getUrl(PageURIs.LOGIN.value))
        try:
            WebDriverWait(self.browser, self.TIMEOUT).until(EC.url_to_be(self.getUrl(PageURIs.LOGIN.value)))
        except Exception:
            self.fail()
    
class TestLoggedInFilter(TestBase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.login()
        
    def setUp(self):
        self.removeAllNames()
        self.browser.get(self.getUrl(PageURIs.FILTER.value))
        self.waitForFilter()

    def waitForFilter(self):
        WebDriverWait(self.browser, self.TIMEOUT_LONG).until(EC.visibility_of_element_located((By.XPATH, "//h1")))
        WebDriverWait(self.browser, self.TIMEOUT_LONG).until(EC.invisibility_of_element_located((By.ID, "ajax_loader")))
    
    def getRemoveButton(self):
        WebDriverWait(self.browser, self.TIMEOUT_LONG).until(EC.visibility_of_element_located((By.CLASS_NAME, "remove_ctf_name")))
        return self.browser.find_elements(By.CLASS_NAME, "remove_ctf_name")

    def saveChanges(self):
        WebDriverWait(self.browser, self.TIMEOUT).until(EC.element_to_be_clickable((By.ID, "save_button"))).click()
        WebDriverWait(self.browser, self.TIMEOUT).until(
            EC.visibility_of_element_located((By.XPATH, "/html/body//main//div[@id='modal_success']//button"))).click()
        #WebDriverWait(self.browser, self.TIMEOUT).until(EC.element_to_be_clickable((By.ID, "save_button")))
        WebDriverWait(self.browser, self.TIMEOUT).until(EC.invisibility_of_element_located((By.CLASS_NAME, "modal-backdrop")))

    def removeAllNames(self):
        self.browser.get(self.getUrl(PageURIs.FILTER.value))
        remove_buttons = self.getRemoveButton()
        for button in remove_buttons:
            button.click()
        self.saveChanges()

    def getCtfNameInputs(self):
        WebDriverWait(self.browser, self.TIMEOUT_LONG).until(EC.visibility_of_element_located((By.CLASS_NAME, "ctf_name_input")))
        return self.browser.find_elements(By.CLASS_NAME, 'ctf_name_input')

    def addInput(self):
        WebDriverWait(self.browser, self.TIMEOUT).until(EC.element_to_be_clickable((By.ID, "add_button"))).click()

    def enterCtfName(self, index: int, value: str):
        inputs = self.getCtfNameInputs()
        if (index > len(inputs) - 1):
            for _ in range(len(inputs) - 1, index):
                self.addInput()
        inputs = self.getCtfNameInputs()
        inputs[index].send_keys(value)

    # ---
 
    def testBasicLoggedIn(self):
        self.assertEqual('Filter the Writeups Feed', self.browser.find_element(By.TAG_NAME, 'h1').get_attribute('textContent'))
        self.assertEqual(main.COOKIE_MENU_TYPE_LOGGED_IN, self.browser.get_cookie(main.COOKIE_MENU_TYPE)["value"])

    def testAddRefresh(self):
        name = "MyCTF"
        index = 0
        self.enterCtfName(index, name)
        self.saveChanges()

        self.browser.refresh()
        self.waitForFilter()

        inputs = self.getCtfNameInputs()
        self.assertEqual(name, inputs[index].get_attribute("value"))

    def testAddRefreshRemove(self):
        name = "MyCTF"
        index = 0
        self.enterCtfName(index, name)
        self.saveChanges()

        self.browser.refresh()
        self.waitForFilter()

        remove_buttons = self.getRemoveButton()
        remove_buttons[index].click()
        self.saveChanges()

        self.browser.refresh()
        self.waitForFilter()

        inputs = self.getCtfNameInputs()
        self.assertEqual("", inputs[index].get_attribute("value"))

    def testAddMultipleRefresh(self):
        names = ["MyCTF{}".format(i) for i in range(3)]
        for i, name in enumerate(names):
            self.enterCtfName(i, name)
        self.saveChanges()

        self.browser.refresh()
        self.waitForFilter()

        inputs = self.getCtfNameInputs()
        self.assertEqual(len(names), len(inputs))
        for i, name in enumerate(names):
            self.assertEqual(name, inputs[i].get_attribute("value"))

    def testAddDuplicate(self):
        names = ["MyCTF" for _ in range(3)]
        for i, name in enumerate(names):
            self.enterCtfName(i, name)
        self.saveChanges()

        self.browser.refresh()
        self.waitForFilter()

        inputs = self.getCtfNameInputs()
        unique_names = set(names)
        self.assertEqual(len(unique_names), len(inputs))
        for i in range(len(unique_names)):
            self.assertIn(inputs[i].get_attribute("value"), unique_names)

    def testAddMaxInputs(self):
        self.removeAllNames()
        for _ in range(main.MAX_CTF_ENTRIES):
            self.addInput()
        WebDriverWait(self.browser, self.TIMEOUT).until(EC.invisibility_of_element_located((By.ID, "add_button")))




if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main(verbosity=2)