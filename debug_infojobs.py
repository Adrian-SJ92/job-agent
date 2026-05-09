from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time

opts = Options()
opts.add_argument('--headless')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.binary_location = '/usr/bin/chromium'

print("Iniciando driver...")
driver = webdriver.Chrome(service=Service('/usr/bin/chromedriver'), options=opts)
print("Driver OK")

url = 'https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=React&provinceIds=29'
print(f"Cargando: {url}")
driver.get(url)
print("Esperando 5s...")
time.sleep(5)

html = driver.page_source
print(f"HTML recibido: {len(html)} chars")
print("--- PRIMEROS 3000 CHARS ---")
print(html[:3000])
print("--- FIN ---")

driver.quit()
