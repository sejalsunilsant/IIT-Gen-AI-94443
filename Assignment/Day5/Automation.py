from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
import time

driver = webdriver.Chrome()
driver.get("https://duckduckgo.com/")
search_box = driver.find_element(By.NAME, "q")
search_box.send_keys("LM Studio Tutorials")
search_box.send_keys(Keys.RETURN)

print("page title:", driver.title)

driver.quit()
