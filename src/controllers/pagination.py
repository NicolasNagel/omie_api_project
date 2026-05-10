import calendar
import logging

from typing import Literal, Iterator, Dict, Any, Callable, Optional, List
from datetime import datetime


logger = logging.getLogger(__name__)


class PaginationController:
    def __init__ (self) -> None:
        ...

    def generate_date_range(self, start_date_str: str) -> List[str]:
        def add_month(data: datetime) -> datetime:
            new_month = data.month + 1
            new_year = data.year
            if new_month > 12:
                new_month = 1
                new_year += 1
            return data.replace(month=new_month, year=new_year)
        
        start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
        start_date = start_date.replace(day=1)

        today = datetime.today()

        date_list = []
        current_date = start_date
        while current_date <= today:
            date_list.append(current_date.strftime("%d/%m/%Y"))
            current_date = add_month(current_date)

        return date_list


    def pagination(
            self,
            pagination_type: Literal['per_page', 'date_range'],
            request_function: Callable[[str, str, Dict[str, Any]], Dict[str, Any]],
            resource: str,
            action: str,
            params: Dict[str, Any],
            data_source: str,
            page_label: str = 'pagina',
            total_of_pages_label: str = 'total_de_paginas',
            records_label: str = 'total_de_registros',
            date_init: Optional[str] = None,
            date_start_label: str = 'dPeriodoInicial',
            date_end_label: str = 'dPeriodoFinal',
    ) -> Iterator[Dict[str, Any]]:
        match pagination_type:
            case 'per_page':
                yield from self.per_page(
                    request_function=request_function,
                    resource=resource,
                    action=action,
                    params=params,
                    data_source=data_source,
                    page_label=page_label,
                    total_of_pages_label=total_of_pages_label,
                    records_label=records_label,
                )
            case 'date_range':
                yield from self.date_range(
                    request_function=request_function,
                    resource=resource,
                    action=action,
                    params=params,
                    data_source=data_source,
                    date_init=date_init,
                    date_start_label=date_start_label,
                    date_end_label=date_end_label
                )

            case _:
                raise ValueError(f'Tipo de paginação inválido: {pagination_type}')
            
    def per_page(
            self,
            request_function: Callable[[str, str, Dict[str, Any]], Dict[str, Any]],
            resource: str,
            action: str,
            params: Dict[str, Any],
            data_source: Optional[str] = None,
            page_label: str = 'pagina',
            total_of_pages_label: str = 'total_de_paginas',
            records_label: str = 'total_de_registros',
    ) -> Iterator[Dict[str, Any]]:
        """Executa paginação por número de página."""

        page_label = page_label or 'pagina'
        total_of_pages_label = total_of_pages_label or 'total_de_paginas'
        records_label = records_label or 'total_de_registros'

        first_response = request_function(
            resource,
            action,
            params
        )

        total_of_pages = first_response.get(total_of_pages_label, None)
        total_records = first_response.get(records_label, 0)

        logger.info(
            f'Total de páginas: {total_of_pages} | Total de registros: {total_records}'
        )

        records_fetched = 0
        for page in range(1, total_of_pages + 1):
            params_page = params.copy()
            params_page[page_label] = page

            logger.info(f'Coletando página: {page} de {total_of_pages}')

            response = request_function(
                resource,
                action,
                params_page
            )

            if data_source:
                contents = response.get(data_source, [])
                records_fetched += len(contents)

                logger.info(
                    f'Pagina: {page} coletada com {len(contents)} '
                    f'Total acumulado: {records_fetched}'
                )

            yield response

    def date_range(
            self,
            request_function: Callable[[str, str, Dict[str, Any]], Dict[str, Any]],
            resource: str,
            action: str,
            params: Dict[str, Any],
            data_source: str,
            date_init: str,
            date_start_label: str = 'dPeriodoInicial',
            date_end_label: str = 'dPeriodoFinal',
    ) -> Iterator[Dict[str, Any]]:
        """Executa paginação por intervalo de datas."""

        dates = self.generate_date_range(date_init)

        for date in dates:
            date_obj = datetime.strptime(date, '%d/%m/%Y')
            last_day = calendar.monthrange(date_obj.year, date_obj.month)[1]
            end_month_data = date_obj.replace(day=last_day)
            end_month_data = end_month_data.strftime('%d/%m/%Y')

            params_date = params.copy()
            params_date[date_start_label] = date
            params_date[date_end_label] = end_month_data

            logger.info(
                f'Coletando período: {date} até {last_day}'
            )

            response = request_function(
                resource,
                action,
                params_date
            )

            if data_source:
                contents = response.get(data_source, [])

                logger.info(
                    f'Período {date} até {last_day} coletado com '
                    f'{len(contents)} registros.'
                )

            yield response