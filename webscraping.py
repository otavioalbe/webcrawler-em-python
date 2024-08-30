import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime

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
            next_button = soup.find('a', string='Next >')  # Usando 'string' em vez de 'text'
            if next_button:
                next_href = next_button['href']
                main_url = f"http://localhost:8000{next_href}"
            else:
                main_url = None  # Não há mais páginas para processar
        else:
            break  # Falha ao carregar a página, parar o loop
    return country_links

def scrape_country_data(country_url):
    html_content = fetch_html(country_url)
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Extração dos dados
        country_name = soup.find('tr', id='places_country__row').find('td', class_='w2p_fw').text.strip()
        currency_name = soup.find('tr', id='places_currency_name__row').find('td', class_='w2p_fw').text.strip()
        continent = soup.find('tr', id='places_continent__row').find('td', class_='w2p_fw').text.strip()
        neighbours_tags = soup.find('tr', id='places_neighbours__row').find('td', class_='w2p_fw').find_all('a')
        neighbours = ', '.join([tag.text.strip() for tag in neighbours_tags])
        
        # Timestamp do momento de obtenção dos dados
        timestamp = datetime.now().isoformat()

        return [country_name, currency_name, continent, neighbours, timestamp]
    else:
        return None

def scrape_all_countries(main_url, output_csv):
    country_links = get_country_links(main_url)
    data = []
    
    for link in country_links:
        country_url = f"http://localhost:8000{link}"
        country_name = link.split('/')[-1]  # Extrai o nome do país do link
        print(f"\n============= Lendo dados do país {country_name} =============\n")
        country_data = scrape_country_data(country_url)
        if country_data:
            data.append(country_data)

    # Salvando os dados em um arquivo CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['País', 'Nome da moeda', 'Continente', 'Países vizinhos', 'Timestamp'])
        writer.writerows(data)
    print(f"Arquivo CSV criado: {output_csv}")

# Exemplo de uso
main_url = "http://localhost:8000/places/default/index"
output_csv = 'dados_paises.csv'
scrape_all_countries(main_url, output_csv)
