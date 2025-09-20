from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

CHROME_DRIVER_PATH = r"D:\ird-projects\my_pyautomation\ui\driver\chromedriver.exe"
DEBUGGER_ADDRESS = "127.0.0.1:9222"  # Chrome must be launched with --remote-debugging-port=9222

def get_driver():
    opts = Options()
    opts.debugger_address = DEBUGGER_ADDRESS
    return webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=opts)