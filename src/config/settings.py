from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Classe responsável por guardar as informações de segurança para o Projeto."""

    APP_KEY: str
    APP_SECRET: str
    BASE_URL: str

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )