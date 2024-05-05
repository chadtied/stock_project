from seleniumbase import Driver
from selenium.webdriver.common.by import By
import requests

#建立變數
driver= Driver(uc= True, incognito= False, headless= True)

driver.get('https://data.gov.tw/dataset/11549')
download_url= driver.find_element(By.CSS_SELECTOR,"#__nuxt > div > div > main > div.page > div.table.table--fixed.od-table.od-table--bordered.print-table > div:nth-child(2) > div:nth-child(2) > ul > li > a").get_attribute('href')
response= requests.get(download_url)

if response.status_code == 200:
    with open('./stock.csv', 'w') as f: #下載路徑依照需求更改，目前為預設路徑
        f.write(response.text)
else:   print(response.status_code)
