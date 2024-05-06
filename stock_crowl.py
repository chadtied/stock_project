from seleniumbase import Driver
from selenium.webdriver.common.by import By
import requests

#建立變數
driver= Driver(uc= True, incognito= False, headless= True)
download_url= ''

driver.get('https://data.gov.tw/dataset/11549')
web_elements= driver.find_elements(By.CSS_SELECTOR,"ul > li.resource-item > a")

for element in web_elements:
    if "CSV" in element.text:   download_url= element.get_attribute('href')

response= requests.get(download_url)
if response.status_code == 200:
    with open('./stock.csv', 'w') as f: #下載路徑依照需求更改，目前為預設路徑
        f.write(response.text)
else:   print(response.status_code)
