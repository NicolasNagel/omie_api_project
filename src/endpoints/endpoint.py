import json

from typing import Optional

def read_json(path: str) -> dict:
    """Lê um arquivo JSON e retorna seu conteúdo como um dicionário.
    
    Args:
        path (str): O caminho para o arquivo JSON.

    Returns:
        dict: O conteúdo do arquivo JSON como um dicionário.
    """
    with open(path, 'r') as file:
        return json.load(file)
    

class Endpoints:
    """Classe para gerenciar os endpoints da API."""
    def __init__(self) -> None:
        self.path = 'src/endpoints/data/data.json'
        self.endpoints = read_json(self.path)

    def get(
            self,
            resource: Optional[str] = None,
            action: Optional[str] = None
    ) -> dict:
        """Retorna um endpoint específico com base no recurso ou ação fornecidos.
        
        Args:
            resource (str, optional): O recurso do endpoint a ser retornado.
            action (str, optional): A ação do endpoint a ser retornado.

        Returns:
            dict: O endpoint específico como um dicionário.
        """
        if action:
            for endpoint in self.endpoints:
                if endpoint.get('action') == action:
                    return endpoint
        elif resource:
            for endpoint in self.endpoints:
                if endpoint.get('resource') == resource:
                    return endpoint
        else:
            raise Exception('Resource or action not found.')     

    def get_all(self) -> list[dict]:
        """Retorna todos os endpoints disponíveis.
        
        Returns:
            list[dict]: Uma lista de dicionários, cada um representando um endpoint.
        """
        return self.endpoints