import unittest
import main
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from pathlib import Path
from multiprocessing import Process


GECKODRIVER_PATH = Path(__file__).parent / "geckodriver" / "geckodriver"

class TestSite(unittest.TestCase):
    PORT = 5001

    @classmethod
    def getServerUrl(cls):
        return f"http://localhost:{cls.PORT}/"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.app = main.create_app()
        cls.server = Process(target = cls.app.run, kwargs = {'port': cls.PORT})
        cls.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        cls.server.join()

    def setUp(self):
        options = Options()
        options.headless = True
        self.browser = webdriver.Firefox(options=options, executable_path = GECKODRIVER_PATH)
        self.addCleanup(self.browser.quit)

    def testPageTitle(self):
        self.browser.get(self.getServerUrl())
        self.assertIn('Writeup Feed Filter', self.browser.title)

if __name__ == '__main__':
    unittest.main(verbosity=2)