from typing import Union

from requests import Session, Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class APISession:
    def __init__(self) -> None:
        self.session = Session()

        self.retry = Retry(
            connect=1,
            total=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=['GET', 'POST', 'PUT', 'DELETE']
        )

        self.adapters = HTTPAdapter(max_retries=self.retry)

        self.session.mount('http://', self.adapters)
        self.session.mount('https://', self.adapters)

    def get(self) -> Union[Session, None]:
        return self.session
    

class API:
    def __init__(
            self,
            url: str,
            headers: dict = None,
            params: dict = None,
            json: dict = None,
            proxies: dict = None
        ) -> None:
        self.url = url
        self.headers = headers
        self.params = params
        self.json = json
        self.proxies = proxies
        self.verify = True
        self.session = APISession().get()

    def get(self) -> Union[Response, None]:
        response = self.session.get(
            url=self.url,
            headers=self.headers,
            params=self.params,
            json=self.json,
            verify=self.verify,
            proxies=self.proxies
        )

        return response
    
    def post(self) -> Union[Response, None]:
        response = self.session.post(
            url=self.url,
            headers=self.headers,
            params=self.params,
            json=self.json,
            verify=self.verify,
            proxies=self.proxies
        )

        return response
    
    def put(self) -> Union[Response, None]:
        response = self.session.put(
            url=self.url,
            headers=self.headers,
            params=self.params,
            json=self.json,
            verify=self.verify,
            proxies=self.proxies
        )
        
        return response
    
    def delete(self) -> Union[Response, None]:
        response = self.session.delete(
            url=self.url,
            headers=self.headers,
            params=self.params,
            json=self.json,
            verify=self.verify,
            proxies=self.proxies
        )

        return response