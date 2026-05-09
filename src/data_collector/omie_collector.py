import logging

from typing import Optional, List, Dict, Any

from src.config.settings import Settings
from src.api.api_reponse import API
from src.endpoints.endpoint import Endpoints
from src.controllers.pagination import PaginationController
from src.database.database import DataBase


logger = logging.getLogger(__name__)


class OMIECollector:
    """Classe responsável por fazer a coleta de Dados na API da OMIE."""

    def __init__(self) -> None:
        self.settings = Settings()
        self.api = API()
        self.endpoints = Endpoints()
        self.database = DataBase()
        self.pagination = PaginationController()

        self.HEADERS = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        self.black_list = [
            "tags",
            "recomendacoes",
            "homepage",
            "fax_ddd",
            "fax_numero",
            "bloquear_exclusao",
            "produtor_rural",
        ]

    def request(
            self,
            resource: str,
            action: str,
            params:Dict[str, Any],
    ) -> Dict[str, Any]:
        """Faz uma requisição para o endpoint especificado e retorna o total de páginas disponíveis.
    
        Args:
            resource (str): O recurso do endpoint.
            action (str): A ação a ser realizada.
            params (Dict[str, Any]): Os parâmetros da requisição.

        Returns:
            Dict[str, Any]: Conteúdo em JSON do endpoint solicitado.
        """
        return self.api.omie_post(
            base_url=self.settings.BASE_URL,
            resource=resource,
            action=action,
            app_key=self.settings.APP_KEY,
            app_secret=self.settings.APP_SECRET,
            params=params,
            headers=self.HEADERS
        )
    
    def get_total_of_pages(
            self,
            resource: str,
            action: str,
            params: Dict[str, Any],
            page_label: Optional[str] = None,
            total_of_pages_label: Optional[str] = None,
            records_label: Optional[str] = None,
    ) -> int:
        """Faz uma requisição para o endpoint especificado e retorna o total de páginas disponíveis.
    
        Args:
            resource (str): O recurso do endpoint.
            action (str): A ação a ser realizada.
            params (dict): Os parâmetros da requisição.

        Returns:
            int: O total de páginas disponíveis.
        """

        page_label = 'pagina' if page_label is None else page_label
        total_of_pages_label = 'total_de_paginas' if total_of_pages_label is None else total_of_pages_label
        records_label = 'registros' if records_label is None else records_label

        response = self.request(
            resource=resource,
            action=action,
            params=params
        )

        total_of_pages = response.get(total_of_pages_label, 0)
        total_records = response.get('total_de_registros', 0)

        logger.info(f'Total de páginas: {total_of_pages} | total de registros: {total_records}')

        return total_of_pages
    
    def remove_black_list_fields(self, contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove campos indesejados dos registros."""

        for content in contents:
            for field in self.black_list:
                content.pop(field, None)

        return contents
    
    def collect_endpoint(self, endpoint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Coleta os dados do endpoint solicitado."""
        resource = endpoint.get('resources', None)
        action = endpoint.get('action', None)
        params = endpoint.get('params', {}).copy()
        data_source = endpoint.get('data_source', None)

        pagination_type = endpoint.get('pagination_type', 'per_page')
        page_label = endpoint.get('page_label', None)

        total_of_pages_label = endpoint.get('total_of_pages_label', None)
        records_label = endpoint.get('records_label', None)

        date_init = endpoint.get('date_init')
        date_start_label = endpoint.get('date_start_label', 'dPeriodoInicial')
        date_end_label = endpoint.get('date_end_label', 'dPeriodoFinal') 

        logger.info(f'Iniciando Coleta: {data_source}')

        results = []

        responses = self.pagination.pagination(
            pagination_type=pagination_type,
            request_function=self.request,
            resource=resource,
            action=action,
            params=params,
            data_source=data_source,
            page_label=page_label,
            total_of_pages_label=total_of_pages_label,
            records_label=records_label,
            date_init=date_init,
            date_start_label=date_start_label,
            date_end_label=date_end_label
        )

        for page, response in enumerate(responses, start=1):
            contents = response.get(data_source, [])

            contents = self.remove_black_list_fields(contents)
            results.extend(contents)

            table_name = self.database.rename_table(resource)

            self.database.save_data_into_db(
                page=page,
                data=contents,
                table_name=table_name
            )

        logger.info(f'Coleta finalizada: {data_source}')

        return results
    
    def collect_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """Coleta todos os endpoints configurados."""
        collected_data = {}

        for endpoint in self.endpoints.get_all():
            data_source = endpoint.get('data_source')

            collected_data[data_source] = self.collect_endpoint(endpoint)

        return collected_data