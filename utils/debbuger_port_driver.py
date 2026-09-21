from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

DEBUGGER_ADDRESS = "127.0.0.1:9222"

def get_driver():
    opts = Options()
    opts.debugger_address = DEBUGGER_ADDRESS
    return webdriver.Chrome(options=opts)