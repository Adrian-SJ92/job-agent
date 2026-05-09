from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time

opts = Options()
opts.add_argument('--headless')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--disable-blink-features=AutomationControlled')
opts.add_argument('user-agent=Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36')
opts.add_experimental_option('excludeSwitches', ['enable-automation'])
opts.add_experimental_option('useAutomationExtension', False)
opts.binary_location = '/usr/bin/chromium'

print("Iniciando driver...")
driver = webdriver.Chrome(service=Service('/usr/bin/chromedriver'), options=opts)

# Ocultar navigator.webdriver
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
})

print("Driver OK")

url = 'https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=React&provinceIds=29'
print(f"Cargando: {url}")
driver.get(url)
print("Esperando 6s...")
time.sleep(6)

html = driver.page_source
print(f"HTML recibido: {len(html)} chars")

if 'captcha' in html.lower():
    print("SIGUE CAPTCHA — anti-bot activo")
else:
    print("SIN CAPTCHA — buscando ofertas...")
    # Mostrar clases de los primeros <li> para identificar el selector correcto
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    lis = soup.find_all('li')[:10]
    for li in lis:
        print(f"  <li class='{li.get('class')}'>")

print("--- PRIMEROS 2000 CHARS ---")
print(html[:2000])
driver.quit()
