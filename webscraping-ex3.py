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

def read_existing_data(csv_file):
    existing_data = {}
    try:
        with open(csv_file, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Pula o cabeçalho
            for row in reader:
                if row:
                    country_name = row[0]
                    existing_data[country_name] = row[1:]  # Exclui o nome do país
    except FileNotFoundError:
        print(f"O arquivo {csv_file} não foi encontrado. Um novo arquivo será criado.")
    return existing_data

def update_csv(data, output_csv):
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['País', 'Nome da moeda', 'Continente', 'Países vizinhos', 'Timestamp'])
        for country, details in data.items():
            writer.writerow([country] + details)

def scrape_and_monitor(main_url, output_csv, delay_between_requests=1.0):
    existing_data = read_existing_data(output_csv)
    new_data = {}
    
    with requests.Session() as session, ThreadPoolExecutor(max_workers=5) as executor:
        while main_url:
            html_content = fetch_html(session, main_url)
            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                country_links = [f"http://localhost:8000{a_tag['href']}" for a_tag in soup.find_all('a', href=True) if 'view' in a_tag['href']]

                results = executor.map(lambda url: scrape_country_data(session, url), country_links)

                for result in results:
                    if result:
                        country_name, *details = result
                        if country_name in existing_data:
                            if existing_data[country_name] != details:
                                print(f"Atualizando dados para {country_name}.")
                                new_data[country_name] = details
                            else:
                                print(f"Nenhuma mudança detectada para {country_name}.")
                                new_data[country_name] = existing_data[country_name]
                        else:
                            print(f"Novo país encontrado: {country_name}. Adicionando ao CSV.")
                            new_data[country_name] = details

                next_button = soup.find('a', string='Next >')
                if next_button:
                    next_href = next_button['href']
                    main_url = f"http://localhost:8000{next_href}"
                else:
                    main_url = None

                time.sleep(delay_between_requests)

            else:
                break

    update_csv(new_data, output_csv)
    print(f"Monitoramento completo. Arquivo CSV atualizado: {output_csv}")

# Exemplo de uso
main_url = "http://localhost:8000/places/default/index"
output_csv = 'dados_paises.csv'
scrape_and_monitor(main_url, output_csv)
