import requests
from bs4 import BeautifulSoup

def fetch_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        return None

def get_country_links(main_url):
    country_links = []
    count = 0
    while main_url:
        html_content = fetch_html(main_url)
        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Encontrando todos os links dos países na página atual
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if 'view' in href:  # Verifica se o link é para um país
                    country_links.append(href)
            count = count + 1
            print(f"Coletando páginas de países... Por favor aguarde ({count}/26) ")
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
    country_links = get_country_links(main_url)
    for link in country_links:
        country_name = link.split('/')[-1]  # Extrai o nome do país do link
        country_url = f"http://localhost:8000{link}"
        print(f"\n============= Printando HTML de {country_name} =============\n")
        html_content = fetch_html(country_url)
        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            print(soup.prettify())  # Exibe o HTML de forma organizada

# Exemplo de uso
main_url = "http://localhost:8000/places/default/index"
scrape_all_countries(main_url)
