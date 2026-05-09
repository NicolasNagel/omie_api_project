import logging

from typing import Optional, Union, Dict, Any

from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util import Retry


logger = logging.getLogger(__name__)

class APISession:
    """
    Classe para gerenciar sessões de requisições HTTP com suporte a retries e tratamento de erros.
    """
    def __init__(self) -> None:
        self.session = Session()

        self.retry = Retry(
            connect=1,
            total=5,
            backoff_factor=0.5,
            respect_retry_after_header=True,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=['GET', 'POST', 'PUT', 'DELETE']
        )

        self.adapters = HTTPAdapter(max_retries=self.retry)

        self.session.mount('http://', self.adapters)
        self.session.mount('https://', self.adapters)

    def get(self) -> Union[Session, None]:
        return self.session
    

class API:
    """
    Classe para gerenciar requisições HTTP/HTTPS com suporte a retries e tratamento de erros.
    """
    def __init__(
            self,
            url: str = '',
            headers: Optional[Dict[str, Any]] = None,
            verify: bool = True,
            proxies: Optional[Dict[str, Any]] = None,
            timeout: Optional[int] = 30,
            session: Optional[APISession] = None
    ) -> None:
        self.url = url
        self.headers = headers or {}
        self.verify = verify
        self.proxies = proxies
        self.timeout = timeout
        self.session = session or APISession().get()

    def request(
            self,
            method: str,
            url: str = '',
            headers: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            json: Optional[Dict[str, Any]] = None,
            data: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], str, None]:
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json,
                data=data,
                verify=self.verify,
                proxies=self.proxies,
                timeout=self.timeout
            )

            if response.ok:
                if response.status_code == 204:
                    return None
                
            try:
                return response.json()
            except ValueError:
                return response.text
            
        except RequestException as error:
            logger.error(f'Erro ao se conectar com a API: {str(error)}.')
            raise
    
    def get(
            self,
            url: str = '',
            headers: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            json: Optional[Dict[str, Any]] = None,
            data: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], str, None]:
        response = self.request(
            method='GET',
            url=url,
            headers=headers,
            params=params,
            json=json,
            data=data
        )

        return response
    
    def post(
            self,
            url: str = '',
            headers: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            json: Optional[Dict[str, Any]] = None,
            data: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], str, None]:
        response = self.request(
            method='POST',
            url=url,
            headers=headers,
            params=params,
            json=json,
            data=data
        )

        return response
    
    def put(
            self,
            url: str = '',
            headers: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            json: Optional[Dict[str, Any]] = None,
            data: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], str, None]:
        response = self.request(
            method='PUT',
            url=url,
            headers=headers,
            params=params,
            json=json,
            data=data
        )

        return response
    
    def delete(
            self,
            url: str = '',
            headers: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            json: Optional[Dict[str, Any]] = None,
            data: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], str, None]:
        response = self.request(
            method='DELETE',
            url=url,
            headers=headers,
            params=params,
            json=json,
            data=data
        )

        return response
    
    def build_omie_payload(
            self,
            action: str,
            app_key: str,
            app_secret: str,
            params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Monta o payload padrão da OMIE API.
        
        Args:
            action (str): A ação a ser realizada.
            params (Dict[str, Any]): Os parâmetros da requisição.

        Returns
            Dict(str, Any): Payload para requisição na API da OMIE.
        """

        return {
            'call': action,
            'app_key': app_key,
            'app_secret': app_secret,
            'param': [params],
        }
    
    def omie_post(
            self,
            base_url: str,
            resource: str,
            action: str,
            app_key: str,
            app_secret: str,
            params: Dict[str, Any] = None,
            headers: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Faz uma requisição tipo GET no padrão da API da OMIE."""

        payload = self.build_omie_payload(
            action=action,
            app_key=app_key,
            app_secret=app_secret,
            params=params
        )

        response = self.post(
            url=f'{base_url}/{resource}',
            headers=headers,
            json=payload
        )

        return response