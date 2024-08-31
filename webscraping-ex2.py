import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import time

def fetch_html(session, url):
    try:
        response = session.get(url, timeout=(5, 14))  # timeout de conexão e leitura
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar: {e}")
        return None

def scrape_country_data(session, country_url):
    html_content = fetch_html(session, country_url)
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        country_name = soup.find('tr', id='places_country__row').find('td', class_='w2p_fw').text.strip()
        currency_name = soup.find('tr', id='places_currency_name__row').find('td', class_='w2p_fw').text.strip()
        continent = soup.find('tr', id='places_continent__row').find('td', class_='w2p_fw').text.strip()

        neighbours_tags = soup.find('tr', id='places_neighbours__row').find('td', class_='w2p_fw').find_all('a')
        neighbours = []

        for tag in neighbours_tags:
            neighbour_href = tag['href']
            neighbour_url = f"http://localhost:8000{neighbour_href}"
            neighbour_html_content = fetch_html(session, neighbour_url)
            if neighbour_html_content:
                neighbour_soup = BeautifulSoup(neighbour_html_content, 'html.parser')
                neighbour_row = neighbour_soup.find('tr', id='places_country__row')
                if neighbour_row:
                    neighbour_name = neighbour_row.find('td', class_='w2p_fw').text.strip()
                    neighbours.append(neighbour_name)

        neighbours = ', '.join(neighbours)
        timestamp = datetime.now().isoformat()

        return [country_name, currency_name, continent, neighbours, timestamp]
    else:
        return None

def scrape_all_countries(main_url, output_csv, delay_between_requests=1.0):
    data = []
    count = 0

    with requests.Session() as session, ThreadPoolExecutor(max_workers=5) as executor:  # Reduzindo número de threads
        while main_url:
            html_content = fetch_html(session, main_url)
            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                country_links = [f"http://localhost:8000{a_tag['href']}" for a_tag in soup.find_all('a', href=True) if 'view' in a_tag['href']]

                results = executor.map(lambda url: scrape_country_data(session, url), country_links)
                data.extend(filter(None, results))

                count += 1
                print(f"Página {count}/26 Por favor aguarde...")

                next_button = soup.find('a', string='Next >')
                if next_button:
                    next_href = next_button['href']
                    main_url = f"http://localhost:8000{next_href}"
                else:
                    main_url = None

                time.sleep(delay_between_requests)  # Atraso entre as requisições para evitar sobrecarga

            else:
                break

    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Pais', 'Nome_da_moeda', 'Continente', 'Países_vizinhos', 'Timestamp'])
        writer.writerows(data)
    print(f"Arquivo CSV criado: {output_csv}")

# Exemplo de uso
main_url = "http://localhost:8000/places/default/index"
output_csv = 'dados_paises.csv'
scrape_all_countries(main_url, output_csv)