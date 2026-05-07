import pandas as pd
import requests

from sqlalchemy import create_engine

from src.config.settings import Settings

settings = Settings()

base_url = settings.BASE_URL
app_key = settings.APP_KEY
app_secret = settings.APP_SECRET

endpoints = [
    {
        'resources': 'geral/clientes/',
        'action': 'ListarClientes',
        'params': {
            'pagina': 1,
            "registros_por_pagina": 100,
            "apenas_importado_api": "N"
        }
    }
]

HEADERS = {
    'Content-Type': 'application/json' 
}

def request(resource: str, body: dict, params: dict) -> dict:
    """Faz uma requisição POST para o endpoint especificado e retorna a resposta em formato JSON.
    
    Args:
        resource (str): O recurso do endpoint.
        body (dict): O corpo da requisição.
        params (dict): Os parâmetros da requisição.

    Returns:
        dict: A resposta da requisição em formato JSON.
    """
    response = requests.post(
        url=f'{base_url}/{resource}',
        headers=HEADERS,
        json=body,
        params=params
    )

    if response.status_code == 200:
        json = response.json()
        return json
    else:
        raise Exception(f'Erro: {response.status_code}')


def get_total_of_pages(resource: str, action: str, params: dict) -> int:
    """Faz uma requisição para o endpoint especificado e retorna o total de páginas disponíveis.
    
    Args:
        resource (str): O recurso do endpoint.
        action (str): A ação a ser realizada.
        params (dict): Os parâmetros da requisição.

    Returns:
        int: O total de páginas disponíveis.
    """
    payload = {
        'call': action,
        'app_key': app_key,
        'app_secret': app_secret,
        'param': [params]
    }
    
    response = request(resource, payload, params)
    total_of_pages = response.get('total_de_paginas', 0)
    records = response.get('total_de_registros', 0)
    print(f'Total of Pages: {total_of_pages}')
    print(f'Records: {records}')

    return total_of_pages

for endpoint in endpoints:
    resource = endpoint.get('resources', None)
    action = endpoint.get('action', None)
    params = endpoint.get('params', None)

    total_of_pages = get_total_of_pages(resource, action, params)

    records_fetched = 0
    for page in range(1, total_of_pages + 1):
        params['pagina'] = page

        body = {
            'call': action,
            'app_key': app_key,
            'app_secret': app_secret,
            'param': [params]
        }

        response = request(resource, body, params)
        records_fetched += response.get('registros', 0)

        print(f'Page: {page} Records: {records_fetched}')

