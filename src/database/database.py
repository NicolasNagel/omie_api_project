import pandas as pd
import logging
import json

from typing import List, Dict, Any
from datetime import datetime

from sqlalchemy import create_engine, text

from src.config.settings import Settings


logger = logging.getLogger(__name__)


class DataBase:
    """Classe responsável por fazer o gerenciamento do Banco de Dados."""
    def __init__(self) -> None:
        self.settings = Settings()

        self.db_user = self.settings.DB_USER
        self.db_pass = self.settings.DB_PASS
        self.db_host = self.settings.DB_HOST
        self.db_port = self.settings.DB_PORT
        self.db_name = self.settings.DB_NAME

        self.conn_string = f'postgresql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}'
        self.engine = create_engine(self.conn_string)

    def rename_table(self, resource: str) -> str:
        """Renomeia o nome da tabela.
        
        Args:
            resource (str): O recurso do endpoint.

        Returns:
            None
        """
        name = resource.split('/')[-2]
        table_name = f'bronze_{name}'

        return table_name

    def flatten_dict(
        self,
        data: Dict[str, Any],
        parent_key: str = '',
        sep: str = '_',
    ) -> Dict[str, Any]:
        """Achata dicionários aninhados, concatenando as chaves com um separador.

        Args:
            data (Dict[str, Any]): O dicionário a ser achatado.
            parent_key (str, optional): A chave pai para concatenar. Defaults to ''.
            sep (str, optional): O separador para concatenar as chaves. Defaults to '_'.

        Returns:
            Dict[str, Any]: O dicionário achatado.
        """
        items = []
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key

            if isinstance(value, dict):

                items.extend(
                    self.flatten_dict(
                        data=value,
                        parent_key=new_key, 
                        sep=sep
                    ).items()
                )

            elif isinstance(value, list):
                items.append(
                    (
                        new_key,
                        json.dumps(value, ensure_ascii=False)
                    )
                )

            else:
                items.append((new_key, value))

        return dict(items)
    
    def normalize_column_name(self, column: str) -> str:
        """
        Normaliza nomes de colunas para o Banco de Dados.
        
        Args:
            column (str): O nome da coluna a ser normalizada.

        Returns:
            str: O nome da coluna normalizada.
        """

        return (
            column
            .replace('.', '_')
            .replace('-', '_')
            .replace('/', '_')
            .replace(' ', '_')
            .lower()
        )
    
    def get_columns_of_db(self, table_name: str) -> List[str]:
        """Obtém os nomes das colunas de uma tabela no banco de dados.
        
        Args:
            table_name (str): O nome da tabela.
        
        Returns:
            List[str]: Uma lista com os nomes das colunas da tabela.
        """
        connection = self.engine.connect()

        query = text(f"""
            SELECT column_name
             FROM information_schema.columns
            WHERE table_name = '{table_name}'
        """)
        result = connection.execute(query)
        return [row[0] for row in result]
    
    def update_table_structure(self, table_name: str, df_columns: List[str]) -> None:
        """
        Atualiza a estrutura da tabela no banco de dados.

        Args:
            table_name (str): O nome da tabela a ser atualizada.
            df_columns (List[str]): A lista de colunas presentes no DataFrame.

        Returns:
            None
        """
        existing_columns = self.get_columns_of_db(table_name)

        missing_columns = [col for col in df_columns if col not in existing_columns]

        with self.engine.begin() as conn:
            for column in missing_columns:
                conn.execute(text(
                    f'ALTER TABLE "{table_name}" ADD COLUMN "{column}" TEXT'
                ))

    def save_data_into_db(
            self,
            page: int,
            data: List[Dict[str, Any]],
            table_name: str
    ) -> None:
        """Salva os dados em um banco de dados PostgreSQL usando SQLAlchemy.
    
        Args:
            page (int): O número da página atual.
            resource (str): O recurso do endpoint
            content (dict): O conteúdo a ser salvo no banco de dados.

        Returns:
            None
        """
        flatten_data = [
            self.flatten_dict(record) for record in data
        ]

        df = pd.json_normalize(flatten_data)
        df['sistem_source'] = 'OMIE_API'
        df['inserted_at'] = datetime.now()

        for col in df.columns:
            df[col] = df[col].apply(
                lambda x: json.dumps(x, ensure_ascii=False)
                if isinstance(x, (dict, list))
                else x
            )
        
        df.columns = [
            self.normalize_column_name(col)
            for col in df.columns
        ]

        logger.info(f'Salvando {len(df)} registros em {table_name}')

        if page == 1:
            df.to_sql(table_name, self.engine, if_exists='replace', index=False)
        else:
            self.update_table_structure(table_name, df.columns)
            df.to_sql(table_name, self.engine, if_exists='append', index=False)

        logger.info(f'{len(df)} dados salvos com sucesso na tabela: {table_name}')