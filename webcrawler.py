import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def fetch_html(session, url):
    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Error fetching the URL {url}: {e}")
        return None

def scrape_country_data(session, country_url):
    html_content = fetch_html(session, country_url)
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        country_name = country_url.split('/')[-1]  # Extrai o nome do país do link
        print(f"\n============= Printando HTML de {country_name} =============\n")
        print(soup.prettify())  # Exibe o HTML de forma organizada
        return soup
    return None

def get_country_links(session, main_url):
    country_links = []
    while main_url:
        html_content = fetch_html(session, main_url)
        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Encontrando todos os links dos países na página atual
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if 'view' in href:  # Verifica se o link é para um país
                    country_links.append(href)
            
            # Verificando se existe um link "Next" para a próxima página
            next_button = soup.find('a', string='Next >')
            if next_button:
                next_href = next_button['href']
                main_url = f"http://localhost:8000{next_href}"
            else:
                main_url = None  # Não há mais páginas para processar
        else:
            break  # Falha ao carregar a página, parar o loop
    return country_links

def scrape_all_countries(main_url):
    with requests.Session() as session:
        country_links = get_country_links(session, main_url)
        full_urls = [f"http://localhost:8000{link}" for link in country_links]

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(scrape_country_data, session, url) for url in full_urls]
            for future in as_completed(futures):
                _ = future.result()
                time.sleep(2)  # Delay entre as requisições para evitar sobrecarga do servidor

# Exemplo de uso
main_url = "http://localhost:8000/places/default/index"
scrape_all_countries(main_url)